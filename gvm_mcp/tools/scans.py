from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from gvm_mcp.connection import GvmConnectionManager
from gvm_mcp.utils.xml_helpers import element_to_dict


def register_scan_tools(server: FastMCP, connection: GvmConnectionManager) -> None:
    @server.tool(name="gvm_list_tasks", structured_output=False)
    def list_tasks(filter_string: str = "") -> dict[str, Any]:
        result = connection.execute(lambda gmp: gmp.get_tasks(filter_string=filter_string or None))
        return element_to_dict(result)

    @server.tool(name="gvm_create_task", structured_output=False)
    def create_task(
        name: str,
        target_id: str,
        config_id: str,
        scanner_id: str | None = None,
        comment: str = "",
    ) -> dict[str, Any]:
        result = connection.execute(
            lambda gmp: gmp.create_task(
                name=name,
                target_id=target_id,
                config_id=config_id,
                scanner_id=scanner_id,
                comment=comment or None,
            )
        )
        return element_to_dict(result)

    @server.tool(name="gvm_start_task", structured_output=False)
    def start_task(task_id: str) -> dict[str, Any]:
        result = connection.execute(lambda gmp: gmp.start_task(task_id=task_id))
        return element_to_dict(result)

    @server.tool(name="gvm_stop_task", structured_output=False)
    def stop_task(task_id: str) -> dict[str, Any]:
        result = connection.execute(lambda gmp: gmp.stop_task(task_id=task_id))
        return element_to_dict(result)
