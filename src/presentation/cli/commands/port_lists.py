"""CLI commands for port list management."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from src.infrastructure import ConfigLoader, create_client
from src.services.port_lists import PortListService

app = typer.Typer(help="Manage port lists")
console = Console()


def _get_service() -> PortListService:
    config = ConfigLoader.from_env_and_file()
    client = create_client(config)
    return PortListService(client)


@app.command("list")
def list_port_lists(
    filter: Annotated[str, typer.Option("--filter", "-f", help="GMP filter string")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    service = _get_service()
    result = service.list(filter)

    if json_output:
        rprint(json.dumps(result.model_dump(), indent=2, default=str))
        return

    table = Table(title="Port Lists")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Ports", justify="right")

    for port_list in result.port_lists:
        table.add_row(
            port_list.id[:8] + "...",
            port_list.name,
            str(port_list.port_count),
        )

    console.print(table)


@app.command("get")
def get_port_list(
    port_list_id: Annotated[str, typer.Argument(help="Port list UUID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    service = _get_service()
    port_list = service.get(port_list_id)

    if json_output:
        rprint(json.dumps(port_list.model_dump(), indent=2, default=str))
        return

    console.print(f"[bold cyan]{port_list.name}[/bold cyan]")
    console.print(f"[dim]ID: {port_list.id}[/dim]")
    console.print(f"Ports: {port_list.port_count}")
