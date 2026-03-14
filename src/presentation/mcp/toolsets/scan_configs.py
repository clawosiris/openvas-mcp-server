# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""MCP tools for scan config management."""

from typing import Any
from mcp.server.fastmcp import FastMCP

from src.services.scan_configs import ScanConfigService


def register_scan_config_tools(server: FastMCP, service: ScanConfigService) -> None:
    """Register scan config management tools."""

    @server.tool(name="openvas_list_scan_configs")
    def list_scan_configs(filter: str = "") -> dict[str, Any]:
        result = service.list(filter)
        return result.model_dump()

    @server.tool(name="openvas_get_scan_config")
    def get_scan_config(config_id: str) -> dict[str, Any]:
        result = service.get(config_id)
        return result.model_dump()
