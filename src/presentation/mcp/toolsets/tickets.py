# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG


from typing import TYPE_CHECKING, Any

from src.services.tickets import TicketService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_ticket_tools(server: FastMCP, service: TicketService) -> None:
    @server.tool(name="openvas_list_tickets")
    def list_tickets(filter: str = "") -> dict[str, Any]:
        return service.list(filter).model_dump()

    @server.tool(name="openvas_get_ticket")
    def get_ticket(ticket_id: str) -> dict[str, Any]:
        return service.get(ticket_id).model_dump()

    @server.tool(name="openvas_create_ticket")
    def create_ticket(result_id: str, comment: str = "") -> dict[str, Any]:
        return service.create(result_id=result_id, comment=comment).model_dump()

    @server.tool(name="openvas_update_ticket")
    def update_ticket(ticket_id: str, status: str, comment: str = "") -> dict[str, Any]:
        return service.update(ticket_id=ticket_id, status=status, comment=comment).model_dump()

    @server.tool(name="openvas_delete_ticket")
    def delete_ticket(ticket_id: str) -> dict[str, Any]:
        return {"success": service.delete(ticket_id), "ticket_id": ticket_id}
