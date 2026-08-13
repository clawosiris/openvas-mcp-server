# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""CLI commands for scan config management."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from src.infrastructure import ConfigLoader, create_client
from src.services.scan_configs import ScanConfigService

app = typer.Typer(help="Manage scan configurations")
console = Console()


def _get_service() -> ScanConfigService:
    config = ConfigLoader.from_env_and_file()
    client = create_client(config)
    return ScanConfigService(client)


@app.command("list")
def list_scan_configs(
    filter: Annotated[str, typer.Option("--filter", "-f", help="GMP filter string")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    service = _get_service()
    result = service.list(filter)

    if json_output:
        rprint(json.dumps(result.model_dump(), indent=2, default=str))
        return

    table = Table(title="Scan Configurations")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Families", justify="right")
    table.add_column("NVTs", justify="right")

    for config in result.scan_configs:
        table.add_row(
            config.id[:8] + "...",
            config.name,
            str(config.family_count),
            str(config.nvt_count),
        )

    console.print(table)


@app.command("get")
def get_scan_config(
    config_id: Annotated[str, typer.Argument(help="Scan config UUID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    service = _get_service()
    config = service.get(config_id)

    if json_output:
        rprint(json.dumps(config.model_dump(), indent=2, default=str))
        return

    console.print(f"[bold cyan]{config.name}[/bold cyan]")
    console.print(f"[dim]ID: {config.id}[/dim]")
    console.print(f"Families: {config.family_count}")
    console.print(f"NVTs: {config.nvt_count}")
