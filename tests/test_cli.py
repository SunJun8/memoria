import json

from typer.testing import CliRunner

from memoria.infrastructure.db.session import create_engine_for_path, create_session_factory
from memoria.infrastructure.db.models import LLMJob, Proposal
from memoria.interfaces.cli.app import app


def test_cli_ingest_and_list_issues(monkeypatch, tmp_path):
    db_path = tmp_path / "memoria.db"
    jobs_dir = tmp_path / "jobs"
    monkeypatch.setenv("MEMORIA_DB_PATH", str(db_path))
    monkeypatch.setenv("MEMORIA_JOBS_DIR", str(jobs_dir))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    runner = CliRunner()

    ingest_result = runner.invoke(app, ["ingest", "text", "Build local memory", "--title", "Memory note"])
    assert ingest_result.exit_code == 0
    raw_entry_id = json.loads(ingest_result.stdout)["raw_entry_id"]
    assert raw_entry_id == 1

    sleep_result = runner.invoke(app, ["sleep", "--mock"])
    assert sleep_result.exit_code == 0
    job_id = json.loads(sleep_result.stdout)["job_id"]
    assert job_id == 1
    assert db_path.exists()
    assert any(jobs_dir.glob("*.jsonl"))

    sleep_list = runner.invoke(app, ["sleep", "list", "--json"])
    assert sleep_list.exit_code == 0
    assert json.loads(sleep_list.stdout)[0]["id"] == job_id
    assert json.loads(sleep_list.stdout)[0]["status"] == "succeeded"

    sleep_show = runner.invoke(app, ["sleep", "show", str(job_id), "--json"])
    assert sleep_show.exit_code == 0
    assert json.loads(sleep_show.stdout)["id"] == job_id

    issue_result = runner.invoke(app, ["issue", "list", "--json"])
    assert issue_result.exit_code == 0
    issues = json.loads(issue_result.stdout)
    assert issues[0]["title"] == "Mock consolidated memory"

    issue_show = runner.invoke(app, ["issue", "show", "1", "--json"])
    assert issue_show.exit_code == 0
    assert json.loads(issue_show.stdout)["title"] == "Mock consolidated memory"

    chain_result = runner.invoke(app, ["chain", "list", "--json"])
    assert chain_result.exit_code == 0
    assert json.loads(chain_result.stdout) == []

    proposed_result = runner.invoke(app, ["proposed", "list", "--json"])
    assert proposed_result.exit_code == 0
    assert json.loads(proposed_result.stdout) == []

    patch_result = runner.invoke(app, ["patch", "list", "--json"])
    assert patch_result.exit_code == 0
    assert json.loads(patch_result.stdout)


def test_cli_sleep_mock_creates_git_backup_after_success(monkeypatch, tmp_path):
    db_path = tmp_path / "memoria.db"
    jobs_dir = tmp_path / "jobs"
    backup_repo = tmp_path / "backup-git"
    monkeypatch.setenv("MEMORIA_DB_PATH", str(db_path))
    monkeypatch.setenv("MEMORIA_JOBS_DIR", str(jobs_dir))
    monkeypatch.setenv("MEMORIA_BACKUP_GIT_REPO", str(backup_repo))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    runner = CliRunner()

    assert runner.invoke(app, ["ingest", "text", "Backup after sleep"]).exit_code == 0
    sleep_result = runner.invoke(app, ["sleep", "--mock"])

    assert sleep_result.exit_code == 0
    assert (backup_repo / ".git").exists()
    snapshots = list((backup_repo / "snapshots").glob("*"))
    assert snapshots
    backed_up_db = snapshots[0] / "memoria.db"
    engine = create_engine_for_path(backed_up_db)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        job = session.get(LLMJob, 1)
    assert job.status == "succeeded"


def test_cli_proposed_show(monkeypatch, tmp_path):
    db_path = tmp_path / "memoria.db"
    monkeypatch.setenv("MEMORIA_DB_PATH", str(db_path))
    monkeypatch.setenv("MEMORIA_JOBS_DIR", str(tmp_path / "jobs"))
    runner = CliRunner()
    engine = create_engine_for_path(db_path)
    from memoria.infrastructure.db.session import init_db

    init_db(engine)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        proposal = Proposal(
            proposal_type="merge_chain",
            payload={"chain_ids": [1, 2]},
            reason="same topic",
            confidence=0.8,
        )
        session.add(proposal)
        session.commit()
        proposal_id = proposal.id

    result = runner.invoke(app, ["proposed", "show", str(proposal_id), "--json"])

    assert result.exit_code == 0
    assert json.loads(result.stdout)["reason"] == "same topic"


def test_cli_sleep_without_api_key_fails_before_db_init(monkeypatch, tmp_path):
    db_path = tmp_path / "no-key.db"
    monkeypatch.setenv("MEMORIA_DB_PATH", str(db_path))
    monkeypatch.setenv("MEMORIA_JOBS_DIR", str(tmp_path / "jobs"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    runner = CliRunner()

    result = runner.invoke(app, ["sleep"])

    assert result.exit_code == 1
    assert "OPENAI_API_KEY" in result.output
    assert not db_path.exists()
