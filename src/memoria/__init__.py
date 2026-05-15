from __future__ import annotations

from importlib import metadata
from pathlib import Path
import tomllib

_DISTRIBUTION_NAME = "memoria-cli"


def _read_project_version() -> str:
    pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        with pyproject_path.open("rb") as fh:
            return tomllib.load(fh)["project"]["version"]
    except (FileNotFoundError, KeyError):
        return "0+unknown"


try:
    __version__ = metadata.version(_DISTRIBUTION_NAME)
except metadata.PackageNotFoundError:
    __version__ = _read_project_version()
