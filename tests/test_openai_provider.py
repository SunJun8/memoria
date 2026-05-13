import os
import json

import pytest

from memoria.infrastructure.llm.mock_provider import MockLLMProvider
from memoria.infrastructure.llm.openai_provider import OpenAIProvider


def test_openai_provider_uses_configured_reasoning_effort():
    provider = OpenAIProvider(
        model="gpt-test",
        reasoning_effort="medium",
        api_key="test-key",
        client=None,
    )
    assert provider.model == "gpt-test"
    assert provider.reasoning_effort == "medium"


class FakeResponse:
    output_text = json.dumps(
        {
            "actor": "llm",
            "source": "openai_provider",
            "operations": [
                {
                    "operation_id": "op-1",
                    "operation_type": "create_issue",
                    "reason": "test response",
                    "confidence": 0.9,
                    "payload": {
                        "title": "Fake issue",
                        "summary": "Created by fake client",
                        "status": "open",
                        "status_confidence": 0.9,
                        "status_reason": "test response",
                        "tags": [],
                    },
                    "refs": {"raw_entry_ids": [1]},
                    "job_id": None,
                }
            ],
            "job_id": None,
        }
    )

    def model_dump(self, mode):
        return {"output_text": self.output_text, "mode": mode}


class FakeResponses:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return FakeResponse()


class FakeClient:
    def __init__(self):
        self.responses = FakeResponses()


def _assert_openai_strict_objects(schema):
    if schema.get("type") == "object":
        assert schema.get("additionalProperties") is False
        assert set(schema.get("required", [])) == set(schema.get("properties", {}).keys())
    for key in ("properties", "$defs"):
        for value in schema.get(key, {}).values():
            _assert_openai_strict_objects(value)
    for value in schema.get("anyOf", []):
        _assert_openai_strict_objects(value)
    items = schema.get("items")
    if isinstance(items, dict):
        _assert_openai_strict_objects(items)


def _operation_schema(request):
    schema = request["text"]["format"]["schema"]
    return schema["properties"]["operations"]["items"]


def test_openai_provider_sends_reasoning_and_strict_schema_to_client():
    client = FakeClient()
    provider = OpenAIProvider(
        model="gpt-test",
        reasoning_effort="medium",
        reasoning_summary="detailed",
        client=client,
    )

    result = provider.run_memory_job(
        system_state={"pending_raw": [{"id": 1, "content": "Test memory"}]},
        tools=object(),
        strictness="strict",
    )

    request = client.responses.kwargs
    assert request["model"] == "gpt-test"
    assert request["reasoning"] == {"effort": "medium", "summary": "detailed"}
    assert all(tool["strict"] is True for tool in request["tools"])
    assert request["tools"][0]["parameters"]["properties"]["limit"]["maximum"] == 100
    assert request["text"]["format"]["type"] == "json_schema"
    assert request["text"]["format"]["strict"] is True
    _assert_openai_strict_objects(request["text"]["format"]["schema"])
    operation_schema = _operation_schema(request)
    payload_properties = operation_schema["properties"]["payload"]["properties"]
    assert "title" in payload_properties
    assert "event_id" in payload_properties
    assert "processing_state" in payload_properties
    assert "report_json" in payload_properties
    nested_payload = payload_properties["payload"]["anyOf"][0]
    assert nested_payload["type"] == "object"
    assert nested_payload["additionalProperties"] is False
    assert "mode" in nested_payload["properties"]
    assert "processed" in nested_payload["properties"]
    report_json = payload_properties["report_json"]["anyOf"][0]
    assert "processed_raw_ids" in report_json["properties"]
    assert "raw_entry_ids" in operation_schema["properties"]["refs"]["properties"]
    assert result.patch.operations[0].payload["title"] == "Fake issue"
    assert "job_id" not in result.patch.operations[0].model_dump(exclude_none=True)
    assert result.transcript_events[0]["payload"]["tools"] == "provided"


class FakeToolCall:
    type = "function_call"
    call_id = "call-1"
    name = "list_issues"
    arguments = json.dumps({"limit": 5})

    def model_dump(self, mode):
        return {
            "type": self.type,
            "call_id": self.call_id,
            "name": self.name,
            "arguments": self.arguments,
            "mode": mode,
        }


class FakeToolCallResponse:
    output_text = ""
    output = [FakeToolCall()]
    id = "response-1"

    def model_dump(self, mode):
        return {"output": [item.model_dump(mode) for item in self.output], "mode": mode}


class FakeToolResponses:
    def __init__(self):
        self.requests = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        if len(self.requests) == 1:
            return FakeToolCallResponse()
        return FakeResponse()


class FakeToolClient:
    def __init__(self):
        self.responses = FakeToolResponses()


class FakeTools:
    def __init__(self):
        self.calls = []

    def list_issues(self, limit=20):
        self.calls.append(("list_issues", limit))
        return {"issues": [{"id": 1, "title": "Existing issue"}]}


def test_openai_provider_runs_tool_loop_before_final_patch():
    client = FakeToolClient()
    tools = FakeTools()
    provider = OpenAIProvider(
        model="gpt-test",
        reasoning_effort="medium",
        client=client,
        max_tool_rounds=3,
    )

    result = provider.run_memory_job(
        system_state={"pending_raw": [{"id": 1, "content": "Test memory"}]},
        tools=tools,
        strictness="balanced",
    )

    assert tools.calls == [("list_issues", 5)]
    assert len(client.responses.requests) == 2
    followup_input = client.responses.requests[1]["input"]
    assert followup_input[0]["type"] == "function_call_output"
    assert followup_input[0]["call_id"] == "call-1"
    assert "Existing issue" in followup_input[0]["output"]
    assert result.patch.operations[0].payload["title"] == "Fake issue"
    assert [event["type"] for event in result.transcript_events].count("tool_result") == 1


@pytest.mark.openai_live
def test_openai_provider_live_or_fallback():
    require_live = os.environ.get("MEMORIA_REQUIRE_OPENAI_LIVE") == "1"
    api_key = os.environ.get("OPENAI_API_KEY")
    if not require_live:
        result = MockLLMProvider().run_memory_job(
            system_state={"pending_raw": [{"id": 1, "content": "Test memory"}]},
            tools=None,
            strictness="balanced",
        )
        assert result.patch.operations
        return
    if not api_key:
        if require_live:
            raise AssertionError(
                "OPENAI_API_KEY is required when MEMORIA_REQUIRE_OPENAI_LIVE=1"
            )
        result = MockLLMProvider().run_memory_job(
            system_state={"pending_raw": [{"id": 1, "content": "Test memory"}]},
            tools=None,
            strictness="balanced",
        )
        assert result.patch.operations
        return
    provider = OpenAIProvider(
        model=os.environ.get("MEMORIA_LLM_MODEL", "gpt-5.1"),
        reasoning_effort="medium",
        api_key=api_key,
    )
    result = provider.run_memory_job(
        system_state={
            "pending_raw": [
                {
                    "id": 1,
                    "content": "Create one concise memory issue for testing.",
                }
            ]
        },
        tools=None,
        strictness="strict",
    )
    assert result.patch.operations
    assert result.transcript_events
