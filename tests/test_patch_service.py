from sqlalchemy import select

from memoria.application.services.patch_service import PatchService
from memoria.infrastructure.db.models import ChainMembership, IssueLink, MemoryChain, MemoryEvent, MemoryIssue, PatchRecord, RawEntry
from memoria.schemas.patches import MemoryPatch


def test_apply_create_issue_patch_records_audit(session_factory):
    service = PatchService(session_factory)
    patch = MemoryPatch.model_validate(
        {
            "actor": "llm",
            "source": "system_job",
            "operations": [
                {
                    "operation_id": "op-1",
                    "operation_type": "create_issue",
                    "reason": "new issue",
                    "confidence": 0.91,
                    "payload": {
                        "title": "Memory MVP",
                        "summary": "Implement the first version",
                        "tags": ["memoria"],
                    },
                    "refs": {"raw_entry_ids": [1]},
                }
            ],
        }
    )

    patch_id = service.apply_patch(patch)

    with session_factory() as session:
        issue = session.scalars(select(MemoryIssue)).one()
        record = session.get(PatchRecord, patch_id)

    assert issue.title == "Memory MVP"
    assert issue.summary == "Implement the first version"
    assert issue.status == "open"
    assert record is not None
    assert record.after_json["created_issue_ids"] == [issue.id]


def test_apply_patch_does_not_support_delete(session_factory):
    service = PatchService(session_factory)

    try:
        service.apply_operation_dict(
            {
                "operation_id": "op-1",
                "operation_type": "delete_issue",
                "reason": "not allowed",
                "confidence": 1.0,
                "payload": {"issue_id": 1},
            }
        )
    except ValueError as exc:
        assert "delete_issue" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_apply_operation_dict_does_not_write_without_audit(session_factory):
    service = PatchService(session_factory)

    try:
        service.apply_operation_dict(
            {
                "operation_id": "op-1",
                "operation_type": "create_issue",
                "reason": "single operation writes need patch audit",
                "confidence": 0.9,
                "payload": {"title": "Unsafe write"},
            }
        )
    except ValueError as exc:
        assert "apply_patch" in str(exc)
    else:
        raise AssertionError("expected ValueError")

    with session_factory() as session:
        assert session.scalars(select(MemoryIssue)).all() == []
        assert session.scalars(select(PatchRecord)).all() == []


def test_apply_patch_rolls_back_when_later_operation_fails(session_factory):
    service = PatchService(session_factory)
    patch = MemoryPatch.model_validate(
        {
            "actor": "llm",
            "source": "system_job",
            "operations": [
                {
                    "operation_id": "op-1",
                    "operation_type": "create_issue",
                    "reason": "new issue",
                    "confidence": 0.91,
                    "payload": {
                        "title": "Memory MVP",
                        "summary": "Implement the first version",
                    },
                },
                {
                    "operation_id": "op-2",
                    "operation_type": "update_issue",
                    "reason": "missing target should fail",
                    "confidence": 0.9,
                    "payload": {"issue_id": 999, "status": "closed"},
                },
            ],
        }
    )

    try:
        service.apply_patch(patch)
    except ValueError as exc:
        assert "issue" in str(exc)
    else:
        raise AssertionError("expected ValueError")

    with session_factory() as session:
        issues = session.scalars(select(MemoryIssue)).all()
        records = session.scalars(select(PatchRecord)).all()

    assert issues == []
    assert records == []


def test_create_event_rejects_missing_raw_entry(session_factory):
    service = PatchService(session_factory)
    patch = MemoryPatch.model_validate(
        {
            "actor": "llm",
            "source": "system_job",
            "operations": [
                {
                    "operation_id": "op-1",
                    "operation_type": "create_event",
                    "reason": "missing raw should fail",
                    "confidence": 0.9,
                    "payload": {
                        "raw_entry_id": 999,
                        "event_type": "work_event",
                        "title": "Bad event",
                        "content": "Should not be created",
                    },
                }
            ],
        }
    )

    try:
        service.apply_patch(patch)
    except ValueError as exc:
        assert "raw entry" in str(exc)
    else:
        raise AssertionError("expected ValueError")

    with session_factory() as session:
        assert session.scalars(select(MemoryEvent)).all() == []
        assert session.scalars(select(PatchRecord)).all() == []


def test_add_to_chain_rejects_missing_target(session_factory):
    service = PatchService(session_factory)
    with session_factory() as session:
        chain = MemoryChain(title="Existing chain")
        session.add(chain)
        session.commit()
        chain_id = chain.id

    patch = MemoryPatch.model_validate(
        {
            "actor": "llm",
            "source": "system_job",
            "operations": [
                {
                    "operation_id": "op-1",
                    "operation_type": "add_to_chain",
                    "reason": "missing issue should fail",
                    "confidence": 0.9,
                    "payload": {
                        "chain_id": chain_id,
                        "target_type": "issue",
                        "target_id": 999,
                        "weight": 0.7,
                    },
                }
            ],
        }
    )

    try:
        service.apply_patch(patch)
    except ValueError as exc:
        assert "issue" in str(exc)
    else:
        raise AssertionError("expected ValueError")

    with session_factory() as session:
        assert session.scalars(select(ChainMembership)).all() == []
        assert session.scalars(select(PatchRecord)).all() == []


def test_after_json_uses_plan_key_names_for_links_and_memberships(session_factory):
    service = PatchService(session_factory)
    with session_factory() as session:
        source = MemoryIssue(title="Source")
        target = MemoryIssue(title="Target")
        chain = MemoryChain(title="Chain")
        session.add_all([source, target, chain])
        session.commit()
        source_id = source.id
        target_id = target.id
        chain_id = chain.id

    patch = MemoryPatch.model_validate(
        {
            "actor": "llm",
            "source": "system_job",
            "operations": [
                {
                    "operation_id": "op-1",
                    "operation_type": "link_issues",
                    "reason": "related",
                    "confidence": 0.8,
                    "payload": {
                        "source_issue_id": source_id,
                        "target_issue_id": target_id,
                        "link_type": "relates_to",
                    },
                },
                {
                    "operation_id": "op-2",
                    "operation_type": "add_to_chain",
                    "reason": "important in chain",
                    "confidence": 0.8,
                    "payload": {
                        "chain_id": chain_id,
                        "target_type": "issue",
                        "target_id": source_id,
                    },
                },
            ],
        }
    )

    patch_id = service.apply_patch(patch)

    with session_factory() as session:
        link = session.scalars(select(IssueLink)).one()
        membership = session.scalars(select(ChainMembership)).one()
        record = session.get(PatchRecord, patch_id)

    assert record.after_json["created_link_ids"] == [link.id]
    assert record.after_json["created_membership_ids"] == [membership.id]


def test_mark_raw_processed_accepts_single_raw_entry_id(session_factory):
    service = PatchService(session_factory)
    with session_factory() as session:
        raw = RawEntry(content="pending")
        session.add(raw)
        session.commit()
        raw_id = raw.id

    patch = MemoryPatch.model_validate(
        {
            "actor": "llm",
            "source": "system_job",
            "operations": [
                {
                    "operation_id": "op-1",
                    "operation_type": "mark_raw_processed",
                    "reason": "processed",
                    "confidence": 1.0,
                    "payload": {"raw_entry_id": raw_id},
                }
            ],
        }
    )

    service.apply_patch(patch)

    with session_factory() as session:
        saved = session.get(RawEntry, raw_id)

    assert saved.processing_state == "processed"
