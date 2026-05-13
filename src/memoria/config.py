from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _xdg_path(env_name: str, fallback: Path) -> Path:
    value = os.environ.get(env_name)
    return Path(value).expanduser() if value else fallback


def _env_path(env_name: str, fallback: Path) -> Path:
    value = os.environ.get(env_name)
    return Path(value).expanduser() if value else fallback


def _config_path() -> Path:
    return _xdg_path("XDG_CONFIG_HOME", Path.home() / ".config") / "memoria" / "config.toml"


def _data_home() -> Path:
    return _xdg_path("XDG_DATA_HOME", Path.home() / ".local" / "share") / "memoria"


def _state_home() -> Path:
    return _xdg_path("XDG_STATE_HOME", Path.home() / ".local" / "state") / "memoria"


@dataclass(frozen=True)
class MemoriaConfig:
    config_path: Path = field(default_factory=_config_path)
    db_path: Path = field(default_factory=lambda: _data_home() / "memoria.db")
    jobs_dir: Path = field(default_factory=lambda: _data_home() / "jobs")
    backup_git_repo: Path = field(default_factory=lambda: _data_home() / "backups" / "git")
    logs_dir: Path = field(default_factory=lambda: _state_home() / "logs")
    llm_provider: str = "openai"
    llm_model: str = "gpt-5.1"
    reasoning_effort: str = "medium"
    reasoning_summary: str = "auto"
    api_key_env: str = "OPENAI_API_KEY"
    openai_base_url: str | None = None
    store_llm_transcripts: bool = True
    transcript_retention_days: int | None = None
    sleep_default_limit: int = 20
    max_tool_rounds: int = 8
    max_patch_operations: int = 50
    backup_after_sleep: bool = True


def load_config() -> MemoriaConfig:
    config_path = _env_path("MEMORIA_CONFIG", _config_path())
    db_path = _env_path("MEMORIA_DB_PATH", _data_home() / "memoria.db")
    jobs_dir = _env_path("MEMORIA_JOBS_DIR", _data_home() / "jobs")
    backup_git_repo = _env_path("MEMORIA_BACKUP_GIT_REPO", _data_home() / "backups" / "git")
    llm_model = os.environ.get("MEMORIA_LLM_MODEL", "gpt-5.1")
    reasoning_summary = os.environ.get("MEMORIA_REASONING_SUMMARY", "auto")

    return MemoriaConfig(
        config_path=config_path,
        db_path=db_path,
        jobs_dir=jobs_dir,
        backup_git_repo=backup_git_repo,
        logs_dir=_state_home() / "logs",
        llm_model=llm_model,
        reasoning_summary=reasoning_summary,
    )
