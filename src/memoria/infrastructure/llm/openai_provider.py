from __future__ import annotations

import json
from typing import Any, Optional

from memoria.schemas.llm import LLMRunResult
from memoria.schemas.patches import MemoryPatch


class OpenAIProvider:
    MAX_TOOL_LIMIT = 100

    def __init__(
        self,
        model: str = "gpt-5.1",
        reasoning_effort: str = "medium",
        reasoning_summary: str = "auto",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        client: object = None,
        max_tool_rounds: int = 8,
    ) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.reasoning_summary = reasoning_summary
        self.max_tool_rounds = max_tool_rounds
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key, base_url=base_url)
        self._client = client

    def run_memory_job(
        self,
        *,
        system_state: dict,
        tools: object,
        strictness: str,
    ) -> LLMRunResult:
        schema = self._openai_strict_schema()
        prompt = self._build_prompt(
            system_state=system_state,
            strictness=strictness,
            schema=schema,
        )
        transcript_events = [
            {
                "type": "request",
                "payload": {
                    "model": self.model,
                    "reasoning_effort": self.reasoning_effort,
                    "reasoning_summary": self.reasoning_summary,
                    "strictness": strictness,
                    "system_state": system_state,
                    "tools": "provided" if tools is not None else None,
                },
            }
        ]
        response = None
        input_payload: Any = prompt
        previous_response_id = None
        for _round in range(self.max_tool_rounds + 1):
            request = {
                "model": self.model,
                "input": input_payload,
                "reasoning": {
                    "effort": self.reasoning_effort,
                    "summary": self.reasoning_summary,
                },
                "text": {
                    "format": {
                        "type": "json_schema",
                        "name": "memory_patch",
                        "schema": schema,
                        "strict": True,
                    }
                },
            }
            if previous_response_id is not None:
                request["previous_response_id"] = previous_response_id
            if tools is not None:
                request["tools"] = self._tool_specs()

            response = self._client.responses.create(**request)
            transcript_events.append({"type": "response", "payload": self._response_payload(response)})
            tool_calls = self._extract_tool_calls(response)
            if not tool_calls:
                break

            input_payload = []
            for call in tool_calls:
                transcript_events.append({"type": "tool_call", "payload": call})
                result = self._run_tool(tools, call)
                transcript_events.append(
                    {
                        "type": "tool_result",
                        "payload": {
                            "call_id": call["call_id"],
                            "name": call["name"],
                            "result": result,
                        },
                    }
                )
                input_payload.append(
                    {
                        "type": "function_call_output",
                        "call_id": call["call_id"],
                        "output": json.dumps(result, ensure_ascii=False, default=str),
                    }
                )
            previous_response_id = getattr(response, "id", None)
        else:
            raise RuntimeError("OpenAI tool loop exceeded max rounds")

        if response is None:
            raise RuntimeError("OpenAI provider did not produce a response")
        output_json = self._strip_nulls(json.loads(response.output_text))
        patch = MemoryPatch.model_validate(output_json)
        report = {
            "mode": "sleep",
            "strictness": strictness,
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
        }
        transcript_events.append({"type": "patch", "payload": patch.model_dump(mode="json")})
        return LLMRunResult(
            patch=patch,
            report=report,
            transcript_events=transcript_events,
        )

    def _tool_specs(self) -> list[dict]:
        nullable_string = {"anyOf": [{"type": "string"}, {"type": "null"}]}
        limit_schema = {"type": "integer", "minimum": 1, "maximum": self.MAX_TOOL_LIMIT}
        return [
            {
                "type": "function",
                "name": "list_issues",
                "description": "List existing memory issues for context.",
                "strict": True,
                "parameters": self._strict_object(
                    {"limit": limit_schema, "status": nullable_string}
                ),
            },
            {
                "type": "function",
                "name": "search_issues",
                "description": "Search existing memory issues by title or summary.",
                "strict": True,
                "parameters": self._strict_object(
                    {"query": {"type": "string"}, "limit": limit_schema}
                ),
            },
            {
                "type": "function",
                "name": "get_issue",
                "description": "Read one memory issue by id.",
                "strict": True,
                "parameters": self._strict_object({"issue_id": {"type": "integer"}}),
            },
            {
                "type": "function",
                "name": "list_chains",
                "description": "List existing memory chains for context.",
                "strict": True,
                "parameters": self._strict_object({"limit": limit_schema}),
            },
        ]

    def _extract_tool_calls(self, response: object) -> list[dict]:
        calls = []
        for item in getattr(response, "output", []) or []:
            item_type = self._read_attr(item, "type")
            if item_type != "function_call":
                continue
            arguments = self._read_attr(item, "arguments") or "{}"
            if isinstance(arguments, str):
                parsed_arguments = json.loads(arguments)
            else:
                parsed_arguments = arguments
            calls.append(
                {
                    "call_id": self._read_attr(item, "call_id"),
                    "name": self._read_attr(item, "name"),
                    "arguments": parsed_arguments,
                }
            )
        return calls

    def _run_tool(self, tools: object, call: dict) -> dict:
        allowed_tools = {"list_issues", "search_issues", "get_issue", "list_chains"}
        name = call["name"]
        if tools is None or name not in allowed_tools or not hasattr(tools, name):
            return {"error": f"unavailable tool {name}"}
        result = getattr(tools, name)(**call["arguments"])
        if isinstance(result, dict):
            return result
        return {"result": result}

    @staticmethod
    def _read_attr(item: object, name: str) -> Any:
        if isinstance(item, dict):
            return item.get(name)
        return getattr(item, name, None)

    def _build_prompt(self, *, system_state: dict, strictness: str, schema: dict) -> str:
        return "\n\n".join(
            [
                "You are the Memoria memory consolidation worker.",
                "Return only a valid JSON object that matches the MemoryPatch schema.",
                "Create at least one useful create_issue operation from pending_raw when pending_raw is present.",
                "Do not delete memory.",
                "Use proposed state for uncertain links or memberships.",
                "Include mark_raw_processed operations for raw entries that are consumed.",
                "The patch actor must be llm and source must be openai_provider.",
                "Strictness: " + strictness,
                "System state JSON:",
                json.dumps(system_state, ensure_ascii=False, sort_keys=True),
                "MemoryPatch JSON schema:",
                json.dumps(schema, ensure_ascii=False, sort_keys=True),
            ]
        )

    def _response_payload(self, response: object) -> dict:
        model_dump = getattr(response, "model_dump", None)
        if callable(model_dump):
            return model_dump(mode="json")
        return {"output_text": getattr(response, "output_text", None)}

    def _openai_strict_schema(self) -> dict:
        string_or_null = {"anyOf": [{"type": "string"}, {"type": "null"}]}
        number_or_null = {"anyOf": [{"type": "number"}, {"type": "null"}]}
        integer_or_null = {"anyOf": [{"type": "integer"}, {"type": "null"}]}
        string_array_or_null = {
            "anyOf": [
                {"type": "array", "items": {"type": "string"}},
                {"type": "null"},
            ]
        }
        integer_array_or_null = {
            "anyOf": [
                {"type": "array", "items": {"type": "integer"}},
                {"type": "null"},
            ]
        }
        bool_or_null = {"anyOf": [{"type": "boolean"}, {"type": "null"}]}
        json_value = self._json_value_schema()
        json_object_or_null = {"anyOf": [json_value, {"type": "null"}]}

        payload_properties = {
            "archived_at": string_or_null,
            "author": string_or_null,
            "title": string_or_null,
            "summary": string_or_null,
            "content": string_or_null,
            "corrected_by_event_id": integer_or_null,
            "deleted_at": string_or_null,
            "event_type": string_or_null,
            "event_id": integer_or_null,
            "status": string_or_null,
            "status_confidence": number_or_null,
            "status_reason": string_or_null,
            "superseded_at": string_or_null,
            "tags": string_array_or_null,
            "issue_id": integer_or_null,
            "source_issue_id": integer_or_null,
            "target_issue_id": integer_or_null,
            "link_type": string_or_null,
            "state": string_or_null,
            "chain_id": integer_or_null,
            "description": string_or_null,
            "target_type": string_or_null,
            "target_id": integer_or_null,
            "weight": number_or_null,
            "membership_id": integer_or_null,
            "proposal_type": string_or_null,
            "payload": json_object_or_null,
            "processing_state": string_or_null,
            "raw_entry_id": integer_or_null,
            "raw_entry_ids": integer_array_or_null,
            "job_id": integer_or_null,
            "reason": string_or_null,
            "confidence": number_or_null,
            "report": json_object_or_null,
            "report_json": json_object_or_null,
            "user_locked": bool_or_null,
        }
        refs_properties = {
            "raw_entry_ids": integer_array_or_null,
            "issue_ids": integer_array_or_null,
            "chain_ids": integer_array_or_null,
        }
        operation_properties = {
            "operation_id": {"type": "string"},
            "operation_type": {
                "enum": [
                    "create_event",
                    "create_issue",
                    "update_issue",
                    "append_comment",
                    "link_issues",
                    "create_or_update_chain",
                    "add_to_chain",
                    "update_chain_membership_weight",
                    "create_proposal",
                    "mark_raw_processed",
                    "create_sleep_report",
                ],
                "type": "string",
            },
            "reason": {"type": "string"},
            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            "payload": self._strict_object(payload_properties),
            "refs": self._strict_object(refs_properties),
            "job_id": integer_or_null,
        }
        patch_properties = {
            "actor": {"enum": ["llm"], "type": "string"},
            "source": {"enum": ["openai_provider"], "type": "string"},
            "operations": {
                "type": "array",
                "items": self._strict_object(operation_properties),
            },
            "job_id": integer_or_null,
        }
        return self._strict_object(patch_properties)

    @staticmethod
    def _strict_object(properties: dict) -> dict:
        return {
            "type": "object",
            "properties": properties,
            "required": list(properties.keys()),
            "additionalProperties": False,
        }

    def _json_value_schema(self) -> dict:
        scalar = {
            "anyOf": [
                {"type": "string"},
                {"type": "number"},
                {"type": "boolean"},
                {"type": "null"},
            ]
        }
        array = {"type": "array", "items": scalar}
        value = {
            "anyOf": [
                {"type": "string"},
                {"type": "number"},
                {"type": "boolean"},
                {"type": "null"},
                array,
            ]
        }
        properties = {
            "mode": scalar,
            "strictness": scalar,
            "processed": scalar,
            "processed_raw_ids": {
                "anyOf": [
                    {"type": "array", "items": {"type": "integer"}},
                    {"type": "null"},
                ]
            },
            "issue_ids": {
                "anyOf": [
                    {"type": "array", "items": {"type": "integer"}},
                    {"type": "null"},
                ]
            },
            "chain_ids": {
                "anyOf": [
                    {"type": "array", "items": {"type": "integer"}},
                    {"type": "null"},
                ]
            },
            "title": scalar,
            "summary": scalar,
            "reason": scalar,
            "state": scalar,
            "value": value,
        }
        return {
            "type": "object",
            "properties": properties,
            "required": list(properties.keys()),
            "additionalProperties": False,
        }

    def _strip_nulls(self, value: object) -> object:
        if isinstance(value, list):
            return [self._strip_nulls(item) for item in value]
        if isinstance(value, dict):
            return {
                key: self._strip_nulls(item)
                for key, item in value.items()
                if item is not None
            }
        return value
