from __future__ import annotations

import typer

from memoria.interfaces.cli.commands import backup, chain, ingest, issue, patch, proposed, sleep

app = typer.Typer()
app.add_typer(ingest.app, name="ingest")
app.add_typer(issue.app, name="issue")
app.add_typer(chain.app, name="chain")
app.add_typer(proposed.app, name="proposed")
app.add_typer(patch.app, name="patch")
app.add_typer(sleep.app, name="sleep")
app.add_typer(backup.app, name="backup")
