# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""MCP tools for system operations."""


from typing import TYPE_CHECKING, Any

from src.services.system import SystemService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_system_tools(server: FastMCP, service: SystemService) -> None:
    """Register system tools with MCP server.

    Args:
        server: FastMCP server instance.
        service: System service instance.
    """

    @server.tool(name="openvas_get_version")
    def get_version() -> dict[str, Any]:
        """Get GVM version information.

        Returns:
            GVM version details including GMP protocol version.
        """
        result = service.get_version()
        return result.model_dump()

    @server.tool(name="openvas_test_connection")
    def test_connection() -> dict[str, Any]:
        """Test connection to GVM server.

        Returns:
            Connection status and version if connected.
        """
        try:
            version = service.get_version()
            return {
                "connected": True,
                "gmp_version": version.gmp_version,
            }
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
            }
