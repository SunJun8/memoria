from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from memoria.schemas.patches import MemoryPatch


class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    name: str
    result: dict[str, Any] = Field(default_factory=dict)


class LLMRunResult(BaseModel):
    patch: MemoryPatch
    report: dict
    transcript_events: list[dict]
