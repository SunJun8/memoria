from datetime import datetime

from sqlalchemy import select

from memoria.application.services.ingest_service import IngestRequest, IngestService
from memoria.infrastructure.db.models import ImportAudit, RawEntry


def test_ingest_text_creates_raw_entry(session_factory):
    service = IngestService(session_factory)
    occurred_at = datetime(2026, 5, 13, 9, 0, 0)

    raw_id = service.ingest(
        IngestRequest(
            content="remember this design decision",
            source="text",
            title="Design decision",
            tags=["design"],
            hint="curated",
            occurred_at=occurred_at,
            project_path="/tmp/project",
            metadata={"source_detail": "manual"},
        )
    )

    with session_factory() as session:
        raw = session.get(RawEntry, raw_id)
        audit = session.scalars(select(ImportAudit).where(ImportAudit.raw_entry_id == raw_id)).one()

    assert raw is not None
    assert raw.content == "remember this design decision"
    assert raw.title == "Design decision"
    assert raw.tags == ["design"]
    assert raw.hint == "curated"
    assert raw.occurred_at == occurred_at
    assert raw.meta["source_detail"] == "manual"
    assert raw.meta["project_path"] == "/tmp/project"
    assert raw.processing_state == "pending_processing"
    assert audit.source == "text"
    assert audit.meta == {"title": "Design decision", "tags": ["design"], "hint": "curated"}


def test_ingest_rejects_empty_content(session_factory):
    service = IngestService(session_factory)

    try:
        service.ingest(IngestRequest(content="   ", source="text"))
    except ValueError as exc:
        assert "content" in str(exc)
    else:
        raise AssertionError("expected ValueError")
