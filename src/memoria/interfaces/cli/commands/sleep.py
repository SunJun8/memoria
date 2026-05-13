from __future__ import annotations

import os
from typing import Optional

import typer

from memoria.application.services.backup_service import BackupService
from memoria.application.services.patch_service import PatchService
from memoria.application.services.query_service import QueryService
from memoria.application.services.sleep_service import SleepService
from memoria.config import load_config
from memoria.infrastructure.db.session import create_engine_for_path, create_session_factory, init_db
from memoria.infrastructure.llm.mock_provider import MockLLMProvider
from memoria.infrastructure.llm.openai_provider import OpenAIProvider
from memoria.infrastructure.transcript.jsonl_store import JsonlTranscriptStore
from memoria.interfaces.cli.output import print_result

app = typer.Typer(invoke_without_command=True)


def _session_factory(config):
    engine = create_engine_for_path(config.db_path)
    init_db(engine)
    return create_session_factory(engine)


def _query_service(config):
    return QueryService(_session_factory(config))


@app.callback(invoke_without_command=True)
def run_sleep(
    ctx: typer.Context,
    mock: bool = typer.Option(False, "--mock"),
    limit: Optional[int] = typer.Option(None, "--limit"),
    strictness: str = typer.Option("balanced", "--strictness"),
):
    if ctx.invoked_subcommand is not None:
        return

    config = load_config()
    provider = MockLLMProvider()
    model = "mock-model"
    reasoning_effort = config.reasoning_effort

    if not mock:
        model = config.llm_model
        api_key = os.environ.get(config.api_key_env)
        if not api_key:
            typer.echo(f"{config.api_key_env} is required unless --mock is used.", err=True)
            raise typer.Exit(1)
        provider = OpenAIProvider(
            model=model,
            reasoning_effort=reasoning_effort,
            reasoning_summary=config.reasoning_summary,
            api_key=api_key,
            base_url=config.openai_base_url,
            max_tool_rounds=config.max_tool_rounds,
        )

    session_factory = _session_factory(config)
    after_success_hook = None
    if config.backup_after_sleep:
        backup_service = BackupService(
            db_path=config.db_path,
            jobs_dir=config.jobs_dir,
            backup_repo=config.backup_git_repo,
        )
        after_success_hook = backup_service.create_git_backup
    service = SleepService(
        session_factory=session_factory,
        query_service=QueryService(session_factory),
        patch_service=PatchService(session_factory),
        llm_provider=provider,
        transcript_store=JsonlTranscriptStore(config.jobs_dir),
        model=model,
        reasoning_effort=reasoning_effort,
        after_success_hook=after_success_hook,
    )
    job_id = service.run(limit=limit or config.sleep_default_limit, strictness=strictness)
    print_result({"job_id": job_id})


@app.command("list")
def list_sleep(json_output: bool = typer.Option(False, "--json")):
    config = load_config()
    print_result(_query_service(config).list_sleep_jobs(), as_json=json_output)


@app.command("show")
def show_sleep(job_id: int, json_output: bool = typer.Option(False, "--json")):
    config = load_config()
    job = _query_service(config).get_sleep_job(job_id)
    if job is None:
        raise typer.BadParameter(f"missing sleep job {job_id}")
    print_result(job, as_json=json_output)
