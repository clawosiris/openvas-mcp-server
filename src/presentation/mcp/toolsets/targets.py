# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""MCP tools for target management."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from src.services.targets import (
    AliveTest,
    TargetCreateRequest,
    TargetService,
    TargetUpdateRequest,
)


def register_target_tools(server: FastMCP, service: TargetService) -> None:
    """Register target management tools with MCP server.

    Args:
        server: FastMCP server instance.
        service: Target service instance.
    """

    @server.tool(structured_output=False, name="openvas_list_targets")
    def list_targets(filter: str = "") -> dict[str, Any]:
        """List all scan targets.

        Args:
            filter: Optional GMP filter string (e.g., "name~web").

        Returns:
            List of targets with id, name, hosts, and count info.
        """
        result = service.list(filter)
        return result.model_dump()

    @server.tool(structured_output=False, name="openvas_get_target")
    def get_target(target_id: str) -> dict[str, Any]:
        """Get target details by ID.

        Args:
            target_id: Target UUID.

        Returns:
            Target details including hosts, credentials, port list.
        """
        result = service.get(target_id)
        return result.model_dump()

    @server.tool(structured_output=False, name="openvas_create_target")
    def create_target(
        name: str,
        hosts: list[str],
        comment: str = "",
        exclude_hosts: list[str] | None = None,
        alive_test: str = "Scan Config Default",
        port_list_id: str | None = None,
        ssh_credential_id: str | None = None,
        smb_credential_id: str | None = None,
    ) -> dict[str, Any]:
        """Create a new scan target.

        Args:
            name: Target name.
            hosts: List of hosts (IP addresses, CIDR ranges, or hostnames).
            comment: Optional description.
            exclude_hosts: Hosts to exclude from scan.
            alive_test: Host discovery method (e.g., "ICMP Ping", "Consider Alive").
            port_list_id: Port list UUID for scan.
            ssh_credential_id: SSH credential UUID for authenticated scans.
            smb_credential_id: SMB credential UUID for authenticated scans.

        Returns:
            Created target details.
        """
        # Parse alive_test string to enum
        try:
            alive_test_enum = AliveTest(alive_test)
        except ValueError:
            alive_test_enum = AliveTest.SCAN_CONFIG_DEFAULT

        request = TargetCreateRequest(
            name=name,
            hosts=hosts,
            comment=comment,
            exclude_hosts=exclude_hosts or [],
            alive_test=alive_test_enum,
            port_list_id=port_list_id,
            ssh_credential_id=ssh_credential_id,
            smb_credential_id=smb_credential_id,
        )
        result = service.create(request)
        return result.model_dump()

    @server.tool(structured_output=False, name="openvas_update_target")
    def update_target(
        target_id: str,
        name: str | None = None,
        hosts: list[str] | None = None,
        comment: str | None = None,
        exclude_hosts: list[str] | None = None,
        alive_test: str | None = None,
        port_list_id: str | None = None,
    ) -> dict[str, Any]:
        """Update an existing target.

        Args:
            target_id: Target UUID to update.
            name: New target name (optional).
            hosts: New host list (optional).
            comment: New comment (optional).
            exclude_hosts: New exclude list (optional).
            alive_test: New alive test method (optional).
            port_list_id: New port list UUID (optional).

        Returns:
            Updated target details.
        """
        # Parse alive_test if provided
        alive_test_enum = None
        if alive_test is not None:
            try:
                alive_test_enum = AliveTest(alive_test)
            except ValueError:
                alive_test_enum = AliveTest.SCAN_CONFIG_DEFAULT

        request = TargetUpdateRequest(
            name=name,
            hosts=hosts,
            comment=comment,
            exclude_hosts=exclude_hosts,
            alive_test=alive_test_enum,
            port_list_id=port_list_id,
        )
        result = service.update(target_id, request)
        return result.model_dump()

    @server.tool(structured_output=False, name="openvas_delete_target")
    def delete_target(target_id: str, ultimate: bool = False) -> dict[str, Any]:
        """Delete a target.

        Args:
            target_id: Target UUID to delete.
            ultimate: If true, permanently delete (skip trash).

        Returns:
            Success status.
        """
        success = service.delete(target_id, ultimate=ultimate)
        return {"success": success, "target_id": target_id}

    @server.tool(structured_output=False, name="openvas_clone_target")
    def clone_target(target_id: str) -> dict[str, Any]:
        """Clone an existing target.

        Args:
            target_id: Target UUID to clone.

        Returns:
            Cloned target details.
        """
        result = service.clone(target_id)
        return result.model_dump()
