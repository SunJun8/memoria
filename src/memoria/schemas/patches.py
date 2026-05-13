from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


OperationType = Literal[
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
]


class PatchOperation(BaseModel):
    operation_id: str
    operation_type: OperationType
    reason: str
    confidence: float = Field(ge=0, le=1)
    payload: dict[str, Any]
    refs: dict[str, Any] = Field(default_factory=dict)
    job_id: Optional[int] = None


class MemoryPatch(BaseModel):
    actor: Literal["llm", "user", "system"]
    source: str
    operations: list[PatchOperation]
    job_id: Optional[int] = None
