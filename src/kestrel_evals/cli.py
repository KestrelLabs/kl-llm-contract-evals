from __future__ import annotations

import asyncio
import json
from pathlib import Path

import typer

from .providers.openai_provider import OpenAIProvider
from .runner import run_suite
from .suite_loader import load_suite

app = typer.Typer(no_args_is_help=True)


@app.command()
def version():
    """Print version."""
    from . import __version__

    typer.echo(__version__)


@app.command()
def run(
    suite_path: str = typer.Argument(..., help="Path to suite YAML"),
    model: str = typer.Option("gpt-4.1-mini", help="Model name"),
    out: str = typer.Option("-", help="Write report JSON to file (or '-' for stdout)"),
):
    """Run an eval suite."""

    suite = load_suite(suite_path)
    provider = OpenAIProvider()

    report = asyncio.run(run_suite(suite=suite, provider=provider, model=model))

    payload = json.dumps(report, indent=2)
    if out == "-":
        typer.echo(payload)
    else:
        p = Path(out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(payload, encoding="utf-8")
        typer.echo(f"Wrote report: {p}")

    if report["summary"]["failed"] > 0:
        raise typer.Exit(code=1)
