from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from memoria.application.services.backup_service import BackupService
from memoria.config import load_config
from memoria.interfaces.cli.output import print_result

app = typer.Typer()


def _service() -> BackupService:
    config = load_config()
    return BackupService(
        db_path=config.db_path,
        jobs_dir=config.jobs_dir,
        backup_repo=config.backup_git_repo,
    )


@app.command("create")
def create_backup(
    path: Optional[Path] = typer.Argument(None),
    git: bool = typer.Option(False, "--git"),
):
    config = load_config()
    service = _service()

    if git:
        commit = service.create_git_backup()
        print_result({"commit": commit})
        return

    archive_path = path or config.db_path.parent / "memoria-backup.zip"
    archive = service.create_archive(archive_path)
    print_result({"archive": archive})


@app.command("restore")
def restore_backup(archive: Path, restore_dir: Optional[Path] = typer.Argument(None)):
    service = _service()
    restored_db = (
        service.restore_archive(archive, restore_dir)
        if restore_dir is not None
        else service.restore_to_configured_paths(archive)
    )
    print_result({"restored_db": restored_db})
