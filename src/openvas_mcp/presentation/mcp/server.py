"""MCP server entry point."""

from mcp.server.fastmcp import FastMCP

from openvas_mcp.infrastructure import ConfigLoader, create_client


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

    # Create client (kept for upcoming tool registration)
    _client = create_client(config)

    # TODO: Register toolsets as services are implemented
    # register_target_tools(server, TargetService(client))

    return server


def main() -> None:
    """Run the MCP server."""
    server = create_server()
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
