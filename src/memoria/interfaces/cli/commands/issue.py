from __future__ import annotations

from typing import Optional

import typer

from memoria.application.services.query_service import QueryService
from memoria.config import load_config
from memoria.infrastructure.db.session import create_engine_for_path, create_session_factory, init_db
from memoria.interfaces.cli.output import print_result

app = typer.Typer()


def _query_service():
    config = load_config()
    engine = create_engine_for_path(config.db_path)
    init_db(engine)
    return QueryService(create_session_factory(engine))


@app.command("list")
def list_issues(
    status: Optional[str] = typer.Option(None, "--status"),
    json_output: bool = typer.Option(False, "--json"),
):
    print_result(_query_service().list_issues(status=status), as_json=json_output)


@app.command("show")
def show_issue(issue_id: int, json_output: bool = typer.Option(False, "--json")):
    result = _query_service().get_issue(issue_id)
    if result is None:
        raise typer.Exit(1)
    print_result(result, as_json=json_output)


@app.command("search")
def search_issues(query: str, json_output: bool = typer.Option(False, "--json")):
    print_result(_query_service().search_issues(query), as_json=json_output)
