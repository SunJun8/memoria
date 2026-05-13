from memoria.application.services.patch_service import PatchService
from memoria.application.services.query_service import QueryService
from memoria.infrastructure.db.models import LLMJob, MemoryChain, PatchRecord, Proposal, SleepReport, utcnow
from memoria.schemas.patches import MemoryPatch


def test_query_lists_issues_and_chains(session_factory):
    patch_service = PatchService(session_factory)
    patch_service.apply_patch(
        MemoryPatch.model_validate(
            {
                "actor": "llm",
                "source": "system_job",
                "operations": [
                    {
                        "operation_id": "op-1",
                        "operation_type": "create_issue",
                        "reason": "test",
                        "confidence": 0.8,
                        "payload": {"title": "Memoria MVP", "summary": "Build it", "tags": ["memoria"]},
                    },
                    {
                        "operation_id": "op-2",
                        "operation_type": "create_or_update_chain",
                        "reason": "test",
                        "confidence": 0.7,
                        "payload": {"title": "AI memory", "summary": "Long-running memory system"},
                    },
                ],
            }
        )
    )

    service = QueryService(session_factory)

    assert service.list_issues()[0]["title"] == "Memoria MVP"
    assert service.list_chains()[0]["title"] == "AI memory"


def test_search_issues_uses_simple_contains(session_factory):
    patch_service = PatchService(session_factory)
    patch_service.apply_patch(
        MemoryPatch.model_validate(
            {
                "actor": "llm",
                "source": "system_job",
                "operations": [
                    {
                        "operation_id": "op-1",
                        "operation_type": "create_issue",
                        "reason": "test",
                        "confidence": 0.8,
                        "payload": {"title": "BL616 power issue", "summary": "low power debug"},
                    }
                ],
            }
        )
    )

    service = QueryService(session_factory)

    assert service.search_issues("power")[0]["title"] == "BL616 power issue"


def test_query_excludes_deleted_chains(session_factory):
    with session_factory() as session:
        visible = MemoryChain(title="Visible chain", summary="active memory")
        deleted = MemoryChain(title="Deleted chain", summary="old memory", deleted_at=utcnow())
        session.add_all([visible, deleted])
        session.commit()
        visible_id = visible.id
        deleted_id = deleted.id

    service = QueryService(session_factory)

    assert [chain["title"] for chain in service.list_chains()] == ["Visible chain"]
    assert [chain["title"] for chain in service.search_chains("memory")] == ["Visible chain"]
    assert service.get_chain(visible_id)["title"] == "Visible chain"
    assert service.get_chain(deleted_id) is None


def test_resolve_proposal_updates_state_and_missing_raises(session_factory):
    with session_factory() as session:
        proposal = Proposal(
            proposal_type="merge_chain",
            payload={"chain_ids": [1, 2]},
            reason="same topic",
            confidence=0.75,
        )
        session.add(proposal)
        session.commit()
        proposal_id = proposal.id

    service = QueryService(session_factory)

    listed = service.list_proposals()
    resolved = service.resolve_proposal(proposal_id, "accepted")

    assert listed[0]["proposal_type"] == "merge_chain"
    assert resolved["state"] == "accepted"
    assert resolved["resolved_at"] is not None
    with session_factory() as session:
        saved = session.get(Proposal, proposal_id)
        assert saved.state == "accepted"
        assert saved.resolved_at is not None

    try:
        service.resolve_proposal(999, "rejected")
    except ValueError as exc:
        assert "proposal" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_query_lists_and_gets_patches(session_factory):
    with session_factory() as session:
        patch = PatchRecord(
            actor="llm",
            source="system_job",
            patch_json={"operations": []},
            before_json={"operation_count": 0},
            after_json={"created_issue_ids": []},
        )
        session.add(patch)
        session.commit()
        patch_id = patch.id

    service = QueryService(session_factory)

    assert service.list_patches()[0]["id"] == patch_id
    assert service.get_patch(patch_id)["after_json"] == {"created_issue_ids": []}
    assert service.get_patch(999) is None


def test_query_lists_sleep_reports_and_gets_sleep_job(session_factory):
    with session_factory() as session:
        job = LLMJob(
            job_type="sleep_consolidation",
            status="succeeded",
            model="mock-model",
            reasoning_effort="medium",
            final_report_json={"mode": "sleep"},
        )
        session.add(job)
        session.flush()
        report = SleepReport(job_id=job.id, report_json={"processed": 1})
        session.add(report)
        session.commit()
        job_id = job.id
        report_id = report.id

    service = QueryService(session_factory)

    assert service.list_sleep_reports()[0]["id"] == report_id
    assert service.list_sleep_reports()[0]["report_json"] == {"processed": 1}
    assert service.get_sleep_job(job_id)["final_report_json"] == {"mode": "sleep"}
    assert service.get_sleep_job(999) is None
