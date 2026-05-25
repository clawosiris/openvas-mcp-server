from __future__ import annotations

import os
from typing import Literal, cast

from mcp.server.fastmcp import FastMCP

from .config import load_config
from .connection import GvmConnectionManager
from .tools import (
    register_extraction_tools,
    register_report_tools,
    register_scan_tools,
    register_target_tools,
    register_vulnerability_tools,
)

TransportType = Literal["stdio", "sse", "streamable-http"]
VALID_TRANSPORTS: set[TransportType] = {"stdio", "sse", "streamable-http"}


def create_server() -> FastMCP:
    config = load_config()
    connection = GvmConnectionManager(config)

    server = FastMCP(name="gvm-mcp", description="Greenbone Vulnerability Management MCP server")

    register_target_tools(server, connection)
    register_scan_tools(server, connection)
    register_report_tools(server, connection)
    register_vulnerability_tools(server, connection)
    register_extraction_tools(server, connection)

    return server


def main() -> None:
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport not in VALID_TRANSPORTS:
        raise ValueError(
            f"Invalid MCP_TRANSPORT='{transport}'. Must be 'stdio', 'sse', or 'streamable-http'."
        )

    server = create_server()
    server.run(transport=cast(TransportType, transport))


if __name__ == "__main__":
    main()
