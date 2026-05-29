"""Command-line interface for the Urban Carbon Sink pipeline."""

from __future__ import annotations

import typer

from casa import __version__

app = typer.Typer(
    help="CASA-based monthly CO2 absorption pipeline for urban vegetation.",
    add_completion=False,
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Print the package version."""
    typer.echo(f"casa {__version__}")


@app.command()
def run(
    region: str = typer.Option(..., "--region", "-r", help="Region key, e.g. 'oeiras'."),
    month: str = typer.Option(..., "--month", "-m", help="Month in YYYY-MM format."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Resolve inputs and exit without computing."),
) -> None:
    """Run the CASA pipeline for a single region and month."""
    typer.echo(f"[stub] casa run region={region} month={month} dry_run={dry_run}")
    raise typer.Exit(code=0)


@app.command("list-regions")
def list_regions() -> None:
    """List configured regions from config/regions/*.yml."""
    typer.echo("[stub] no regions configured yet.")


if __name__ == "__main__":
    app()
