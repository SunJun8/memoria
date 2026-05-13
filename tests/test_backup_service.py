import json
import zipfile
from pathlib import Path

from sqlalchemy import select
from typer.testing import CliRunner

from memoria.application.services.backup_service import BackupService
from memoria.application.services.ingest_service import IngestRequest, IngestService
from memoria.infrastructure.db.models import RawEntry
from memoria.infrastructure.db.session import create_engine_for_path, create_session_factory, init_db
from memoria.interfaces.cli.app import app


def test_backup_create_and_restore_archive(tmp_path):
    db_path = tmp_path / "test.db"
    engine = create_engine_for_path(db_path)
    init_db(engine)
    session_factory = create_session_factory(engine)
    IngestService(session_factory).ingest(IngestRequest(content="backup me", source="text"))
    jobs_dir = tmp_path / "jobs"
    jobs_dir.mkdir()
    (jobs_dir / "job-1.jsonl").write_text('{"type":"test"}\n', encoding="utf-8")
    archive_path = tmp_path / "backup.zip"
    restore_dir = tmp_path / "restore"

    service = BackupService(db_path=db_path, jobs_dir=jobs_dir, backup_repo=tmp_path / "git")
    created = service.create_archive(archive_path)
    restored_db = service.restore_archive(created, restore_dir)

    assert created.exists()
    assert restored_db.exists()
    restored_engine = create_engine_for_path(restored_db)
    restored_session_factory = create_session_factory(restored_engine)
    with restored_session_factory() as session:
        raw = session.scalars(select(RawEntry)).one()
    assert raw.content == "backup me"
    assert (restore_dir / "jobs" / "job-1.jsonl").read_text(encoding="utf-8") == '{"type":"test"}\n'


def test_backup_restore_rejects_path_traversal(tmp_path):
    archive_path = tmp_path / "bad.zip"
    outside = tmp_path / "outside.txt"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../outside.txt", "bad")

    service = BackupService(db_path=tmp_path / "db", jobs_dir=tmp_path / "jobs", backup_repo=tmp_path / "git")

    try:
        service.restore_archive(archive_path, tmp_path / "restore")
    except ValueError as exc:
        assert "unsafe" in str(exc)
    else:
        raise AssertionError("expected ValueError")

    assert not outside.exists()


def test_backup_create_git_commit(tmp_path):
    db_path = tmp_path / "memoria.db"
    engine = create_engine_for_path(db_path)
    init_db(engine)
    repo = tmp_path / "backup-git"

    service = BackupService(db_path=db_path, jobs_dir=tmp_path / "jobs", backup_repo=repo)
    commit = service.create_git_backup()
    second_commit = service.create_git_backup()

    assert commit
    assert second_commit
    assert second_commit != commit
    assert (repo / ".git").exists()


def test_backup_cli_create_and_restore_use_config_paths(monkeypatch, tmp_path):
    db_path = tmp_path / "dbdir" / "memoria.db"
    jobs_dir = tmp_path / "custom-jobs"
    backup_repo = tmp_path / "git"
    monkeypatch.setenv("MEMORIA_DB_PATH", str(db_path))
    monkeypatch.setenv("MEMORIA_JOBS_DIR", str(jobs_dir))
    monkeypatch.setenv("MEMORIA_BACKUP_GIT_REPO", str(backup_repo))
    runner = CliRunner()

    ingest_result = runner.invoke(app, ["ingest", "text", "backup cli"])
    assert ingest_result.exit_code == 0
    archive_path = tmp_path / "cli.zip"
    create_result = runner.invoke(app, ["backup", "create", str(archive_path)])
    assert create_result.exit_code == 0
    assert json.loads(create_result.stdout)["archive"] == str(archive_path)
    jobs_dir.mkdir(exist_ok=True)
    (jobs_dir / "job.jsonl").write_text('{"type":"job"}\n', encoding="utf-8")
    create_result = runner.invoke(app, ["backup", "create", str(archive_path)])
    assert create_result.exit_code == 0

    db_path.unlink()
    for path in jobs_dir.iterdir():
        path.unlink()
    restore_result = runner.invoke(app, ["backup", "restore", str(archive_path)])

    assert restore_result.exit_code == 0
    assert json.loads(restore_result.stdout)["restored_db"] == str(db_path)
    assert (jobs_dir / "job.jsonl").read_text(encoding="utf-8") == '{"type":"job"}\n'
    engine = create_engine_for_path(db_path)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        raw = session.scalars(select(RawEntry)).one()
    assert raw.content == "backup cli"


def test_backup_restore_to_configured_paths_clears_jobs_when_snapshot_has_none(tmp_path):
    db_path = tmp_path / "memoria.db"
    engine = create_engine_for_path(db_path)
    init_db(engine)
    jobs_dir = tmp_path / "jobs"
    archive_path = tmp_path / "empty-jobs.zip"
    service = BackupService(db_path=db_path, jobs_dir=jobs_dir, backup_repo=tmp_path / "git")
    service.create_archive(archive_path)
    jobs_dir.mkdir()
    (jobs_dir / "stale.jsonl").write_text("stale\n", encoding="utf-8")

    service.restore_to_configured_paths(archive_path)

    assert jobs_dir.exists()
    assert list(jobs_dir.iterdir()) == []
