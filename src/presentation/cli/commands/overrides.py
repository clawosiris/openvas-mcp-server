from __future__ import annotations

import json
from typing import Annotated

import typer
from rich import print as rprint

from src.infrastructure import ConfigLoader, create_client
from src.services.overrides import OverrideService

app = typer.Typer(help="Manage overrides")


def _svc() -> OverrideService:
    return OverrideService(create_client(ConfigLoader.from_env_and_file()))


@app.command("list")
def list_overrides(
    filter: Annotated[str, typer.Option("--filter", "-f", help="GMP filter string")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().list(filter)
    rprint(json.dumps(out.model_dump(), indent=2) if json_output else out.model_dump())


@app.command("get")
def get_override(
    override_id: str,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().get(override_id)
    rprint(json.dumps(out.model_dump(), indent=2) if json_output else out.model_dump())


@app.command("create")
def create_override(
    text: str,
    nvt_oid: Annotated[str, typer.Option("--nvt-oid", help="NVT OID")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().create(text_value=text, nvt_oid=nvt_oid)
    rprint(json.dumps(out.model_dump(), indent=2) if json_output else out.model_dump())


@app.command("update")
def update_override(
    override_id: str,
    text: str,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().update(override_id, text)
    rprint(json.dumps(out.model_dump(), indent=2) if json_output else out.model_dump())


@app.command("delete")
def delete_override(override_id: str) -> None:
    rprint({"success": _svc().delete(override_id), "override_id": override_id})
