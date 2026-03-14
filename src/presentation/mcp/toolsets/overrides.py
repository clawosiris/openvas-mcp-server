# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG


from typing import TYPE_CHECKING, Any

from src.services.overrides import OverrideService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_override_tools(server: FastMCP, service: OverrideService) -> None:
    @server.tool(name="openvas_list_overrides")
    def list_overrides(filter: str = "") -> dict[str, Any]:
        return service.list(filter).model_dump()

    @server.tool(name="openvas_get_override")
    def get_override(override_id: str) -> dict[str, Any]:
        return service.get(override_id).model_dump()

    @server.tool(name="openvas_create_override")
    def create_override(text: str, nvt_oid: str = "") -> dict[str, Any]:
        return service.create(text_value=text, nvt_oid=nvt_oid).model_dump()

    @server.tool(name="openvas_update_override")
    def update_override(override_id: str, text: str) -> dict[str, Any]:
        return service.update(override_id, text).model_dump()

    @server.tool(name="openvas_delete_override")
    def delete_override(override_id: str) -> dict[str, Any]:
        return {"success": service.delete(override_id), "override_id": override_id}
