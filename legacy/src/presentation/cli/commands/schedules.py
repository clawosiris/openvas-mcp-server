# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""CLI commands for schedule management."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from src.infrastructure import ConfigLoader, create_client
from src.services.schedules import ScheduleService

app = typer.Typer(help="Manage schedules")
console = Console()


def _get_service() -> ScheduleService:
    config = ConfigLoader.from_env_and_file()
    client = create_client(config)
    return ScheduleService(client)


@app.command("list")
def list_schedules(
    filter: Annotated[str, typer.Option("--filter", "-f", help="GMP filter string")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    service = _get_service()
    result = service.list(filter)

    if json_output:
        rprint(json.dumps(result.model_dump(), indent=2, default=str))
        return

    table = Table(title="Schedules")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("First Time")
    table.add_column("Timezone")

    for schedule in result.schedules:
        table.add_row(
            schedule.id[:8] + "...",
            schedule.name,
            str(schedule.first_time) if schedule.first_time else "-",
            schedule.timezone,
        )

    console.print(table)


@app.command("get")
def get_schedule(
    schedule_id: Annotated[str, typer.Argument(help="Schedule UUID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    service = _get_service()
    schedule = service.get(schedule_id)

    if json_output:
        rprint(json.dumps(schedule.model_dump(), indent=2, default=str))
        return

    console.print(f"[bold cyan]{schedule.name}[/bold cyan]")
    console.print(f"[dim]ID: {schedule.id}[/dim]")
    console.print(f"First run: {schedule.first_time}")
    console.print(
        f"Every: {schedule.period_months}m {schedule.period_days}d {schedule.period_hours}h {schedule.period_minutes}min"
    )
    console.print(f"Timezone: {schedule.timezone}")
