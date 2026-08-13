# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Task (scan) service implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from src.errors import OperationError, ResourceNotFoundError
from src.utils import (
    attr,
    collect,
    response_ok,
    text,
    to_bool,
    to_datetime,
    to_int,
    validate_filter,
    validate_uuid,
)

from .models import (
    LastReport,
    ScanConfig,
    Scanner,
    TargetRef,
    Task,
    TaskCreateRequest,
    TaskListResponse,
    TaskStatus,
)

if TYPE_CHECKING:
    from src.infrastructure.client import GvmClient


class TaskService:
    """Service for managing scan tasks.

    Provides operations for creating, starting, stopping, and monitoring scans.
    """

    def __init__(self, client: GvmClient) -> None:
        """Initialize task service.

        Args:
            client: GVM client for executing GMP operations.
        """
        self._client = client

    def get(self, task_id: str) -> Task:
        """Get a task by ID.

        Args:
            task_id: Task UUID.

        Returns:
            Task details.

        Raises:
            InvalidUuidError: If task_id is not a valid UUID.
            ResourceNotFoundError: If task doesn't exist.
        """
        task_id = validate_uuid(task_id, "task_id")

        def operation(gmp: Any) -> Any:
            return gmp.get_task(task_id=task_id)

        response: Element = self._client.execute(operation)

        if not response_ok(response):
            raise ResourceNotFoundError("task", task_id)

        task_elem = response.find("task")
        if task_elem is None:
            raise ResourceNotFoundError("task", task_id)

        return self._parse_task(task_elem)

    def list(self, filter_string: str = "") -> TaskListResponse:
        """List tasks with optional filter.

        Args:
            filter_string: GMP filter string (e.g., "status=Running").

        Returns:
            List of tasks with pagination info.

        Raises:
            InvalidFilterError: If filter contains invalid characters.
        """
        filter_string = validate_filter(filter_string)

        def operation(gmp: Any) -> Any:
            return gmp.get_tasks(filter_string=filter_string or None)

        response: Element = self._client.execute(operation)

        tasks = collect(response, "task", self._parse_task)

        # Extract counts
        tasks_elem = response.find("tasks")
        total = len(tasks)
        if tasks_elem is not None:
            total = to_int(attr(tasks_elem, "max"), len(tasks))

        return TaskListResponse(
            tasks=tasks,
            total=total,
            filtered=len(tasks),
        )

    def create(self, request: TaskCreateRequest) -> Task:
        """Create a new task.

        Args:
            request: Task creation request.

        Returns:
            Created task details.
        """
        # Validate UUIDs
        validate_uuid(request.target_id, "target_id")
        validate_uuid(request.config_id, "config_id")
        if request.scanner_id:
            validate_uuid(request.scanner_id, "scanner_id")
        if request.schedule_id:
            validate_uuid(request.schedule_id, "schedule_id")
        for i, alert_id in enumerate(request.alert_ids):
            validate_uuid(alert_id, f"alert_ids[{i}]")

        def operation(gmp: Any) -> Any:
            return gmp.create_task(
                name=request.name,
                target_id=request.target_id,
                config_id=request.config_id,
                scanner_id=request.scanner_id,
                comment=request.comment or None,
                schedule_id=request.schedule_id,
                alert_ids=request.alert_ids or None,
            )

        response: Element = self._client.execute(operation)

        task_id = attr(response, "id")
        if not task_id:
            task_id = text(response, "id")

        return self.get(task_id)

    def delete(self, task_id: str, *, ultimate: bool = False) -> bool:
        """Delete a task.

        Args:
            task_id: Task UUID.
            ultimate: If True, permanently delete (no trash).

        Returns:
            True if deleted successfully.

        Raises:
            InvalidUuidError: If task_id is not a valid UUID.
            ResourceNotFoundError: If task doesn't exist.
        """
        task_id = validate_uuid(task_id, "task_id")

        def operation(gmp: Any) -> Any:
            return gmp.delete_task(task_id=task_id, ultimate=ultimate)

        response: Element = self._client.execute(operation)

        status = attr(response, "status")
        if status == "404":
            raise ResourceNotFoundError("task", task_id)

        return response_ok(response)

    def start(self, task_id: str) -> str:
        """Start a scan task.

        Args:
            task_id: Task UUID.

        Returns:
            Report ID of the started scan.

        Raises:
            InvalidUuidError: If task_id is not a valid UUID.
            ResourceNotFoundError: If task doesn't exist.
            OperationError: If task cannot be started.
        """
        task_id = validate_uuid(task_id, "task_id")

        def operation(gmp: Any) -> Any:
            return gmp.start_task(task_id=task_id)

        response: Element = self._client.execute(operation)

        if not response_ok(response):
            status_text = attr(response, "status_text")
            raise OperationError(f"Failed to start task: {status_text}")

        # Extract report ID from response
        report_id_elem = response.find("report_id")
        report_id = report_id_elem.text if report_id_elem is not None else ""

        return report_id or ""

    def stop(self, task_id: str) -> bool:
        """Stop a running scan task.

        Args:
            task_id: Task UUID.

        Returns:
            True if stop was requested successfully.

        Raises:
            InvalidUuidError: If task_id is not a valid UUID.
            OperationError: If task cannot be stopped.
        """
        task_id = validate_uuid(task_id, "task_id")

        def operation(gmp: Any) -> Any:
            return gmp.stop_task(task_id=task_id)

        response: Element = self._client.execute(operation)

        if not response_ok(response):
            status_text = attr(response, "status_text")
            raise OperationError(f"Failed to stop task: {status_text}")

        return True

    def resume(self, task_id: str) -> str:
        """Resume a stopped/paused scan task.

        Args:
            task_id: Task UUID.

        Returns:
            Report ID of the resumed scan.

        Raises:
            InvalidUuidError: If task_id is not a valid UUID.
            OperationError: If task cannot be resumed.
        """
        task_id = validate_uuid(task_id, "task_id")

        def operation(gmp: Any) -> Any:
            return gmp.resume_task(task_id=task_id)

        response: Element = self._client.execute(operation)

        if not response_ok(response):
            status_text = attr(response, "status_text")
            raise OperationError(f"Failed to resume task: {status_text}")

        report_id_elem = response.find("report_id")
        report_id = report_id_elem.text if report_id_elem is not None else ""

        return report_id or ""

    def clone(self, task_id: str) -> Task:
        """Clone an existing task.

        Args:
            task_id: Task UUID to clone.

        Returns:
            Cloned task details.

        Raises:
            InvalidUuidError: If task_id is not a valid UUID.
            ResourceNotFoundError: If task doesn't exist.
        """
        task_id = validate_uuid(task_id, "task_id")

        def operation(gmp: Any) -> Any:
            return gmp.clone_task(task_id=task_id)

        response: Element = self._client.execute(operation)

        if not response_ok(response):
            raise ResourceNotFoundError("task", task_id)

        new_task_id = attr(response, "id")
        return self.get(new_task_id)

    def _parse_task(self, elem: Element) -> Task:
        """Parse task XML element into Task model."""
        # Parse status
        status_str = text(elem, "status")
        status = self._parse_status(status_str)

        # Parse target
        target = None
        target_elem = elem.find("target")
        if target_elem is not None:
            target_id = attr(target_elem, "id")
            if target_id:
                target = TargetRef(
                    id=target_id,
                    name=text(target_elem, "name"),
                )

        # Parse scanner
        scanner = None
        scanner_elem = elem.find("scanner")
        if scanner_elem is not None:
            scanner_id = attr(scanner_elem, "id")
            if scanner_id:
                scanner = Scanner(
                    id=scanner_id,
                    name=text(scanner_elem, "name"),
                )

        # Parse scan config
        config = None
        config_elem = elem.find("config")
        if config_elem is not None:
            config_id = attr(config_elem, "id")
            if config_id:
                config = ScanConfig(
                    id=config_id,
                    name=text(config_elem, "name"),
                )

        # Parse last report
        last_report = None
        last_report_elem = elem.find("last_report/report")
        if last_report_elem is not None:
            report_id = attr(last_report_elem, "id")
            if report_id:
                last_report = LastReport(
                    id=report_id,
                    timestamp=to_datetime(text(last_report_elem, "timestamp")),
                )

        # Parse report count
        report_count = to_int(text(elem, "report_count/finished"), 0)

        return Task(
            id=attr(elem, "id"),
            name=text(elem, "name"),
            comment=text(elem, "comment"),
            status=status,
            progress=to_int(text(elem, "progress"), 0),
            target=target,
            scanner=scanner,
            config=config,
            last_report=last_report,
            report_count=report_count,
            trend=text(elem, "trend"),
            in_use=to_bool(text(elem, "in_use")),
            creation_time=to_datetime(text(elem, "creation_time")),
            modification_time=to_datetime(text(elem, "modification_time")),
        )

    def _parse_status(self, value: str) -> TaskStatus:
        """Parse status string to enum."""
        if not value:
            return TaskStatus.NEW
        for member in TaskStatus:
            if member.value.lower() == value.lower():
                return member
        return TaskStatus.NEW
