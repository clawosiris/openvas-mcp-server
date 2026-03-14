# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""MCP server entry point."""

import os

from mcp.server.fastmcp import FastMCP

from src.infrastructure import ConfigLoader, create_client
from src.services.assets import AssetService
from src.services.compliance import ComplianceService
from src.services.notes import NoteService
from src.services.overrides import OverrideService
from src.services.port_lists import PortListService
from src.services.reports import ReportService
from src.services.scan_configs import ScanConfigService
from src.services.schedules import ScheduleService
from src.services.system import SystemService
from src.services.targets import TargetService
from src.services.tasks import TaskService
from src.services.tickets import TicketService
from src.services.vulns import VulnerabilityService

from .toolsets.assets import register_asset_tools
from .toolsets.compliance import register_compliance_tools
from .toolsets.notes import register_note_tools
from .toolsets.overrides import register_override_tools
from .toolsets.port_lists import register_port_list_tools
from .toolsets.reports import register_report_tools
from .toolsets.scan_configs import register_scan_config_tools
from .toolsets.schedules import register_schedule_tools
from .toolsets.system import register_system_tools
from .toolsets.targets import register_target_tools
from .toolsets.tasks import register_task_tools
from .toolsets.tickets import register_ticket_tools
from .toolsets.vulns import register_vuln_tools


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
    register_scan_config_tools(server, ScanConfigService(client))
    register_port_list_tools(server, PortListService(client))
    register_schedule_tools(server, ScheduleService(client))
    register_vuln_tools(server, VulnerabilityService(client))
    register_note_tools(server, NoteService(client))
    register_override_tools(server, OverrideService(client))
    register_ticket_tools(server, TicketService(client))
    register_asset_tools(server, AssetService(client))
    register_compliance_tools(server, ComplianceService(client))

    return server


def main() -> None:
    """Run the MCP server."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    if transport not in ("stdio", "sse", "streamable-http"):
        raise ValueError(
            f"Invalid MCP_TRANSPORT='{transport}'. Must be 'stdio', 'sse', or 'streamable-http'."
        )
    server = create_server()
    server.run(transport=transport)


if __name__ == "__main__":
    main()
