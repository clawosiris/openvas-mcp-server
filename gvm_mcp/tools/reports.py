from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from gvm_mcp.connection import GvmConnectionManager
from gvm_mcp.utils.xml_helpers import element_to_dict


def register_report_tools(server: FastMCP, connection: GvmConnectionManager) -> None:
    @server.tool(name="gvm_list_reports", structured_output=False)
    def list_reports(filter_string: str = "") -> dict[str, Any]:
        result = connection.execute(lambda gmp: gmp.get_reports(filter_string=filter_string or None))
        return element_to_dict(result)

    @server.tool(name="gvm_get_report", structured_output=False)
    def get_report(
        report_id: str,
        report_format_id: str | None = None,
        details: bool = True,
    ) -> dict[str, Any]:
        result = connection.execute(
            lambda gmp: gmp.get_report(
                report_id=report_id,
                report_format_id=report_format_id,
                details=details,
            )
        )
        return element_to_dict(result)
