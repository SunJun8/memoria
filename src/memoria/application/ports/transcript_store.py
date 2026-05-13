from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class TranscriptWriteResult:
    path: Path
    sha256: str


class TranscriptStore(Protocol):
    def write(self, job_key: str, events: list[dict]) -> TranscriptWriteResult:
        ...
