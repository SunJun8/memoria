from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from memoria.domain.enums import IssueStatus, JobStatus, ProcessingState, ProposalState
from memoria.infrastructure.db.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RawEntry(Base):
    __tablename__ = "raw_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    hint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    occurred_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    processing_state: Mapped[str] = mapped_column(
        String(40), default=ProcessingState.PENDING.value, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow, nullable=False)


class MemoryEvent(Base):
    __tablename__ = "memory_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_entry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("raw_entries.id"), nullable=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    state: Mapped[str] = mapped_column(String(40), default="accepted", nullable=False)
    corrected_by_event_id: Mapped[Optional[int]] = mapped_column(ForeignKey("memory_events.id"), nullable=True)
    superseded_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    raw_entry: Mapped[Optional[RawEntry]] = relationship()


class MemoryIssue(Base):
    __tablename__ = "memory_issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(40), default=IssueStatus.OPEN.value, nullable=False)
    status_confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    status_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow, nullable=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    superseded_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class IssueComment(Base):
    __tablename__ = "issue_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issue_id: Mapped[int] = mapped_column(ForeignKey("memory_issues.id"), nullable=False)
    event_id: Mapped[Optional[int]] = mapped_column(ForeignKey("memory_events.id"), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str] = mapped_column(String(40), default="llm", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    issue: Mapped[MemoryIssue] = relationship()
    event: Mapped[Optional[MemoryEvent]] = relationship()


class IssueLink(Base):
    __tablename__ = "issue_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_issue_id: Mapped[int] = mapped_column(ForeignKey("memory_issues.id"), nullable=False)
    target_issue_id: Mapped[int] = mapped_column(ForeignKey("memory_issues.id"), nullable=False)
    link_type: Mapped[str] = mapped_column(String(60), nullable=False)
    state: Mapped[str] = mapped_column(String(40), default=ProposalState.PROPOSED.value, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)


class MemoryChain(Base):
    __tablename__ = "memory_chains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow, nullable=False)


class ChainMembership(Base):
    __tablename__ = "chain_memberships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chain_id: Mapped[int] = mapped_column(ForeignKey("memory_chains.id"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    state: Mapped[str] = mapped_column(String(40), default=ProposalState.PROPOSED.value, nullable=False)
    user_locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=utcnow, onupdate=utcnow, nullable=False)
    chain: Mapped[MemoryChain] = relationship()


class Proposal(Base):
    __tablename__ = "proposals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    proposal_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    reason: Mapped[str] = mapped_column(Text, default="", nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    state: Mapped[str] = mapped_column(String(40), default=ProposalState.PROPOSED.value, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class PatchRecord(Base):
    __tablename__ = "patch_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    actor: Mapped[str] = mapped_column(String(40), nullable=False)
    source: Mapped[str] = mapped_column(String(80), nullable=False)
    patch_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    before_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    after_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)


class LLMJob(Base):
    __tablename__ = "llm_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default=JobStatus.RUNNING.value, nullable=False)
    model: Mapped[str] = mapped_column(String(120), nullable=False)
    reasoning_effort: Mapped[str] = mapped_column(String(40), nullable=False)
    strictness: Mapped[str] = mapped_column(String(40), default="balanced", nullable=False)
    transcript_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transcript_sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    final_report_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    patch_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patch_records.id"), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    patch: Mapped[Optional[PatchRecord]] = relationship()


class SleepReport(Base):
    __tablename__ = "sleep_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("llm_jobs.id"), nullable=False)
    report_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    job: Mapped[LLMJob] = relationship()


class Attachment(Base):
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_entry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("raw_entries.id"), nullable=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str] = mapped_column(String(300), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    mtime: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    raw_entry: Mapped[Optional[RawEntry]] = relationship()


class ImportAudit(Base):
    __tablename__ = "import_audits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_entry_id: Mapped[int] = mapped_column(ForeignKey("raw_entries.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    meta: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    raw_entry: Mapped[RawEntry] = relationship()
