from __future__ import annotations

import json
from typing import Annotated

import typer
from rich import print as rprint

from src.infrastructure import ConfigLoader, create_client
from src.services.compliance import ComplianceService

app = typer.Typer(help="Compliance operations")


def _svc() -> ComplianceService:
    return ComplianceService(create_client(ConfigLoader.from_env_and_file()))


@app.command("policies")
def policies(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().list_policies()
    rprint(json.dumps(out.model_dump(), indent=2) if json_output else out.model_dump())


@app.command("audits")
def audits(
    filter: Annotated[str, typer.Option("--filter", "-f", help="GMP filter string")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().list_audits(filter)
    rprint(json.dumps(out, indent=2) if json_output else out)


@app.command("audit")
def get_audit(
    audit_id: str,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().get_audit(audit_id)
    rprint(json.dumps(out, indent=2) if json_output else out)


@app.command("start")
def start(audit_id: str) -> None:
    rprint({"audit_id": audit_id, "report_id": _svc().start_audit(audit_id)})


@app.command("stop")
def stop(audit_id: str) -> None:
    rprint({"audit_id": audit_id, "success": _svc().stop_audit(audit_id)})


@app.command("status")
def status(
    target_id: str,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().get_compliance_status(target_id)
    rprint(json.dumps(out.model_dump(), indent=2) if json_output else out.model_dump())
