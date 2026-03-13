"""MCP server entry point."""

from mcp.server.fastmcp import FastMCP

from src.infrastructure import ConfigLoader, create_client
from src.services.reports import ReportService
from src.services.system import SystemService
from src.services.targets import TargetService
from src.services.tasks import TaskService

from .toolsets.reports import register_report_tools
from .toolsets.system import register_system_tools
from .toolsets.targets import register_target_tools
from .toolsets.tasks import register_task_tools


def create_server() -> FastMCP:
    """Create and configure the MCP server.

    Returns:
        Configured FastMCP server instance.
    """
    server = FastMCP(
        name="openvas-mcp",
        description="OpenVAS/GVM vulnerability management",
    )

    # Load configuration from environment
    config = ConfigLoader.from_env()

    # Create client
    client = create_client(config)

    # Register toolsets
    register_system_tools(server, SystemService(client))
    register_target_tools(server, TargetService(client))
    register_task_tools(server, TaskService(client))
    register_report_tools(server, ReportService(client))

    return server


def main() -> None:
    """Run the MCP server."""
    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
