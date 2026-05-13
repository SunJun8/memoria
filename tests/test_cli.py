import json

from typer.testing import CliRunner

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
