from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from sqlalchemy.orm import Session, sessionmaker

from memoria.infrastructure.db.models import ImportAudit, RawEntry


@dataclass(frozen=True)
class IngestRequest:
    content: str
    source: str
    title: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    hint: Optional[str] = None
    occurred_at: Optional[datetime] = None
    project_path: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class IngestService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def ingest(self, request: IngestRequest) -> int:
        if not request.content.strip():
            raise ValueError("content must not be empty")

        raw_meta = dict(request.metadata)
        if request.project_path is not None:
            raw_meta["project_path"] = request.project_path

        with self._session_factory() as session:
            raw_entry = RawEntry(
                content=request.content,
                title=request.title,
                tags=list(request.tags),
                hint=request.hint,
                occurred_at=request.occurred_at,
                meta=raw_meta,
            )
            session.add(raw_entry)
            session.flush()

            session.add(
                ImportAudit(
                    raw_entry_id=raw_entry.id,
                    source=request.source,
                    meta={
                        "title": request.title,
                        "tags": list(request.tags),
                        "hint": request.hint,
                    },
                )
            )
            session.commit()

            return raw_entry.id
