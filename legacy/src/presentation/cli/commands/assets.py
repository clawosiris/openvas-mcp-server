# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich import print as rprint

from src.infrastructure import ConfigLoader, create_client
from src.services.assets import AssetService

app = typer.Typer(help="Manage assets")


def _svc() -> AssetService:
    return AssetService(create_client(ConfigLoader.from_env_and_file()))


@app.command("hosts")
def hosts(
    filter: Annotated[str, typer.Option("--filter", "-f", help="GMP filter string")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().list_hosts(filter)
    data = [x.model_dump() for x in out]
    rprint(json.dumps(data, indent=2) if json_output else data)


@app.command("os")
def os_assets(
    filter: Annotated[str, typer.Option("--filter", "-f", help="GMP filter string")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().list_os(filter)
    data = [x.model_dump() for x in out]
    rprint(json.dumps(data, indent=2) if json_output else data)


@app.command("certs")
def certs(
    filter: Annotated[str, typer.Option("--filter", "-f", help="GMP filter string")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().list_tls_certificates(filter)
    data = [x.model_dump() for x in out]
    rprint(json.dumps(data, indent=2) if json_output else data)
