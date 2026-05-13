from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from memoria.application.services.ingest_service import IngestRequest, IngestService
from memoria.config import load_config
from memoria.infrastructure.db.session import create_engine_for_path, create_session_factory, init_db
from memoria.interfaces.cli.output import print_result

app = typer.Typer()


def _session_factory():
    config = load_config()
    engine = create_engine_for_path(config.db_path)
    init_db(engine)
    return create_session_factory(engine)


def _ingest_content(content, source, title, tags, hint, project_path):
    service = IngestService(_session_factory())
    raw_entry_id = service.ingest(
        IngestRequest(
            content=content,
            source=source,
            title=title,
            tags=list(tags),
            hint=hint,
            project_path=project_path,
        )
    )
    print_result({"raw_entry_id": raw_entry_id})


@app.command("text")
def ingest_text(
    content: str,
    title: Optional[str] = typer.Option(None, "--title"),
    tag: list[str] = typer.Option([], "--tag"),
    hint: Optional[str] = typer.Option(None, "--hint"),
    project_path: Optional[str] = typer.Option(None, "--project-path"),
):
    _ingest_content(content, "text", title, tag, hint, project_path)


@app.command("file")
def ingest_file(
    path: Path,
    title: Optional[str] = typer.Option(None, "--title"),
    tag: list[str] = typer.Option([], "--tag"),
    hint: Optional[str] = typer.Option(None, "--hint"),
    project_path: Optional[str] = typer.Option(None, "--project-path"),
):
    _ingest_content(path.read_text(encoding="utf-8"), "file", title, tag, hint, project_path)


@app.command("stdin")
def ingest_stdin(
    title: Optional[str] = typer.Option(None, "--title"),
    tag: list[str] = typer.Option([], "--tag"),
    hint: Optional[str] = typer.Option(None, "--hint"),
    project_path: Optional[str] = typer.Option(None, "--project-path"),
):
    _ingest_content(typer.get_text_stream("stdin").read(), "stdin", title, tag, hint, project_path)
