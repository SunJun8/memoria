from __future__ import annotations

from memoria.schemas.llm import LLMRunResult
from memoria.schemas.patches import MemoryPatch, PatchOperation


class MockLLMProvider:
    def run_memory_job(
        self,
        *,
        system_state: dict,
        tools: object,
        strictness: str,
    ) -> LLMRunResult:
        pending_raw = list(system_state.get("pending_raw", []))
        processed_raw_ids = [raw["id"] for raw in pending_raw]
        operations = []

        if pending_raw:
            summary = "\n".join(raw["content"] for raw in pending_raw)
            operations.append(
                PatchOperation(
                    operation_id="mock-create-issue",
                    operation_type="create_issue",
                    reason="Mock provider consolidates pending raw entries.",
                    confidence=1.0,
                    payload={
                        "title": "Mock consolidated memory",
                        "summary": summary,
                        "status": "open",
                        "status_confidence": 1.0,
                        "status_reason": "Created by mock provider.",
                        "tags": [],
                    },
                )
            )
            operations.append(
                PatchOperation(
                    operation_id="mock-mark-raw-processed",
                    operation_type="mark_raw_processed",
                    reason="Mock provider consumed pending raw entries.",
                    confidence=1.0,
                    payload={"raw_entry_ids": processed_raw_ids},
                )
            )

        report = {
            "mode": "sleep",
            "strictness": strictness,
            "processed_raw_ids": processed_raw_ids,
        }
        patch = MemoryPatch(
            actor="llm",
            source="mock_provider",
            operations=operations,
        )
        return LLMRunResult(
            patch=patch,
            report=report,
            transcript_events=[
                {
                    "type": "request",
                    "payload": {"system_state": system_state, "strictness": strictness},
                },
                {
                    "type": "response",
                    "payload": {
                        "operation_count": len(operations),
                        "report": report,
                    },
                },
            ],
        )
