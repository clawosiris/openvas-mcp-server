# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Tests for task models."""

import pytest
from pydantic import ValidationError

from src.services.tasks import (
    ScanConfig,
    Scanner,
    Task,
    TaskCreateRequest,
    TaskListResponse,
    TaskStatus,
)
from src.services.tasks.models import TargetRef


class TestTaskModel:
    """Tests for Task model."""

    def test_minimal_task(self):
        """Task can be created with minimal fields."""
        task = Task(
            id="test-uuid",
            name="Test Task",
            status=TaskStatus.NEW,
        )
        assert task.id == "test-uuid"
        assert task.name == "Test Task"
        assert task.status == TaskStatus.NEW
        assert task.progress == 0
        assert task.target is None

    def test_full_task(self):
        """Task can be created with all fields."""
        task = Task(
            id="test-uuid",
            name="Full Task",
            comment="A test task",
            status=TaskStatus.RUNNING,
            progress=45,
            target=TargetRef(id="target-id", name="Web Servers"),
            scanner=Scanner(id="scanner-id", name="OpenVAS Default"),
            config=ScanConfig(id="config-id", name="Full and fast"),
            report_count=5,
            in_use=True,
        )
        assert task.progress == 45
        assert task.target is not None
        assert task.target.name == "Web Servers"
        assert task.config is not None
        assert task.config.name == "Full and fast"

    def test_task_serialization(self):
        """Task can be serialized to dict."""
        task = Task(
            id="test-uuid",
            name="Test",
            status=TaskStatus.DONE,
        )
        data = task.model_dump()
        assert data["id"] == "test-uuid"
        assert data["status"] == "Done"


class TestTaskCreateRequest:
    """Tests for TaskCreateRequest model."""

    def test_valid_request(self):
        """Valid create request is accepted."""
        request = TaskCreateRequest(
            name="Scan Task",
            target_id="target-uuid",
            config_id="config-uuid",
        )
        assert request.name == "Scan Task"
        assert request.target_id == "target-uuid"
        assert request.config_id == "config-uuid"

    def test_name_required(self):
        """Name is required."""
        with pytest.raises(ValidationError):
            TaskCreateRequest(
                target_id="target-uuid",
                config_id="config-uuid",
            )  # type: ignore

    def test_target_required(self):
        """Target ID is required."""
        with pytest.raises(ValidationError):
            TaskCreateRequest(
                name="Task",
                config_id="config-uuid",
            )  # type: ignore

    def test_config_required(self):
        """Config ID is required."""
        with pytest.raises(ValidationError):
            TaskCreateRequest(
                name="Task",
                target_id="target-uuid",
            )  # type: ignore

    def test_defaults(self):
        """Default values are set correctly."""
        request = TaskCreateRequest(
            name="Task",
            target_id="target-uuid",
            config_id="config-uuid",
        )
        assert request.comment == ""
        assert request.scanner_id is None
        assert request.schedule_id is None
        assert request.alert_ids == []


class TestTaskListResponse:
    """Tests for TaskListResponse model."""

    def test_empty_response(self):
        """Empty list response."""
        response = TaskListResponse(
            tasks=[],
            total=0,
            filtered=0,
        )
        assert response.tasks == []
        assert response.total == 0

    def test_with_tasks(self):
        """Response with tasks."""
        task = Task(
            id="uuid",
            name="Test",
            status=TaskStatus.RUNNING,
        )
        response = TaskListResponse(
            tasks=[task],
            total=10,
            filtered=1,
        )
        assert len(response.tasks) == 1
        assert response.total == 10


class TestTaskStatusEnum:
    """Tests for TaskStatus enum."""

    def test_values(self):
        """All expected values exist."""
        assert TaskStatus.NEW.value == "New"
        assert TaskStatus.RUNNING.value == "Running"
        assert TaskStatus.DONE.value == "Done"
        assert TaskStatus.STOPPED.value == "Stopped"

    def test_from_string(self):
        """Can create from string value."""
        status = TaskStatus("Running")
        assert status == TaskStatus.RUNNING
