# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""MCP tools for task (scan) management."""

from typing import Any
from mcp.server.fastmcp import FastMCP

from src.services.tasks import TaskCreateRequest, TaskService


def register_task_tools(server: FastMCP, service: TaskService) -> None:
    """Register task management tools with MCP server.

    Args:
        server: FastMCP server instance.
        service: Task service instance.
    """

    @server.tool(name="openvas_list_tasks")
    def list_tasks(filter: str = "") -> dict[str, Any]:
        """List all scan tasks.

        Args:
            filter: Optional GMP filter string (e.g., "status=Running").

        Returns:
            List of tasks with id, name, status, progress, and target info.
        """
        result = service.list(filter)
        return result.model_dump()

    @server.tool(name="openvas_get_task")
    def get_task(task_id: str) -> dict[str, Any]:
        """Get task details by ID.

        Args:
            task_id: Task UUID.

        Returns:
            Task details including status, progress, target, and last report.
        """
        result = service.get(task_id)
        return result.model_dump()

    @server.tool(name="openvas_create_task")
    def create_task(
        name: str,
        target_id: str,
        config_id: str,
        scanner_id: str | None = None,
        comment: str = "",
    ) -> dict[str, Any]:
        """Create a new scan task.

        Args:
            name: Task name.
            target_id: Target UUID to scan.
            config_id: Scan configuration UUID.
            scanner_id: Scanner UUID (optional, uses default if not specified).
            comment: Optional description.

        Returns:
            Created task details.
        """
        request = TaskCreateRequest(
            name=name,
            target_id=target_id,
            config_id=config_id,
            scanner_id=scanner_id,
            comment=comment,
        )
        result = service.create(request)
        return result.model_dump()

    @server.tool(name="openvas_start_task")
    def start_task(task_id: str) -> dict[str, Any]:
        """Start a scan task.

        Args:
            task_id: Task UUID to start.

        Returns:
            Report ID of the started scan.
        """
        report_id = service.start(task_id)
        return {"task_id": task_id, "report_id": report_id, "status": "started"}

    @server.tool(name="openvas_stop_task")
    def stop_task(task_id: str) -> dict[str, Any]:
        """Stop a running scan task.

        Args:
            task_id: Task UUID to stop.

        Returns:
            Success status.
        """
        success = service.stop(task_id)
        return {"task_id": task_id, "success": success, "status": "stop_requested"}

    @server.tool(name="openvas_resume_task")
    def resume_task(task_id: str) -> dict[str, Any]:
        """Resume a stopped or paused scan task.

        Args:
            task_id: Task UUID to resume.

        Returns:
            Report ID of the resumed scan.
        """
        report_id = service.resume(task_id)
        return {"task_id": task_id, "report_id": report_id, "status": "resumed"}

    @server.tool(name="openvas_delete_task")
    def delete_task(task_id: str, ultimate: bool = False) -> dict[str, Any]:
        """Delete a scan task.

        Args:
            task_id: Task UUID to delete.
            ultimate: If true, permanently delete (skip trash).

        Returns:
            Success status.
        """
        success = service.delete(task_id, ultimate=ultimate)
        return {"task_id": task_id, "success": success}

    @server.tool(name="openvas_clone_task")
    def clone_task(task_id: str) -> dict[str, Any]:
        """Clone an existing task.

        Args:
            task_id: Task UUID to clone.

        Returns:
            Cloned task details.
        """
        result = service.clone(task_id)
        return result.model_dump()
