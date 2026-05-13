from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from memoria.domain.enums import ProcessingState
from memoria.infrastructure.db.models import (
    ChainMembership,
    IssueComment,
    IssueLink,
    LLMJob,
    MemoryChain,
    MemoryEvent,
    MemoryIssue,
    PatchRecord,
    Proposal,
    RawEntry,
    SleepReport,
)
from memoria.schemas.patches import MemoryPatch, PatchOperation


class PatchService:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def apply_patch(self, patch: MemoryPatch) -> int:
        with self._session_factory() as session:
            try:
                patch_id = self.apply_patch_in_session(session, patch)
                session.commit()
                return patch_id
            except Exception:
                session.rollback()
                raise

    def apply_patch_in_session(self, session: Session, patch: MemoryPatch) -> int:
        before_json = self._before_json(patch)
        after_json = self._empty_after_json()

        for operation in patch.operations:
            self._apply_operation(session, operation, after_json)

        record = PatchRecord(
            actor=patch.actor,
            source=patch.source,
            patch_json=patch.model_dump(mode="json"),
            before_json=before_json,
            after_json=after_json,
        )
        session.add(record)
        session.flush()

        if patch.job_id is not None:
            job = session.get(LLMJob, patch.job_id)
            if job is None:
                raise ValueError(f"missing job {patch.job_id}")
            job.patch_id = record.id

        return record.id

    def apply_operation_dict(self, operation_dict: dict[str, Any]) -> dict[str, list[int]]:
        operation_type = operation_dict.get("operation_type")
        if isinstance(operation_type, str) and operation_type.startswith("delete_"):
            raise ValueError(f"unsupported operation {operation_type}")

        raise ValueError("single-operation writes must use apply_patch for audit")

    def _apply_operation(
        self,
        session: Session,
        operation: PatchOperation,
        after_json: dict[str, list[int]],
    ) -> None:
        operation_type = operation.operation_type
        if operation_type.startswith("delete_"):
            raise ValueError(f"unsupported operation {operation_type}")

        handlers = {
            "create_event": self._create_event,
            "create_issue": self._create_issue,
            "update_issue": self._update_issue,
            "append_comment": self._append_comment,
            "link_issues": self._link_issues,
            "create_or_update_chain": self._create_or_update_chain,
            "add_to_chain": self._add_to_chain,
            "update_chain_membership_weight": self._update_chain_membership_weight,
            "create_proposal": self._create_proposal,
            "mark_raw_processed": self._mark_raw_processed,
            "create_sleep_report": self._create_sleep_report,
        }
        handler = handlers.get(operation_type)
        if handler is None:
            raise ValueError(f"unsupported operation {operation_type}")
        handler(session, operation, after_json)

    def _create_event(
        self,
        session: Session,
        operation: PatchOperation,
        after_json: dict[str, list[int]],
    ) -> None:
        payload = operation.payload
        raw_entry_id = payload.get("raw_entry_id")
        if raw_entry_id is not None and session.get(RawEntry, raw_entry_id) is None:
            raise ValueError(f"missing raw entry {raw_entry_id}")
        corrected_by_event_id = payload.get("corrected_by_event_id")
        if corrected_by_event_id is not None and session.get(MemoryEvent, corrected_by_event_id) is None:
            raise ValueError(f"missing event {corrected_by_event_id}")
        event = MemoryEvent(
            raw_entry_id=raw_entry_id,
            event_type=self._required(payload, "event_type"),
            title=self._required(payload, "title"),
            content=payload.get("content", payload.get("summary", "")),
            confidence=operation.confidence,
            state=payload.get("state", "accepted"),
            corrected_by_event_id=corrected_by_event_id,
            superseded_at=payload.get("superseded_at"),
        )
        session.add(event)
        session.flush()
        after_json["created_event_ids"].append(event.id)

    def _create_issue(
        self,
        session: Session,
        operation: PatchOperation,
        after_json: dict[str, list[int]],
    ) -> None:
        payload = operation.payload
        issue = MemoryIssue(
            title=self._required(payload, "title"),
            summary=payload.get("summary", ""),
            status=payload.get("status", "open"),
            status_confidence=payload.get("status_confidence", operation.confidence),
            status_reason=payload.get("status_reason", operation.reason),
            tags=list(payload.get("tags", [])),
        )
        session.add(issue)
        session.flush()
        after_json["created_issue_ids"].append(issue.id)

    def _update_issue(
        self,
        session: Session,
        operation: PatchOperation,
        after_json: dict[str, list[int]],
    ) -> None:
        payload = operation.payload
        issue_id = self._required(payload, "issue_id")
        issue = session.get(MemoryIssue, issue_id)
        if issue is None:
            raise ValueError(f"missing issue {issue_id}")

        for field in (
            "title",
            "summary",
            "status",
            "status_confidence",
            "status_reason",
            "tags",
            "archived_at",
            "superseded_at",
        ):
            if field in payload:
                value = list(payload[field]) if field == "tags" else payload[field]
                setattr(issue, field, value)
        after_json["updated_issue_ids"].append(issue.id)

    def _append_comment(
        self,
        session: Session,
        operation: PatchOperation,
        after_json: dict[str, list[int]],
    ) -> None:
        payload = operation.payload
        issue_id = self._required(payload, "issue_id")
        if session.get(MemoryIssue, issue_id) is None:
            raise ValueError(f"missing issue {issue_id}")

        event_id = payload.get("event_id")
        if event_id is not None and session.get(MemoryEvent, event_id) is None:
            raise ValueError(f"missing event {event_id}")

        comment = IssueComment(
            issue_id=issue_id,
            event_id=event_id,
            content=self._required(payload, "content"),
            author=payload.get("author", "llm"),
        )
        session.add(comment)
        session.flush()
        after_json["created_comment_ids"].append(comment.id)

    def _link_issues(
        self,
        session: Session,
        operation: PatchOperation,
        after_json: dict[str, list[int]],
    ) -> None:
        payload = operation.payload
        source_issue_id = self._required(payload, "source_issue_id")
        target_issue_id = self._required(payload, "target_issue_id")
        self._require_issue(session, source_issue_id)
        self._require_issue(session, target_issue_id)

        link = IssueLink(
            source_issue_id=source_issue_id,
            target_issue_id=target_issue_id,
            link_type=self._required(payload, "link_type"),
            state=payload.get("state", "proposed"),
            reason=payload.get("reason", operation.reason),
            confidence=operation.confidence,
        )
        session.add(link)
        session.flush()
        after_json["created_link_ids"].append(link.id)

    def _create_or_update_chain(
        self,
        session: Session,
        operation: PatchOperation,
        after_json: dict[str, list[int]],
    ) -> None:
        payload = operation.payload
        chain_id = payload.get("chain_id")
        chain = session.get(MemoryChain, chain_id) if chain_id is not None else None
        if chain_id is not None and chain is None:
            raise ValueError(f"missing chain {chain_id}")

        if chain is None:
            chain = MemoryChain(
                title=self._required(payload, "title"),
                summary=payload.get("summary", ""),
                description=payload.get("description", ""),
                tags=list(payload.get("tags", [])),
            )
            session.add(chain)
            session.flush()
            after_json["created_chain_ids"].append(chain.id)
            return

        for field in ("title", "summary", "description", "tags", "deleted_at"):
            if field in payload:
                value = list(payload[field]) if field == "tags" else payload[field]
                setattr(chain, field, value)
        after_json["updated_chain_ids"].append(chain.id)

    def _add_to_chain(
        self,
        session: Session,
        operation: PatchOperation,
        after_json: dict[str, list[int]],
    ) -> None:
        payload = operation.payload
        chain_id = self._required(payload, "chain_id")
        if session.get(MemoryChain, chain_id) is None:
            raise ValueError(f"missing chain {chain_id}")
        target_type = self._required(payload, "target_type")
        target_id = self._required(payload, "target_id")
        self._require_chain_target(session, target_type, target_id)

        membership = ChainMembership(
            chain_id=chain_id,
            target_type=target_type,
            target_id=target_id,
            weight=payload.get("weight", 0.5),
            reason=payload.get("reason", operation.reason),
            confidence=operation.confidence,
            state=payload.get("state", "proposed"),
            user_locked=payload.get("user_locked", False),
        )
        session.add(membership)
        session.flush()
        after_json["created_membership_ids"].append(membership.id)

    def _update_chain_membership_weight(
        self,
        session: Session,
        operation: PatchOperation,
        after_json: dict[str, list[int]],
    ) -> None:
        payload = operation.payload
        membership_id = self._required(payload, "membership_id")
        membership = session.get(ChainMembership, membership_id)
        if membership is None:
            raise ValueError(f"missing chain membership {membership_id}")

        membership.weight = self._required(payload, "weight")
        if "reason" in payload:
            membership.reason = payload["reason"]
        if "confidence" in payload:
            membership.confidence = payload["confidence"]
        if "state" in payload:
            membership.state = payload["state"]
        after_json["updated_chain_membership_ids"].append(membership.id)

    def _create_proposal(
        self,
        session: Session,
        operation: PatchOperation,
        after_json: dict[str, list[int]],
    ) -> None:
        payload = operation.payload
        proposal = Proposal(
            proposal_type=self._required(payload, "proposal_type"),
            payload=payload.get("payload", {}),
            reason=payload.get("reason", operation.reason),
            confidence=operation.confidence,
            state=payload.get("state", "proposed"),
        )
        session.add(proposal)
        session.flush()
        after_json["created_proposal_ids"].append(proposal.id)

    def _mark_raw_processed(
        self,
        session: Session,
        operation: PatchOperation,
        after_json: dict[str, list[int]],
    ) -> None:
        payload = operation.payload
        raw_entry_ids = payload.get("raw_entry_ids") or operation.refs.get("raw_entry_ids")
        if raw_entry_ids is None and payload.get("raw_entry_id") is not None:
            raw_entry_ids = [payload["raw_entry_id"]]
        if not raw_entry_ids:
            raise ValueError("missing raw_entry_ids")

        for raw_entry_id in raw_entry_ids:
            raw_entry = session.get(RawEntry, raw_entry_id)
            if raw_entry is None:
                raise ValueError(f"missing raw entry {raw_entry_id}")
            raw_entry.processing_state = payload.get(
                "processing_state", ProcessingState.PROCESSED.value
            )
            after_json["processed_raw_entry_ids"].append(raw_entry.id)

    def _create_sleep_report(
        self,
        session: Session,
        operation: PatchOperation,
        after_json: dict[str, list[int]],
    ) -> None:
        payload = operation.payload
        job_id = self._required(payload, "job_id")
        if session.get(LLMJob, job_id) is None:
            raise ValueError(f"missing job {job_id}")

        report = SleepReport(
            job_id=job_id,
            report_json=payload.get("report_json", payload.get("report", {})),
        )
        session.add(report)
        session.flush()
        after_json["created_sleep_report_ids"].append(report.id)

    def _require_issue(self, session: Session, issue_id: int) -> None:
        if session.get(MemoryIssue, issue_id) is None:
            raise ValueError(f"missing issue {issue_id}")

    def _require_chain_target(self, session: Session, target_type: str, target_id: int) -> None:
        if target_type == "issue":
            if session.get(MemoryIssue, target_id) is None:
                raise ValueError(f"missing issue {target_id}")
            return
        if target_type in {"event", "insight"}:
            if session.get(MemoryEvent, target_id) is None:
                raise ValueError(f"missing event {target_id}")
            return
        if target_type == "raw_entry":
            if session.get(RawEntry, target_id) is None:
                raise ValueError(f"missing raw entry {target_id}")
            return
        raise ValueError(f"unsupported chain target type {target_type}")

    @staticmethod
    def _required(payload: dict[str, Any], field: str) -> Any:
        if field not in payload or payload[field] is None:
            raise ValueError(f"missing {field}")
        return payload[field]

    @staticmethod
    def _before_json(patch: MemoryPatch) -> dict[str, Any]:
        return {
            "operation_ids": [operation.operation_id for operation in patch.operations],
            "operation_count": len(patch.operations),
        }

    @staticmethod
    def _empty_after_json() -> dict[str, list[int]]:
        return {
            "created_event_ids": [],
            "created_issue_ids": [],
            "updated_issue_ids": [],
            "created_comment_ids": [],
            "created_link_ids": [],
            "created_chain_ids": [],
            "updated_chain_ids": [],
            "created_membership_ids": [],
            "updated_chain_membership_ids": [],
            "created_proposal_ids": [],
            "processed_raw_entry_ids": [],
            "created_sleep_report_ids": [],
        }
