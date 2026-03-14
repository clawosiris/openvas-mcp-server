# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG


from typing import TYPE_CHECKING, Any

from src.services.assets import AssetService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_asset_tools(server: FastMCP, service: AssetService) -> None:
    @server.tool(name="openvas_list_asset_hosts")
    def list_asset_hosts(filter: str = "") -> dict[str, Any]:
        items = service.list_hosts(filter)
        return {"items": [i.model_dump() for i in items], "total": len(items)}

    @server.tool(name="openvas_list_asset_os")
    def list_asset_os(filter: str = "") -> dict[str, Any]:
        items = service.list_os(filter)
        return {"items": [i.model_dump() for i in items], "total": len(items)}

    @server.tool(name="openvas_list_asset_tls_certificates")
    def list_asset_tls_certificates(filter: str = "") -> dict[str, Any]:
        items = service.list_tls_certificates(filter)
        return {"items": [i.model_dump() for i in items], "total": len(items)}
