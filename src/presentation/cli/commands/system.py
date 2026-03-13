"""CLI commands for system operations."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console

from src.infrastructure import ConfigLoader, create_client
from src.services.system import SystemService

app = typer.Typer(help="System operations")
console = Console()


def _get_service() -> SystemService:
    """Get configured system service."""
    config = ConfigLoader.from_env_and_file()
    client = create_client(config)
    return SystemService(client)


@app.command("version")
def get_version(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """Show GVM version information."""
    service = _get_service()
    version = service.get_version()

    if json_output:
        rprint(json.dumps(version.model_dump(), indent=2))
        return

    console.print("[bold cyan]GVM Version Information[/bold cyan]")
    console.print(f"GMP Protocol: {version.gmp_version}")
    if version.backend_version:
        console.print(f"Backend: {version.backend_name} {version.backend_version}")


@app.command("test")
def test_connection() -> None:
    """Test connection to GVM server."""
    try:
        service = _get_service()
        version = service.get_version()
        console.print(f"[green]✓ Connected to GVM[/green] (GMP {version.gmp_version})")
    except Exception as e:
        console.print(f"[red]✗ Connection failed:[/red] {e}")
        raise typer.Exit(1) from e
