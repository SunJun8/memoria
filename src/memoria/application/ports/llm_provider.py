from __future__ import annotations

from typing import Protocol

from memoria.schemas.llm import LLMRunResult


class LLMProvider(Protocol):
    def run_memory_job(
        self,
        *,
        system_state: dict,
        tools: object,
        strictness: str,
    ) -> LLMRunResult:
        ...
