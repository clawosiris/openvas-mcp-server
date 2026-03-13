"""CLI commands for vulnerability operations."""

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from src.infrastructure import ConfigLoader, create_client
from src.services.vulns import VulnerabilityService

app = typer.Typer(help="Manage vulnerabilities")
console = Console()


def _get_service() -> VulnerabilityService:
    config = ConfigLoader.from_env_and_file()
    client = create_client(config)
    return VulnerabilityService(client)


@app.command("list")
def list_vulns(
    report_id: Annotated[str, typer.Option("--report", "-r", help="Report UUID")],
    min_qod: Annotated[int, typer.Option("--min-qod", help="Minimum QoD")] = 70,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    service = _get_service()
    result = service.list(report_id, min_qod=min_qod)

    if json_output:
        rprint(json.dumps(result.model_dump(), indent=2, default=str))
        return

    table = Table(title="Vulnerability Findings")
    table.add_column("Severity", justify="right")
    table.add_column("Host")
    table.add_column("Port")
    table.add_column("Name")

    for finding in result.findings[:100]:
        sev_color = (
            "red" if finding.severity >= 7 else "yellow" if finding.severity >= 4 else "blue"
        )
        table.add_row(
            f"[{sev_color}]{finding.severity:.1f}[/{sev_color}]",
            finding.host,
            finding.port or "-",
            finding.name[:60] + ("..." if len(finding.name) > 60 else ""),
        )

    console.print(table)
    console.print(f"[dim]Total: {result.total}[/dim]")


@app.command("search-nvts")
def search_nvts(
    query: Annotated[str, typer.Argument(help="NVT search query")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    service = _get_service()
    results = service.search_nvts(query)

    if json_output:
        rprint(json.dumps([r.model_dump() for r in results], indent=2, default=str))
        return

    table = Table(title=f"NVT Search: {query}")
    table.add_column("OID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Family")
    table.add_column("CVSS", justify="right")

    for nvt in results[:100]:
        table.add_row(nvt.oid, nvt.name, nvt.family, f"{nvt.cvss_base:.1f}")

    console.print(table)
    console.print(f"[dim]Total: {len(results)}[/dim]")
