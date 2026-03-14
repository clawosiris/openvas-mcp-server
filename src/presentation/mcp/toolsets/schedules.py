# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""MCP tools for schedule management."""

from typing import Any
from mcp.server.fastmcp import FastMCP

from src.services.schedules import ScheduleService


def register_schedule_tools(server: FastMCP, service: ScheduleService) -> None:
    """Register schedule management tools."""

    @server.tool(name="openvas_list_schedules")
    def list_schedules(filter: str = "") -> dict[str, Any]:
        result = service.list(filter)
        return result.model_dump()

    @server.tool(name="openvas_get_schedule")
    def get_schedule(schedule_id: str) -> dict[str, Any]:
        result = service.get(schedule_id)
        return result.model_dump()
