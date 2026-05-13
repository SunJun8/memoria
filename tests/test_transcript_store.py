import json
import hashlib

from memoria.infrastructure.transcript.jsonl_store import JsonlTranscriptStore


def test_jsonl_transcript_store_writes_events(tmp_path):
    store = JsonlTranscriptStore(tmp_path)
    result = store.write("job-1", [{"type": "request", "payload": {"hello": "world"}}])
    assert result.path.exists()
    lines = result.path.read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0])["type"] == "request"
    assert len(result.sha256) == 64
    assert result.sha256 == hashlib.sha256(result.path.read_bytes()).hexdigest()
