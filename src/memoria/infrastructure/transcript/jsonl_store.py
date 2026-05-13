from __future__ import annotations

import hashlib
import json
from pathlib import Path

from memoria.application.ports.transcript_store import TranscriptWriteResult


class JsonlTranscriptStore:
    def __init__(self, root_path: Path) -> None:
        self._root_path = Path(root_path)

    def write(self, job_key: str, events: list[dict]) -> TranscriptWriteResult:
        self._root_path.mkdir(parents=True, exist_ok=True)
        path = self._root_path / f"{job_key}.jsonl"
        with path.open("w", encoding="utf-8") as stream:
            for event in events:
                stream.write(json.dumps(event, ensure_ascii=False, default=str))
                stream.write("\n")

        sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        return TranscriptWriteResult(path=path, sha256=sha256)
