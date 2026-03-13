"""CLI entry point."""

import typer

from .commands import system, targets

app = typer.Typer(
    name="openvas",
    help="OpenVAS CLI for Greenbone Vulnerability Management",
    no_args_is_help=True,
)

# Register command groups
app.add_typer(system.app, name="system")
app.add_typer(targets.app, name="target")


@app.command()
def version() -> None:
    """Show version information."""
    from src import __version__

    typer.echo(f"openvas-mcp {__version__}")


if __name__ == "__main__":
    app()
