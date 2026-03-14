# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""CLI commands for target management."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from src.infrastructure import ConfigLoader, create_client
from src.services.targets import (
    AliveTest,
    TargetCreateRequest,
    TargetService,
    TargetUpdateRequest,
)

app = typer.Typer(help="Manage scan targets")
console = Console()


def _get_service() -> TargetService:
    """Get configured target service."""
    config = ConfigLoader.from_env_and_file()
    client = create_client(config)
    return TargetService(client)


@app.command("list")
def list_targets(
    filter: Annotated[str, typer.Option("--filter", "-f", help="GMP filter string")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """List scan targets."""
    service = _get_service()
    result = service.list(filter)

    if json_output:
        rprint(json.dumps(result.model_dump(), indent=2, default=str))
        return

    if not result.targets:
        console.print("[yellow]No targets found.[/yellow]")
        return

    table = Table(title="Targets")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Hosts", style="white")
    table.add_column("In Use", style="yellow")

    for target in result.targets:
        hosts_display = ", ".join(target.hosts[:3])
        if len(target.hosts) > 3:
            hosts_display += f" (+{len(target.hosts) - 3} more)"

        table.add_row(
            target.id[:8] + "...",
            target.name,
            hosts_display,
            "✓" if target.in_use else "",
        )

    console.print(table)
    console.print(f"\n[dim]Total: {result.total} | Shown: {result.filtered}[/dim]")


@app.command("get")
def get_target(
    target_id: Annotated[str, typer.Argument(help="Target UUID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """Get target details."""
    service = _get_service()
    target = service.get(target_id)

    if json_output:
        rprint(json.dumps(target.model_dump(), indent=2, default=str))
        return

    console.print(f"\n[bold cyan]Target: {target.name}[/bold cyan]")
    console.print(f"[dim]ID: {target.id}[/dim]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="yellow")
    table.add_column("Value")

    table.add_row("Hosts", ", ".join(target.hosts))
    if target.exclude_hosts:
        table.add_row("Exclude", ", ".join(target.exclude_hosts))
    table.add_row("Alive Test", target.alive_test.value)
    if target.port_list:
        table.add_row("Port List", f"{target.port_list.name} ({target.port_list.id[:8]}...)")
    if target.comment:
        table.add_row("Comment", target.comment)
    table.add_row("In Use", "Yes" if target.in_use else "No")
    if target.creation_time:
        table.add_row("Created", str(target.creation_time))

    console.print(table)


@app.command("create")
def create_target(
    name: Annotated[str, typer.Option("--name", "-n", help="Target name")],
    hosts: Annotated[list[str], typer.Option("--host", "-H", help="Host (can be repeated)")],
    comment: Annotated[str, typer.Option("--comment", "-c", help="Optional comment")] = "",
    exclude: Annotated[
        list[str] | None, typer.Option("--exclude", "-x", help="Exclude host")
    ] = None,
    alive_test: Annotated[
        str, typer.Option("--alive-test", help="Alive test method")
    ] = "Scan Config Default",
    port_list: Annotated[str | None, typer.Option("--port-list", help="Port list UUID")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    quiet: Annotated[bool, typer.Option("-q", "--quiet", help="Only output target ID")] = False,
) -> None:
    """Create a new target."""
    service = _get_service()

    # Parse alive test
    try:
        alive_test_enum = AliveTest(alive_test)
    except ValueError:
        alive_test_enum = AliveTest.SCAN_CONFIG_DEFAULT

    request = TargetCreateRequest(
        name=name,
        hosts=hosts,
        comment=comment,
        exclude_hosts=exclude or [],
        alive_test=alive_test_enum,
        port_list_id=port_list,
    )

    target = service.create(request)

    if quiet:
        print(target.id)
        return

    if json_output:
        rprint(json.dumps(target.model_dump(), indent=2, default=str))
        return

    console.print(f"[green]✓ Created target:[/green] {target.name}")
    console.print(f"[dim]ID: {target.id}[/dim]")


@app.command("delete")
def delete_target(
    target_id: Annotated[str, typer.Argument(help="Target UUID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
    ultimate: Annotated[
        bool, typer.Option("--ultimate", help="Permanently delete (skip trash)")
    ] = False,
) -> None:
    """Delete a target."""
    service = _get_service()

    if not force:
        # Get target name for confirmation
        target = service.get(target_id)
        confirm = typer.confirm(f"Delete target '{target.name}'?")
        if not confirm:
            raise typer.Abort()

    service.delete(target_id, ultimate=ultimate)
    console.print(f"[green]✓ Deleted target:[/green] {target_id}")


@app.command("clone")
def clone_target(
    target_id: Annotated[str, typer.Argument(help="Target UUID to clone")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    quiet: Annotated[bool, typer.Option("-q", "--quiet", help="Only output new target ID")] = False,
) -> None:
    """Clone a target."""
    service = _get_service()
    target = service.clone(target_id)

    if quiet:
        print(target.id)
        return

    if json_output:
        rprint(json.dumps(target.model_dump(), indent=2, default=str))
        return

    console.print(f"[green]✓ Cloned target:[/green] {target.name}")
    console.print(f"[dim]New ID: {target.id}[/dim]")


@app.command("update")
def update_target(
    target_id: Annotated[str, typer.Argument(help="Target UUID")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="New name")] = None,
    hosts: Annotated[list[str] | None, typer.Option("--host", "-H", help="New hosts")] = None,
    comment: Annotated[str | None, typer.Option("--comment", "-c", help="New comment")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """Update a target."""
    service = _get_service()

    request = TargetUpdateRequest(
        name=name,
        hosts=hosts,
        comment=comment,
    )

    target = service.update(target_id, request)

    if json_output:
        rprint(json.dumps(target.model_dump(), indent=2, default=str))
        return

    console.print(f"[green]✓ Updated target:[/green] {target.name}")
