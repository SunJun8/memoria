from __future__ import annotations

import json
from typing import Optional

from memoria.schemas.llm import LLMRunResult
from memoria.schemas.patches import MemoryPatch


class OpenAIProvider:
    def __init__(
        self,
        model: str = "gpt-5.1",
        reasoning_effort: str = "medium",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        client: object = None,
    ) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
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
        response = self._client.responses.create(
            model=self.model,
            input=prompt,
            reasoning={"effort": self.reasoning_effort, "summary": "auto"},
            text={
                "format": {
                    "type": "json_schema",
                    "name": "memory_patch",
                    "schema": schema,
                    "strict": True,
                }
            },
        )
        output_json = self._strip_nulls(json.loads(response.output_text))
        patch = MemoryPatch.model_validate(output_json)
        response_payload = self._response_payload(response)
        report = {
            "mode": "sleep",
            "strictness": strictness,
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
        }
        return LLMRunResult(
            patch=patch,
            report=report,
            transcript_events=[
                {
                    "type": "request",
                    "payload": {
                        "model": self.model,
                        "reasoning_effort": self.reasoning_effort,
                        "strictness": strictness,
                        "system_state": system_state,
                        "tools": "provided" if tools is not None else None,
                    },
                },
                {"type": "response", "payload": response_payload},
                {"type": "patch", "payload": patch.model_dump(mode="json")},
            ],
        )

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
