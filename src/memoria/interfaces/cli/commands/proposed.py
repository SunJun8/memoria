from __future__ import annotations

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
def list_proposed(json_output: bool = typer.Option(False, "--json")):
    print_result(_query_service().list_proposals(), as_json=json_output)


@app.command("accept")
def accept_proposed(proposal_id: int, json_output: bool = typer.Option(False, "--json")):
    print_result(_query_service().resolve_proposal(proposal_id, "accepted"), as_json=json_output)


@app.command("reject")
def reject_proposed(proposal_id: int, json_output: bool = typer.Option(False, "--json")):
    print_result(_query_service().resolve_proposal(proposal_id, "rejected"), as_json=json_output)
