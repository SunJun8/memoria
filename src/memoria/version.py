from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass

from memoria import __version__


@dataclass(frozen=True)
class VersionInfo:
    version: str
    build_time: str
    python: str
    platform: str


def get_version_info() -> VersionInfo:
    build_time = os.environ.get("MEMORIA_BUILD_TIME")
    return VersionInfo(
        version=_package_version(),
        build_time=build_time if build_time is not None else _build_time(),
        python=sys.version.split()[0],
        platform=platform.platform(),
    )


def format_version_info(info: VersionInfo | None = None) -> str:
    info = info or get_version_info()
    return "\n".join(
        [
            f"Memoria {info.version}",
            f"Build time: {info.build_time}",
            f"Python: {info.python}",
            f"Platform: {info.platform}",
        ]
    )


def _package_version() -> str:
    return __version__


def _build_time() -> str:
    try:
        from memoria.build_info import BUILD_TIME
    except ModuleNotFoundError as exc:
        if exc.name != "memoria.build_info":
            raise
        return "unknown"
    return BUILD_TIME
