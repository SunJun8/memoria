import json
import tomllib
from pathlib import Path

from typer.testing import CliRunner

from memoria import __version__
from memoria.infrastructure.llm.mock_provider import MockLLMProvider
from memoria.infrastructure.db.session import create_engine_for_path, create_session_factory
from memoria.infrastructure.db.models import LLMJob, Proposal
from memoria.interfaces.cli.app import app
from memoria.interfaces.cli.commands import sleep as sleep_command


def test_package_version_matches_pyproject():
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    project_version = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))["project"]["version"]

    assert __version__ == project_version


def test_cli_version_shows_runtime_build_info(monkeypatch):
    monkeypatch.setenv("MEMORIA_BUILD_TIME", "2026-05-15T03:04:05Z")
    runner = CliRunner()

    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert f"Memoria {__version__}" in result.stdout
    assert "Build time: 2026-05-15T03:04:05Z" in result.stdout
    assert "Python:" in result.stdout
    assert "Platform:" in result.stdout


def test_cli_version_uses_unknown_build_time_fallback(monkeypatch):
    monkeypatch.delenv("MEMORIA_BUILD_TIME", raising=False)
    runner = CliRunner()

    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert "Build time: unknown" in result.stdout


def test_version_info_falls_back_when_build_info_missing(monkeypatch):
    import builtins
    import importlib

    import memoria.version as version_module

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "memoria.build_info":
            raise ModuleNotFoundError(name=name)
        return real_import(name, *args, **kwargs)

    monkeypatch.delenv("MEMORIA_BUILD_TIME", raising=False)
    monkeypatch.setattr(builtins, "__import__", fake_import)
    try:
        version_module = importlib.reload(version_module)
        assert version_module.get_version_info().build_time == "unknown"
    finally:
        importlib.reload(version_module)


def test_version_info_reraises_nested_build_info_import_error(monkeypatch):
    import builtins

    import pytest

    from memoria.version import get_version_info

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "memoria.build_info":
            raise ModuleNotFoundError(name="missing_dependency")
        return real_import(name, *args, **kwargs)

    monkeypatch.delenv("MEMORIA_BUILD_TIME", raising=False)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ModuleNotFoundError) as exc_info:
        get_version_info()

    assert exc_info.value.name == "missing_dependency"


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
    monkeypatch.setenv("MEMORIA_CONFIG", str(tmp_path / "config.toml"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    runner = CliRunner()

    result = runner.invoke(app, ["sleep"])

    assert result.exit_code == 1
    assert "OPENAI_API_KEY" in result.output
    assert not db_path.exists()


def test_cli_sleep_uses_api_key_from_config_file(monkeypatch, tmp_path):
    db_path = tmp_path / "configured-key.db"
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        """
[openai]
api_key = "configured-api-key"
""",
        encoding="utf-8",
    )
    monkeypatch.setenv("MEMORIA_CONFIG", str(config_path))
    monkeypatch.setenv("MEMORIA_DB_PATH", str(db_path))
    monkeypatch.setenv("MEMORIA_JOBS_DIR", str(tmp_path / "jobs"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    captured = {}

    class FakeOpenAIProvider(MockLLMProvider):
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(sleep_command, "OpenAIProvider", FakeOpenAIProvider)
    runner = CliRunner()

    result = runner.invoke(app, ["sleep"])

    assert result.exit_code == 0
    assert captured["api_key"] == "configured-api-key"
    assert "OPENAI_API_KEY" not in result.output
