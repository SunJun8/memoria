from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker

from memoria.domain.enums import ProcessingState
from memoria.infrastructure.db.models import MemoryChain, MemoryIssue, RawEntry


class LLMToolService:
    MAX_LIMIT = 100

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_system_state(self, limit: int) -> dict:
        limit = self._clamp_limit(limit)
        with self._session_factory() as session:
            statement = (
                select(RawEntry)
                .where(RawEntry.processing_state == ProcessingState.PENDING.value)
                .order_by(RawEntry.created_at.asc(), RawEntry.id.asc())
                .limit(limit)
            )
            pending_raw = [
                {
                    "id": raw.id,
                    "title": raw.title,
                    "content": raw.content,
                    "hint": raw.hint,
                    "tags": raw.tags,
                }
                for raw in session.scalars(statement).all()
            ]
        return {"pending_raw": pending_raw}

    def list_issues(self, limit: int = 20, status: str | None = None) -> dict:
        limit = self._clamp_limit(limit)
        with self._session_factory() as session:
            statement = select(MemoryIssue).order_by(MemoryIssue.updated_at.desc()).limit(limit)
            if status is not None:
                statement = statement.where(MemoryIssue.status == status)
            issues = [self._issue_dict(issue) for issue in session.scalars(statement).all()]
        return {"issues": issues}

    def search_issues(self, query: str, limit: int = 20) -> dict:
        limit = self._clamp_limit(limit)
        pattern = f"%{query}%"
        with self._session_factory() as session:
            statement = (
                select(MemoryIssue)
                .where(or_(MemoryIssue.title.ilike(pattern), MemoryIssue.summary.ilike(pattern)))
                .order_by(MemoryIssue.updated_at.desc())
                .limit(limit)
            )
            issues = [self._issue_dict(issue) for issue in session.scalars(statement).all()]
        return {"issues": issues}

    def get_issue(self, issue_id: int) -> dict:
        with self._session_factory() as session:
            issue = session.get(MemoryIssue, issue_id)
            if issue is None:
                return {"issue": None}
            return {"issue": self._issue_dict(issue)}

    def list_chains(self, limit: int = 20) -> dict:
        limit = self._clamp_limit(limit)
        with self._session_factory() as session:
            statement = (
                select(MemoryChain)
                .where(MemoryChain.deleted_at.is_(None))
                .order_by(MemoryChain.updated_at.desc())
                .limit(limit)
            )
            chains = [self._chain_dict(chain) for chain in session.scalars(statement).all()]
        return {"chains": chains}

    @staticmethod
    def _issue_dict(issue: MemoryIssue) -> dict:
        return {
            "id": issue.id,
            "title": issue.title,
            "summary": issue.summary,
            "status": issue.status,
            "tags": issue.tags,
            "updated_at": issue.updated_at.isoformat(),
        }

    @staticmethod
    def _chain_dict(chain: MemoryChain) -> dict:
        return {
            "id": chain.id,
            "title": chain.title,
            "summary": chain.summary,
            "description": chain.description,
            "tags": chain.tags,
            "updated_at": chain.updated_at.isoformat(),
        }

    @classmethod
    def _clamp_limit(cls, limit: int) -> int:
        return max(1, min(limit, cls.MAX_LIMIT))
