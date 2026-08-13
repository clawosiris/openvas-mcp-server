# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

import json
from typing import Annotated

import typer
from rich import print as rprint

from src.infrastructure import ConfigLoader, create_client
from src.services.tickets import TicketService

app = typer.Typer(help="Manage tickets")


def _svc() -> TicketService:
    return TicketService(create_client(ConfigLoader.from_env_and_file()))


@app.command("list")
def list_tickets(
    filter: Annotated[str, typer.Option("--filter", "-f", help="GMP filter string")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().list(filter)
    rprint(json.dumps(out.model_dump(), indent=2) if json_output else out.model_dump())


@app.command("get")
def get_ticket(
    ticket_id: str,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().get(ticket_id)
    rprint(json.dumps(out.model_dump(), indent=2) if json_output else out.model_dump())


@app.command("create")
def create_ticket(
    result_id: str,
    comment: Annotated[str, typer.Option("--comment", "-c", help="Ticket comment")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().create(result_id=result_id, comment=comment)
    rprint(json.dumps(out.model_dump(), indent=2) if json_output else out.model_dump())


@app.command("update")
def update_ticket(
    ticket_id: str,
    status: str,
    comment: Annotated[str, typer.Option("--comment", "-c", help="Ticket comment")] = "",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
) -> None:
    out = _svc().update(ticket_id=ticket_id, status=status, comment=comment)
    rprint(json.dumps(out.model_dump(), indent=2) if json_output else out.model_dump())


@app.command("delete")
def delete_ticket(ticket_id: str) -> None:
    rprint({"success": _svc().delete(ticket_id), "ticket_id": ticket_id})
