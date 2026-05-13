from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from memoria.domain.enums import ProcessingState
from memoria.infrastructure.db.models import RawEntry


class LLMToolService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_system_state(self, limit: int) -> dict:
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
