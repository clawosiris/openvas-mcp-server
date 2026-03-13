"""CLI commands for task (scan) management."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from src.infrastructure import ConfigLoader, create_client
from src.services.tasks import TaskCreateRequest, TaskService, TaskStatus

app = typer.Typer(help="Manage scan tasks")
console = Console()


def _get_service() -> TaskService:
    """Get configured task service."""
    config = ConfigLoader.from_env_and_file()
    client = create_client(config)
    return TaskService(client)


def _status_color(status: TaskStatus) -> str:
    """Get color for status display."""
    colors = {
        TaskStatus.RUNNING: "green",
        TaskStatus.DONE: "cyan",
        TaskStatus.STOPPED: "yellow",
        TaskStatus.NEW: "white",
        TaskStatus.REQUESTED: "blue",
        TaskStatus.INTERRUPTED: "red",
    }
    return colors.get(status, "white")


@app.command("list")
def list_tasks(
    filter: Annotated[str, typer.Option("--filter", "-f", help="GMP filter string")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """List scan tasks."""
    service = _get_service()
    result = service.list(filter)

    if json_output:
        rprint(json.dumps(result.model_dump(), indent=2, default=str))
        return

    if not result.tasks:
        console.print("[yellow]No tasks found.[/yellow]")
        return

    table = Table(title="Scan Tasks")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Status")
    table.add_column("Progress", justify="right")
    table.add_column("Target")

    for task in result.tasks:
        status_str = (
            f"[{_status_color(task.status)}]{task.status.value}[/{_status_color(task.status)}]"
        )
        progress_str = f"{task.progress}%" if task.status == TaskStatus.RUNNING else "-"
        target_name = task.target.name if task.target else "-"

        table.add_row(
            task.id[:8] + "...",
            task.name,
            status_str,
            progress_str,
            target_name,
        )

    console.print(table)
    console.print(f"\n[dim]Total: {result.total} | Shown: {result.filtered}[/dim]")


@app.command("get")
def get_task(
    task_id: Annotated[str, typer.Argument(help="Task UUID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """Get task details."""
    service = _get_service()
    task = service.get(task_id)

    if json_output:
        rprint(json.dumps(task.model_dump(), indent=2, default=str))
        return

    console.print(f"\n[bold cyan]Task: {task.name}[/bold cyan]")
    console.print(f"[dim]ID: {task.id}[/dim]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="yellow")
    table.add_column("Value")

    status_str = f"[{_status_color(task.status)}]{task.status.value}[/{_status_color(task.status)}]"
    table.add_row("Status", status_str)

    if task.status == TaskStatus.RUNNING:
        table.add_row("Progress", f"{task.progress}%")

    if task.target:
        table.add_row("Target", f"{task.target.name} ({task.target.id[:8]}...)")
    if task.config:
        table.add_row("Config", f"{task.config.name}")
    if task.scanner:
        table.add_row("Scanner", f"{task.scanner.name}")
    if task.last_report:
        table.add_row("Last Report", f"{task.last_report.id[:8]}...")
    table.add_row("Reports", str(task.report_count))
    if task.comment:
        table.add_row("Comment", task.comment)
    if task.creation_time:
        table.add_row("Created", str(task.creation_time))

    console.print(table)


@app.command("create")
def create_task(
    name: Annotated[str, typer.Option("--name", "-n", help="Task name")],
    target: Annotated[str, typer.Option("--target", "-t", help="Target UUID")],
    config: Annotated[str, typer.Option("--config", "-c", help="Scan config UUID")],
    scanner: Annotated[str | None, typer.Option("--scanner", "-s", help="Scanner UUID")] = None,
    comment: Annotated[str, typer.Option("--comment", help="Optional comment")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    quiet: Annotated[bool, typer.Option("-q", "--quiet", help="Only output task ID")] = False,
) -> None:
    """Create a new scan task."""
    service = _get_service()

    request = TaskCreateRequest(
        name=name,
        target_id=target,
        config_id=config,
        scanner_id=scanner,
        comment=comment,
    )

    task = service.create(request)

    if quiet:
        print(task.id)
        return

    if json_output:
        rprint(json.dumps(task.model_dump(), indent=2, default=str))
        return

    console.print(f"[green]✓ Created task:[/green] {task.name}")
    console.print(f"[dim]ID: {task.id}[/dim]")


@app.command("start")
def start_task(
    task_id: Annotated[str, typer.Argument(help="Task UUID")],
) -> None:
    """Start a scan task."""
    service = _get_service()
    report_id = service.start(task_id)

    console.print("[green]✓ Started task[/green]")
    if report_id:
        console.print(f"[dim]Report ID: {report_id}[/dim]")


@app.command("stop")
def stop_task(
    task_id: Annotated[str, typer.Argument(help="Task UUID")],
) -> None:
    """Stop a running scan task."""
    service = _get_service()
    service.stop(task_id)

    console.print("[yellow]✓ Stop requested for task[/yellow]")


@app.command("resume")
def resume_task(
    task_id: Annotated[str, typer.Argument(help="Task UUID")],
) -> None:
    """Resume a stopped/paused scan task."""
    service = _get_service()
    report_id = service.resume(task_id)

    console.print("[green]✓ Resumed task[/green]")
    if report_id:
        console.print(f"[dim]Report ID: {report_id}[/dim]")


@app.command("delete")
def delete_task(
    task_id: Annotated[str, typer.Argument(help="Task UUID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
    ultimate: Annotated[
        bool, typer.Option("--ultimate", help="Permanently delete (skip trash)")
    ] = False,
) -> None:
    """Delete a task."""
    service = _get_service()

    if not force:
        task = service.get(task_id)
        confirm = typer.confirm(f"Delete task '{task.name}'?")
        if not confirm:
            raise typer.Abort()

    service.delete(task_id, ultimate=ultimate)
    console.print(f"[green]✓ Deleted task:[/green] {task_id}")


@app.command("clone")
def clone_task(
    task_id: Annotated[str, typer.Argument(help="Task UUID to clone")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    quiet: Annotated[bool, typer.Option("-q", "--quiet", help="Only output new task ID")] = False,
) -> None:
    """Clone a task."""
    service = _get_service()
    task = service.clone(task_id)

    if quiet:
        print(task.id)
        return

    if json_output:
        rprint(json.dumps(task.model_dump(), indent=2, default=str))
        return

    console.print(f"[green]✓ Cloned task:[/green] {task.name}")
    console.print(f"[dim]New ID: {task.id}[/dim]")
