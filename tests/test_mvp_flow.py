import json

from typer.testing import CliRunner

from memoria.interfaces.cli.app import app


def test_mvp_cli_flow(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMORIA_DB_PATH", str(tmp_path / "memoria.db"))
    monkeypatch.setenv("MEMORIA_JOBS_DIR", str(tmp_path / "jobs"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    runner = CliRunner()

    ingest = runner.invoke(app, ["ingest", "text", "Build Memoria", "--title", "MVP"])
    assert ingest.exit_code == 0
    assert json.loads(ingest.stdout)["raw_entry_id"] == 1

    sleep = runner.invoke(app, ["sleep", "--mock"])
    assert sleep.exit_code == 0
    assert json.loads(sleep.stdout)["job_id"] == 1

    issues = runner.invoke(app, ["issue", "list", "--json"])
    assert issues.exit_code == 0
    assert json.loads(issues.stdout)[0]["title"] == "Mock consolidated memory"

    chains = runner.invoke(app, ["chain", "list", "--json"])
    assert chains.exit_code == 0
    assert json.loads(chains.stdout) == []

    proposed = runner.invoke(app, ["proposed", "list", "--json"])
    assert proposed.exit_code == 0
    assert json.loads(proposed.stdout) == []

    backup = runner.invoke(app, ["backup", "create", "--git"])
    assert backup.exit_code == 0
    assert json.loads(backup.stdout)["commit"]
    assert (tmp_path / "data" / "memoria" / "backups" / "git" / ".git").exists()
