from pathlib import Path

from memoria.config import MemoriaConfig, load_config


def test_default_paths_follow_xdg(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.delenv("MEMORIA_DB_PATH", raising=False)
    monkeypatch.delenv("MEMORIA_CONFIG", raising=False)

    config = load_config()

    assert config.config_path == tmp_path / "config" / "memoria" / "config.toml"
    assert config.db_path == tmp_path / "data" / "memoria" / "memoria.db"
    assert config.jobs_dir == tmp_path / "data" / "memoria" / "jobs"
    assert config.backup_git_repo == tmp_path / "data" / "memoria" / "backups" / "git"
    assert config.logs_dir == tmp_path / "state" / "memoria" / "logs"


def test_env_overrides_db_and_model(monkeypatch, tmp_path):
    monkeypatch.setenv("MEMORIA_CONFIG", str(tmp_path / "config.toml"))
    monkeypatch.setenv("MEMORIA_DB_PATH", str(tmp_path / "custom.db"))
    monkeypatch.setenv("MEMORIA_JOBS_DIR", str(tmp_path / "custom-jobs"))
    monkeypatch.setenv("MEMORIA_BACKUP_GIT_REPO", str(tmp_path / "custom-git"))
    monkeypatch.setenv("MEMORIA_LLM_MODEL", "gpt-test-model")
    monkeypatch.setenv("MEMORIA_REASONING_SUMMARY", "detailed")

    config = load_config()

    assert config.config_path == tmp_path / "config.toml"
    assert config.db_path == tmp_path / "custom.db"
    assert config.jobs_dir == tmp_path / "custom-jobs"
    assert config.backup_git_repo == tmp_path / "custom-git"
    assert config.llm_model == "gpt-test-model"
    assert config.reasoning_effort == "medium"
    assert config.reasoning_summary == "detailed"


def test_empty_path_env_values_fall_back_to_xdg(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("MEMORIA_CONFIG", "")
    monkeypatch.setenv("MEMORIA_DB_PATH", "")
    monkeypatch.setenv("MEMORIA_JOBS_DIR", "")

    config = load_config()

    assert config.config_path == tmp_path / "config" / "memoria" / "config.toml"
    assert config.db_path == tmp_path / "data" / "memoria" / "memoria.db"
    assert config.jobs_dir == tmp_path / "data" / "memoria" / "jobs"


def test_config_has_openai_defaults():
    config = MemoriaConfig()

    assert config.llm_provider == "openai"
    assert config.llm_model == "gpt-5.1"
    assert config.reasoning_summary == "auto"
    assert config.api_key_env == "OPENAI_API_KEY"
    assert config.openai_base_url is None
    assert config.store_llm_transcripts is True
    assert config.transcript_retention_days is None
    assert config.sleep_default_limit == 20
    assert config.max_tool_rounds == 8
    assert config.max_patch_operations == 50
    assert config.backup_after_sleep is True
