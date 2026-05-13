from __future__ import annotations

from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker

from memoria.infrastructure.db.models import (
    LLMJob,
    MemoryChain,
    MemoryIssue,
    PatchRecord,
    Proposal,
    SleepReport,
    utcnow,
)
from memoria.domain.enums import JobType


class QueryService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_issues(self, status: Optional[str] = None) -> list[dict]:
        with self._session_factory() as session:
            statement = select(MemoryIssue).order_by(MemoryIssue.updated_at.desc())
            if status is not None:
                statement = statement.where(MemoryIssue.status == status)
            return [self._issue_dict(issue) for issue in session.scalars(statement).all()]

    def search_issues(self, query: str) -> list[dict]:
        pattern = self._contains_pattern(query)
        with self._session_factory() as session:
            statement = (
                select(MemoryIssue)
                .where(
                    or_(
                        MemoryIssue.title.ilike(pattern),
                        MemoryIssue.summary.ilike(pattern),
                    )
                )
                .order_by(MemoryIssue.updated_at.desc())
            )
            return [self._issue_dict(issue) for issue in session.scalars(statement).all()]

    def get_issue(self, issue_id: int) -> Optional[dict]:
        with self._session_factory() as session:
            issue = session.get(MemoryIssue, issue_id)
            if issue is None:
                return None
            return self._issue_dict(issue)

    def list_chains(self) -> list[dict]:
        with self._session_factory() as session:
            statement = (
                select(MemoryChain)
                .where(MemoryChain.deleted_at.is_(None))
                .order_by(MemoryChain.updated_at.desc())
            )
            return [self._chain_dict(chain) for chain in session.scalars(statement).all()]

    def search_chains(self, query: str) -> list[dict]:
        pattern = self._contains_pattern(query)
        with self._session_factory() as session:
            statement = (
                select(MemoryChain)
                .where(
                    MemoryChain.deleted_at.is_(None),
                    or_(
                        MemoryChain.title.ilike(pattern),
                        MemoryChain.summary.ilike(pattern),
                    ),
                )
                .order_by(MemoryChain.updated_at.desc())
            )
            return [self._chain_dict(chain) for chain in session.scalars(statement).all()]

    def get_chain(self, chain_id: int) -> Optional[dict]:
        with self._session_factory() as session:
            chain = session.get(MemoryChain, chain_id)
            if chain is None or chain.deleted_at is not None:
                return None
            return self._chain_dict(chain)

    def list_proposals(self) -> list[dict]:
        with self._session_factory() as session:
            statement = select(Proposal).order_by(Proposal.created_at.desc())
            return [self._proposal_dict(proposal) for proposal in session.scalars(statement).all()]

    def get_proposal(self, proposal_id: int) -> Optional[dict]:
        with self._session_factory() as session:
            proposal = session.get(Proposal, proposal_id)
            if proposal is None:
                return None
            return self._proposal_dict(proposal)

    def resolve_proposal(self, proposal_id: int, state: str) -> dict:
        with self._session_factory() as session:
            proposal = session.get(Proposal, proposal_id)
            if proposal is None:
                raise ValueError(f"missing proposal {proposal_id}")

            proposal.state = state
            proposal.resolved_at = utcnow()
            result = self._proposal_dict(proposal)
            session.commit()
            return result

    def list_patches(self) -> list[dict]:
        with self._session_factory() as session:
            statement = select(PatchRecord).order_by(PatchRecord.created_at.desc())
            return [self._patch_dict(patch) for patch in session.scalars(statement).all()]

    def get_patch(self, patch_id: int) -> Optional[dict]:
        with self._session_factory() as session:
            patch = session.get(PatchRecord, patch_id)
            if patch is None:
                return None
            return self._patch_dict(patch)

    def list_sleep_reports(self) -> list[dict]:
        with self._session_factory() as session:
            statement = select(SleepReport).order_by(SleepReport.created_at.desc())
            return [self._sleep_report_dict(report) for report in session.scalars(statement).all()]

    def list_sleep_jobs(self) -> list[dict]:
        with self._session_factory() as session:
            statement = (
                select(LLMJob)
                .where(LLMJob.job_type == JobType.SLEEP.value)
                .order_by(LLMJob.created_at.desc(), LLMJob.id.desc())
            )
            return [self._job_dict(job) for job in session.scalars(statement).all()]

    def get_sleep_job(self, job_id: int) -> Optional[dict]:
        with self._session_factory() as session:
            job = session.get(LLMJob, job_id)
            if job is None or job.job_type != JobType.SLEEP.value:
                return None
            return self._job_dict(job)

    @staticmethod
    def _issue_dict(issue: MemoryIssue) -> dict:
        return {
            "id": issue.id,
            "title": issue.title,
            "summary": issue.summary,
            "status": issue.status,
            "status_confidence": issue.status_confidence,
            "status_reason": issue.status_reason,
            "tags": issue.tags,
            "created_at": issue.created_at,
            "updated_at": issue.updated_at,
            "archived_at": issue.archived_at,
            "superseded_at": issue.superseded_at,
        }

    @staticmethod
    def _chain_dict(chain: MemoryChain) -> dict:
        return {
            "id": chain.id,
            "title": chain.title,
            "summary": chain.summary,
            "description": chain.description,
            "tags": chain.tags,
            "deleted_at": chain.deleted_at,
            "created_at": chain.created_at,
            "updated_at": chain.updated_at,
        }

    @staticmethod
    def _proposal_dict(proposal: Proposal) -> dict:
        return {
            "id": proposal.id,
            "proposal_type": proposal.proposal_type,
            "payload": proposal.payload,
            "reason": proposal.reason,
            "confidence": proposal.confidence,
            "state": proposal.state,
            "created_at": proposal.created_at,
            "resolved_at": proposal.resolved_at,
        }

    @staticmethod
    def _patch_dict(patch: PatchRecord) -> dict:
        return {
            "id": patch.id,
            "actor": patch.actor,
            "source": patch.source,
            "patch_json": patch.patch_json,
            "before_json": patch.before_json,
            "after_json": patch.after_json,
            "created_at": patch.created_at,
        }

    @staticmethod
    def _sleep_report_dict(report: SleepReport) -> dict:
        return {
            "id": report.id,
            "job_id": report.job_id,
            "report_json": report.report_json,
            "created_at": report.created_at,
        }

    @staticmethod
    def _job_dict(job: LLMJob) -> dict:
        return {
            "id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "model": job.model,
            "reasoning_effort": job.reasoning_effort,
            "strictness": job.strictness,
            "transcript_path": job.transcript_path,
            "transcript_sha256": job.transcript_sha256,
            "final_report_json": job.final_report_json,
            "patch_id": job.patch_id,
            "error": job.error,
            "created_at": job.created_at,
            "completed_at": job.completed_at,
        }

    @staticmethod
    def _contains_pattern(query: str) -> str:
        return f"%{query}%"
