from __future__ import annotations

import json
import sqlite3
import shutil
import subprocess
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


class BackupService:
    def __init__(self, db_path: Path, jobs_dir: Path, backup_repo: Path) -> None:
        self.db_path = db_path
        self.jobs_dir = jobs_dir
        self.backup_repo = backup_repo

    def create_archive(self, archive_path: Path) -> Path:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {"created_at": datetime.now(timezone.utc).isoformat()}

        with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            if self.db_path.exists():
                with tempfile.NamedTemporaryFile() as snapshot:
                    self._snapshot_db(Path(snapshot.name))
                    archive.write(snapshot.name, "memoria.db")
            if self.jobs_dir.exists():
                for job_path in self.jobs_dir.rglob("*"):
                    if job_path.is_file():
                        archive.write(job_path, Path("jobs") / job_path.relative_to(self.jobs_dir))
            archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))

        return archive_path

    def restore_archive(self, archive_path: Path, restore_dir: Path) -> Path:
        restore_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(archive_path, "r") as archive:
            for member in archive.infolist():
                target = self._safe_restore_target(restore_dir, member.filename)
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(member) as source, target.open("wb") as destination:
                    shutil.copyfileobj(source, destination)
        return restore_dir / "memoria.db"

    def restore_to_configured_paths(self, archive_path: Path) -> Path:
        with tempfile.TemporaryDirectory() as temp_dir:
            extracted_db = self.restore_archive(archive_path, Path(temp_dir))
            if extracted_db.exists():
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(extracted_db, self.db_path)
            extracted_jobs = Path(temp_dir) / "jobs"
            if self.jobs_dir.exists():
                shutil.rmtree(self.jobs_dir)
            if extracted_jobs.exists():
                shutil.copytree(extracted_jobs, self.jobs_dir)
            else:
                self.jobs_dir.mkdir(parents=True, exist_ok=True)
        return self.db_path

    def create_git_backup(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        snapshot_dir = self.backup_repo / "snapshots" / timestamp
        snapshot_dir.mkdir(parents=True, exist_ok=True)

        if self.db_path.exists():
            self._snapshot_db(snapshot_dir / "memoria.db")
        if self.jobs_dir.exists():
            shutil.copytree(self.jobs_dir, snapshot_dir / "jobs")

        manifest = {"created_at": datetime.now(timezone.utc).isoformat()}
        (snapshot_dir / "manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        self.backup_repo.mkdir(parents=True, exist_ok=True)
        if not (self.backup_repo / ".git").exists():
            self._git("init")

        self._git("config", "user.name", "Memoria Backup")
        self._git("config", "user.email", "memoria-backup@example.invalid")
        self._git("add", ".")
        self._git("commit", "-m", f"memoria backup {timestamp}")
        return self._git("rev-parse", "HEAD")

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self.backup_repo,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()

    def _snapshot_db(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as source:
            with sqlite3.connect(destination) as target:
                source.backup(target)

    @staticmethod
    def _safe_restore_target(restore_dir: Path, member_name: str) -> Path:
        if member_name.startswith("/") or Path(member_name).is_absolute():
            raise ValueError(f"unsafe archive member {member_name}")
        target = (restore_dir / member_name).resolve()
        root = restore_dir.resolve()
        if root != target and root not in target.parents:
            raise ValueError(f"unsafe archive member {member_name}")
        return target
