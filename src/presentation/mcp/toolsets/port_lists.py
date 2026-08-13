# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""MCP tools for port list management."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from src.services.port_lists import PortListService


def register_port_list_tools(server: FastMCP, service: PortListService) -> None:
    """Register port list management tools."""

    @server.tool(structured_output=False, name="openvas_list_port_lists")
    def list_port_lists(filter: str = "") -> dict[str, Any]:
        result = service.list(filter)
        return result.model_dump()

    @server.tool(structured_output=False, name="openvas_get_port_list")
    def get_port_list(port_list_id: str) -> dict[str, Any]:
        result = service.get(port_list_id)
        return result.model_dump()
