from __future__ import annotations

from typing import Callable, Optional

from sqlalchemy.orm import Session, sessionmaker

from memoria.application.ports.llm_provider import LLMProvider
from memoria.application.ports.transcript_store import TranscriptStore
from memoria.application.services.llm_tool_service import LLMToolService
from memoria.application.services.patch_service import PatchService
from memoria.application.services.query_service import QueryService
from memoria.domain.enums import JobStatus, JobType
from memoria.infrastructure.db.models import LLMJob, SleepReport, utcnow


class SleepService:
    _job_type = JobType.SLEEP.value

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        query_service: QueryService,
        patch_service: PatchService,
        llm_provider: LLMProvider,
        transcript_store: TranscriptStore,
        model: str,
        reasoning_effort: str,
        finalize_hook: Optional[Callable[[], None]] = None,
    ) -> None:
        self._session_factory = session_factory
        self._query_service = query_service
        self._patch_service = patch_service
        self._llm_provider = llm_provider
        self._transcript_store = transcript_store
        self._model = model
        self._reasoning_effort = reasoning_effort
        self._tools = LLMToolService(session_factory)
        self._finalize_hook = finalize_hook

    def run(self, limit: int, strictness: str) -> int:
        job_id = self._create_job(strictness)
        try:
            system_state = self._tools.get_system_state(limit)
            result = self._llm_provider.run_memory_job(
                system_state=system_state,
                tools=self._tools,
                strictness=strictness,
            )
            transcript = self._transcript_store.write(
                f"llm-job-{job_id}",
                result.transcript_events,
            )
            with self._session_factory() as session:
                try:
                    result.patch.job_id = job_id
                    patch_id = self._patch_service.apply_patch_in_session(session, result.patch)
                    job = session.get(LLMJob, job_id)
                    if job is None:
                        raise ValueError(f"missing job {job_id}")
                    job.status = JobStatus.SUCCEEDED.value
                    job.patch_id = patch_id
                    job.transcript_path = str(transcript.path)
                    job.transcript_sha256 = transcript.sha256
                    job.final_report_json = result.report
                    job.completed_at = utcnow()
                    session.add(SleepReport(job_id=job_id, report_json=result.report))
                    if self._finalize_hook is not None:
                        self._finalize_hook()
                    session.commit()
                except Exception:
                    session.rollback()
                    raise
            return job_id
        except Exception as exc:
            self._mark_failed(job_id, exc)
            raise

    def _create_job(self, strictness: str) -> int:
        with self._session_factory() as session:
            job = LLMJob(
                job_type=self._job_type,
                status=JobStatus.RUNNING.value,
                model=self._model,
                reasoning_effort=self._reasoning_effort,
                strictness=strictness,
            )
            session.add(job)
            session.flush()
            job_id = job.id
            session.commit()
            return job_id

    def _mark_failed(self, job_id: int, exc: Exception) -> None:
        with self._session_factory() as session:
            job = session.get(LLMJob, job_id)
            if job is None:
                return
            job.status = JobStatus.FAILED.value
            job.error = str(exc)
            job.completed_at = utcnow()
            session.commit()
