import hashlib

from sqlalchemy import select

from memoria.application.services.ingest_service import IngestRequest, IngestService
from memoria.application.services.association_service import AssociationService
from memoria.application.services.patch_service import PatchService
from memoria.application.services.query_service import QueryService
from memoria.application.services.sleep_service import SleepService
from memoria.application.services.llm_tool_service import LLMToolService
from memoria.infrastructure.db.models import LLMJob, MemoryIssue, RawEntry, SleepReport
from memoria.infrastructure.llm.mock_provider import MockLLMProvider
from memoria.infrastructure.transcript.jsonl_store import JsonlTranscriptStore
from memoria.schemas.llm import LLMRunResult
from memoria.schemas.patches import MemoryPatch, PatchOperation


def test_sleep_with_mock_provider_creates_issue_and_report(session_factory, tmp_path):
    raw_id = IngestService(session_factory).ingest(
        IngestRequest(content="Build Memoria MVP", source="text")
    )
    sleep = SleepService(
        session_factory=session_factory,
        query_service=QueryService(session_factory),
        patch_service=PatchService(session_factory),
        llm_provider=MockLLMProvider(),
        transcript_store=JsonlTranscriptStore(tmp_path),
        model="mock-model",
        reasoning_effort="medium",
    )
    job_id = sleep.run(limit=10, strictness="balanced")
    with session_factory() as session:
        job = session.get(LLMJob, job_id)
        issue = session.scalars(select(MemoryIssue)).one()
        raw = session.get(RawEntry, raw_id)
        report = session.scalars(select(SleepReport)).one()
    assert job.status == "succeeded"
    assert job.patch_id is not None
    assert job.transcript_path
    assert job.transcript_sha256 == hashlib.sha256(
        open(job.transcript_path, "rb").read()
    ).hexdigest()
    assert raw.processing_state == "processed"
    assert issue.title == "Mock consolidated memory"
    assert report.report_json["mode"] == "sleep"


class FailingTranscriptStore:
    def write(self, job_key, events):
        raise RuntimeError("transcript unavailable")


def test_sleep_transcript_failure_does_not_apply_patch(session_factory):
    raw_id = IngestService(session_factory).ingest(
        IngestRequest(content="Build Memoria MVP", source="text")
    )
    sleep = SleepService(
        session_factory=session_factory,
        query_service=QueryService(session_factory),
        patch_service=PatchService(session_factory),
        llm_provider=MockLLMProvider(),
        transcript_store=FailingTranscriptStore(),
        model="mock-model",
        reasoning_effort="medium",
    )

    try:
        sleep.run(limit=10, strictness="balanced")
    except RuntimeError as exc:
        assert "transcript unavailable" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")

    with session_factory() as session:
        job = session.scalars(select(LLMJob)).one()
        raw = session.get(RawEntry, raw_id)
        issues = session.scalars(select(MemoryIssue)).all()
        reports = session.scalars(select(SleepReport)).all()

    assert job.status == "failed"
    assert job.patch_id is None
    assert raw.processing_state == "pending_processing"
    assert issues == []
    assert reports == []


def test_sleep_finalize_failure_rolls_back_patch(session_factory, tmp_path):
    raw_id = IngestService(session_factory).ingest(
        IngestRequest(content="Build Memoria MVP", source="text")
    )
    sleep = SleepService(
        session_factory=session_factory,
        query_service=QueryService(session_factory),
        patch_service=PatchService(session_factory),
        llm_provider=MockLLMProvider(),
        transcript_store=JsonlTranscriptStore(tmp_path),
        model="mock-model",
        reasoning_effort="medium",
        finalize_hook=lambda: (_ for _ in ()).throw(RuntimeError("finalize failed")),
    )

    try:
        sleep.run(limit=10, strictness="balanced")
    except RuntimeError as exc:
        assert "finalize failed" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")

    with session_factory() as session:
        job = session.scalars(select(LLMJob)).one()
        raw = session.get(RawEntry, raw_id)
        issues = session.scalars(select(MemoryIssue)).all()
        reports = session.scalars(select(SleepReport)).all()

    assert job.status == "failed"
    assert job.patch_id is None
    assert raw.processing_state == "pending_processing"
    assert issues == []
    assert reports == []


def test_sleep_after_success_failure_does_not_mark_job_failed(session_factory, tmp_path):
    IngestService(session_factory).ingest(
        IngestRequest(content="Build Memoria MVP", source="text")
    )
    sleep = SleepService(
        session_factory=session_factory,
        query_service=QueryService(session_factory),
        patch_service=PatchService(session_factory),
        llm_provider=MockLLMProvider(),
        transcript_store=JsonlTranscriptStore(tmp_path),
        model="mock-model",
        reasoning_effort="medium",
        after_success_hook=lambda: (_ for _ in ()).throw(RuntimeError("backup failed")),
    )

    try:
        sleep.run(limit=10, strictness="balanced")
    except RuntimeError as exc:
        assert "backup failed" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")

    with session_factory() as session:
        job = session.scalars(select(LLMJob)).one()
        issues = session.scalars(select(MemoryIssue)).all()

    assert job.status == "succeeded"
    assert issues[0].title == "Mock consolidated memory"


class SleepReportWithoutJobIdProvider:
    def run_memory_job(self, *, system_state, tools, strictness):
        patch = MemoryPatch(
            actor="llm",
            source="test_provider",
            operations=[
                PatchOperation(
                    operation_id="test-create-sleep-report",
                    operation_type="create_sleep_report",
                    reason="Provider reports sleep summary without knowing DB job id.",
                    confidence=1.0,
                    payload={"report_json": {"mode": "sleep", "strictness": strictness}},
                )
            ],
        )
        return LLMRunResult(
            patch=patch,
            report={"mode": "sleep", "strictness": strictness},
            transcript_events=[],
        )


def test_sleep_injects_job_id_into_llm_sleep_report_operation(session_factory, tmp_path):
    sleep = SleepService(
        session_factory=session_factory,
        query_service=QueryService(session_factory),
        patch_service=PatchService(session_factory),
        llm_provider=SleepReportWithoutJobIdProvider(),
        transcript_store=JsonlTranscriptStore(tmp_path),
        model="test-model",
        reasoning_effort="medium",
    )

    job_id = sleep.run(limit=10, strictness="balanced")

    with session_factory() as session:
        job = session.get(LLMJob, job_id)
        report = session.scalars(select(SleepReport)).one()

    assert job.status == "succeeded"
    assert report.job_id == job_id
    assert report.report_json == {"mode": "sleep", "strictness": "balanced"}


def test_association_service_records_association_job_type(session_factory, tmp_path):
    IngestService(session_factory).ingest(
        IngestRequest(content="Connect related memories", source="text")
    )
    service = AssociationService(
        session_factory=session_factory,
        query_service=QueryService(session_factory),
        patch_service=PatchService(session_factory),
        llm_provider=MockLLMProvider(),
        transcript_store=JsonlTranscriptStore(tmp_path),
        model="mock-model",
        reasoning_effort="medium",
    )

    job_id = service.run(limit=10, strictness="balanced")

    with session_factory() as session:
        job = session.get(LLMJob, job_id)

    assert job.job_type == "active_association"


def test_llm_tool_service_clamps_limits(session_factory):
    for index in range(3):
        IngestService(session_factory).ingest(
            IngestRequest(content=f"memory {index}", source="text")
        )
    service = LLMToolService(session_factory)

    state = service.get_system_state(9999)

    assert len(state["pending_raw"]) == 3
    assert service.list_issues(limit=-5) == {"issues": []}
