"""MCP server entry point."""

from mcp.server.fastmcp import FastMCP

from src.infrastructure import ConfigLoader, create_client
from src.services.targets import TargetService

from .toolsets.targets import register_target_tools


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
    register_target_tools(server, TargetService(client))

    return server


def main() -> None:
    """Run the MCP server."""
    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
