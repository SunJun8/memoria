from __future__ import annotations

import json

import typer


def print_result(data, as_json=True):
    if as_json:
        typer.echo(json.dumps(data, ensure_ascii=False, default=str))
        return

    typer.echo(data)
