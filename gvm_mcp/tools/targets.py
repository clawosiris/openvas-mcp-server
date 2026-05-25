from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from gvm_mcp.connection import GvmConnectionManager
from gvm_mcp.utils.xml_helpers import element_to_dict


def register_target_tools(server: FastMCP, connection: GvmConnectionManager) -> None:
    @server.tool(name="gvm_list_targets", structured_output=False)
    def list_targets(filter_string: str = "") -> dict[str, Any]:
        result = connection.execute(lambda gmp: gmp.get_targets(filter_string=filter_string or None))
        return element_to_dict(result)

    @server.tool(name="gvm_get_target", structured_output=False)
    def get_target(target_id: str) -> dict[str, Any]:
        result = connection.execute(lambda gmp: gmp.get_target(target_id=target_id))
        return element_to_dict(result)

    @server.tool(name="gvm_create_target", structured_output=False)
    def create_target(name: str, hosts: list[str], comment: str = "") -> dict[str, Any]:
        result = connection.execute(
            lambda gmp: gmp.create_target(name=name, hosts=[", ".join(hosts)], comment=comment or None)
        )
        return element_to_dict(result)

    @server.tool(name="gvm_delete_target", structured_output=False)
    def delete_target(target_id: str, ultimate: bool = False) -> dict[str, Any]:
        result = connection.execute(
            lambda gmp: gmp.delete_target(target_id=target_id, ultimate=ultimate)
        )
        return element_to_dict(result)
