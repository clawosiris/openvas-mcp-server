from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from gvm_mcp.connection import GvmConnectionManager
from gvm_mcp.utils.xml_helpers import element_to_dict


def register_vulnerability_tools(server: FastMCP, connection: GvmConnectionManager) -> None:
    @server.tool(name="gvm_list_vulnerabilities", structured_output=False)
    def list_vulnerabilities(filter_string: str = "") -> dict[str, Any]:
        result = connection.execute(lambda gmp: gmp.get_vulnerabilities(filter_string=filter_string or None))
        return element_to_dict(result)

    @server.tool(name="gvm_get_result", structured_output=False)
    def get_result(result_id: str) -> dict[str, Any]:
        result = connection.execute(lambda gmp: gmp.get_result(result_id=result_id))
        return element_to_dict(result)
