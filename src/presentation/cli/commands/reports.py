# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""CLI commands for report management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from src.infrastructure import ConfigLoader, create_client
from src.services.reports import ReportFormat, ReportService

app = typer.Typer(help="Manage scan reports")
console = Console()


def _get_service() -> ReportService:
    """Get configured report service."""
    config = ConfigLoader.from_env_and_file()
    client = create_client(config)
    return ReportService(client)


@app.command("list")
def list_reports(
    filter: Annotated[str, typer.Option("--filter", "-f", help="GMP filter string")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """List scan reports."""
    service = _get_service()
    result = service.list(filter)

    if json_output:
        rprint(json.dumps(result.model_dump(), indent=2, default=str))
        return

    if not result.reports:
        console.print("[yellow]No reports found.[/yellow]")
        return

    table = Table(title="Scan Reports")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Task", style="green")
    table.add_column("Date")
    table.add_column("High", style="red", justify="right")
    table.add_column("Med", style="yellow", justify="right")
    table.add_column("Low", style="blue", justify="right")

    for report in result.reports:
        task_name = report.task.name if report.task else "-"
        date_str = str(report.scan_end.date()) if report.scan_end else "-"

        table.add_row(
            report.id[:8] + "...",
            task_name,
            date_str,
            str(report.summary.vulnerabilities.high),
            str(report.summary.vulnerabilities.medium),
            str(report.summary.vulnerabilities.low),
        )

    console.print(table)
    console.print(f"\n[dim]Total: {result.total} | Shown: {result.filtered}[/dim]")


@app.command("get")
def get_report(
    report_id: Annotated[str, typer.Argument(help="Report UUID")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """Get report summary."""
    service = _get_service()
    report = service.get(report_id)

    if json_output:
        rprint(json.dumps(report.model_dump(), indent=2, default=str))
        return

    console.print("\n[bold cyan]Report Summary[/bold cyan]")
    console.print(f"[dim]ID: {report.id}[/dim]\n")

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="yellow")
    table.add_column("Value")

    if report.task:
        table.add_row("Task", f"{report.task.name}")
    if report.scan_start:
        table.add_row("Scan Start", str(report.scan_start))
    if report.scan_end:
        table.add_row("Scan End", str(report.scan_end))
    if report.summary.scan_duration_seconds:
        mins = report.summary.scan_duration_seconds // 60
        secs = report.summary.scan_duration_seconds % 60
        table.add_row("Duration", f"{mins}m {secs}s")

    table.add_row("Hosts", str(report.summary.hosts_count))
    table.add_row(
        "Vulnerabilities",
        f"[red]{report.summary.vulnerabilities.high} High[/red] / "
        f"[yellow]{report.summary.vulnerabilities.medium} Medium[/yellow] / "
        f"[blue]{report.summary.vulnerabilities.low} Low[/blue]",
    )

    console.print(table)


@app.command("detail")
def get_report_detail(
    report_id: Annotated[str, typer.Argument(help="Report UUID")],
    min_qod: Annotated[int, typer.Option("--min-qod", help="Minimum QoD threshold")] = 70,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    """Get detailed report with vulnerabilities."""
    service = _get_service()
    detail = service.get_detail(report_id, min_qod=min_qod)

    if json_output:
        rprint(json.dumps(detail.model_dump(), indent=2, default=str))
        return

    console.print("\n[bold cyan]Report Detail[/bold cyan]")
    console.print(f"[dim]ID: {detail.report.id}[/dim]")
    console.print(f"[dim]Vulnerabilities: {len(detail.vulnerabilities)}[/dim]\n")

    if not detail.vulnerabilities:
        console.print("[green]No vulnerabilities found.[/green]")
        return

    table = Table(title="Vulnerabilities")
    table.add_column("Severity", justify="right")
    table.add_column("Host")
    table.add_column("Port")
    table.add_column("Name")
    table.add_column("QoD", justify="right")

    for vuln in detail.vulnerabilities[:50]:  # Limit display
        sev_color = {"High": "red", "Medium": "yellow", "Low": "blue"}.get(
            vuln.severity_level.value, "white"
        )
        sev_str = f"[{sev_color}]{vuln.severity:.1f}[/{sev_color}]"

        table.add_row(
            sev_str,
            vuln.host,
            vuln.port or "-",
            vuln.name[:50] + ("..." if len(vuln.name) > 50 else ""),
            f"{vuln.qod}%",
        )

    console.print(table)

    if len(detail.vulnerabilities) > 50:
        console.print(
            f"\n[dim]Showing 50 of {len(detail.vulnerabilities)} vulnerabilities. "
            f"Use --json for full list.[/dim]"
        )


@app.command("export")
def export_report(
    report_id: Annotated[str, typer.Argument(help="Report UUID")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output file path")],
    format: Annotated[
        str, typer.Option("--format", "-f", help="Export format (pdf, csv, xml, txt, html)")
    ] = "pdf",
) -> None:
    """Export report to file."""
    service = _get_service()

    try:
        report_format = ReportFormat(format.lower())
    except ValueError:
        console.print(f"[red]Invalid format: {format}[/red]")
        raise typer.Exit(1) from None

    content = service.export(report_id, report_format=report_format)

    output.write_bytes(content)
    console.print(f"[green]✓ Exported report to:[/green] {output}")
    console.print(f"[dim]Size: {len(content):,} bytes[/dim]")


@app.command("delete")
def delete_report(
    report_id: Annotated[str, typer.Argument(help="Report UUID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
) -> None:
    """Delete a report."""
    service = _get_service()

    if not force:
        confirm = typer.confirm(f"Delete report {report_id[:8]}...?")
        if not confirm:
            raise typer.Abort()

    service.delete(report_id)
    console.print(f"[green]✓ Deleted report:[/green] {report_id}")
