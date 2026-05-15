from __future__ import annotations

import typer

from memoria.interfaces.cli.commands import backup, chain, ingest, issue, patch, proposed, sleep
from memoria.version import format_version_info


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(format_version_info())
        raise typer.Exit()


app = typer.Typer()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and build information.",
    ),
) -> None:
    pass


app.add_typer(ingest.app, name="ingest")
app.add_typer(issue.app, name="issue")
app.add_typer(chain.app, name="chain")
app.add_typer(proposed.app, name="proposed")
app.add_typer(patch.app, name="patch")
app.add_typer(sleep.app, name="sleep")
app.add_typer(backup.app, name="backup")
