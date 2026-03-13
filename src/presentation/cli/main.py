"""CLI entry point."""

import typer

from .commands import (
    assets,
    compliance,
    notes,
    overrides,
    port_lists,
    reports,
    scan_configs,
    schedules,
    system,
    targets,
    tasks,
    tickets,
    vulns,
)

app = typer.Typer(
    name="openvas",
    help="OpenVAS CLI for Greenbone Vulnerability Management",
    no_args_is_help=True,
)

# Register command groups
app.add_typer(system.app, name="system")
app.add_typer(targets.app, name="target")
app.add_typer(tasks.app, name="task")
app.add_typer(reports.app, name="report")
app.add_typer(scan_configs.app, name="scan-config")
app.add_typer(port_lists.app, name="port-list")
app.add_typer(schedules.app, name="schedule")
app.add_typer(vulns.app, name="vuln")
app.add_typer(notes.app, name="note")
app.add_typer(overrides.app, name="override")
app.add_typer(tickets.app, name="ticket")
app.add_typer(assets.app, name="asset")
app.add_typer(compliance.app, name="compliance")


@app.command()
def version() -> None:
    """Show version information."""
    from src import __version__

    typer.echo(f"openvas-mcp {__version__}")


if __name__ == "__main__":
    app()
