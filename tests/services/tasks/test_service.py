"""Tests for task service."""

from unittest.mock import MagicMock
from xml.etree.ElementTree import Element, SubElement

import pytest

from src.errors import OperationError, ResourceNotFoundError
from src.services.tasks import TaskCreateRequest, TaskService, TaskStatus
from src.utils import InvalidUuidError


@pytest.fixture
def mock_client() -> MagicMock:
    """Create mock GVM client."""
    return MagicMock()


@pytest.fixture
def task_service(mock_client: MagicMock) -> TaskService:
    """Create task service with mock client."""
    return TaskService(mock_client)


def _create_task_xml(
    task_id: str = "12345678-1234-1234-1234-123456789abc",
    name: str = "Test Task",
    status: str = "New",
    progress: str = "0",
) -> Element:
    """Create a task XML element for testing."""
    task = Element("task", {"id": task_id})
    SubElement(task, "name").text = name
    SubElement(task, "comment").text = "Test comment"
    SubElement(task, "status").text = status
    SubElement(task, "progress").text = progress
    SubElement(task, "in_use").text = "0"
    SubElement(task, "creation_time").text = "2024-01-15T10:30:00Z"

    # Add target
    target = SubElement(task, "target", {"id": "target-uuid-1234"})
    SubElement(target, "name").text = "Test Target"

    # Add config
    config = SubElement(task, "config", {"id": "config-uuid-1234"})
    SubElement(config, "name").text = "Full and fast"

    # Add scanner
    scanner = SubElement(task, "scanner", {"id": "scanner-uuid-1234"})
    SubElement(scanner, "name").text = "OpenVAS Default"

    # Add report count
    report_count = SubElement(task, "report_count")
    SubElement(report_count, "finished").text = "3"

    return task


def _create_get_task_response(task: Element) -> Element:
    """Wrap task in get_task response."""
    response = Element("get_tasks_response", {"status": "200", "status_text": "OK"})
    response.append(task)
    return response


def _create_tasks_response(tasks: list[Element]) -> Element:
    """Create get_tasks response."""
    response = Element("get_tasks_response", {"status": "200", "status_text": "OK"})
    SubElement(response, "tasks", {"start": "1", "max": str(len(tasks))})
    for task in tasks:
        response.append(task)
    return response


class TestTaskServiceGet:
    """Tests for TaskService.get() method."""

    def test_get_existing_task(self, task_service: TaskService, mock_client: MagicMock):
        """Get returns task when it exists."""
        task_xml = _create_task_xml()
        response = _create_get_task_response(task_xml)
        mock_client.execute.return_value = response

        task = task_service.get("12345678-1234-1234-1234-123456789abc")

        assert task.id == "12345678-1234-1234-1234-123456789abc"
        assert task.name == "Test Task"
        assert task.status == TaskStatus.NEW
        assert task.target is not None
        assert task.target.name == "Test Target"

    def test_get_invalid_uuid(self, task_service: TaskService):
        """Get raises InvalidUuidError for invalid UUID."""
        with pytest.raises(InvalidUuidError):
            task_service.get("not-a-valid-uuid")

    def test_get_nonexistent_task(self, task_service: TaskService, mock_client: MagicMock):
        """Get raises ResourceNotFoundError when task doesn't exist."""
        response = Element("get_tasks_response", {"status": "404", "status_text": "Not Found"})
        mock_client.execute.return_value = response

        with pytest.raises(ResourceNotFoundError) as exc_info:
            task_service.get("12345678-1234-1234-1234-123456789abc")

        assert exc_info.value.details.resource_type == "task"


class TestTaskServiceList:
    """Tests for TaskService.list() method."""

    def test_list_returns_tasks(self, task_service: TaskService, mock_client: MagicMock):
        """List returns all tasks."""
        task1 = _create_task_xml(task_id="uuid-1", name="Task 1")
        task2 = _create_task_xml(task_id="uuid-2", name="Task 2", status="Running")
        response = _create_tasks_response([task1, task2])
        mock_client.execute.return_value = response

        result = task_service.list()

        assert len(result.tasks) == 2
        assert result.tasks[0].name == "Task 1"
        assert result.tasks[1].name == "Task 2"
        assert result.tasks[1].status == TaskStatus.RUNNING

    def test_list_empty(self, task_service: TaskService, mock_client: MagicMock):
        """List returns empty list when no tasks."""
        response = _create_tasks_response([])
        mock_client.execute.return_value = response

        result = task_service.list()

        assert result.tasks == []
        assert result.filtered == 0


class TestTaskServiceCreate:
    """Tests for TaskService.create() method."""

    def test_create_task(self, task_service: TaskService, mock_client: MagicMock):
        """Create creates task and returns it."""
        new_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        create_response = Element(
            "create_task_response",
            {"status": "201", "status_text": "OK", "id": new_uuid},
        )

        task_xml = _create_task_xml(task_id=new_uuid, name="New Task")
        get_response = _create_get_task_response(task_xml)

        mock_client.execute.side_effect = [create_response, get_response]

        request = TaskCreateRequest(
            name="New Task",
            target_id="11111111-2222-3333-4444-555555555555",
            config_id="66666666-7777-8888-9999-aaaaaaaaaaaa",
        )

        task = task_service.create(request)

        assert task.id == new_uuid
        assert mock_client.execute.call_count == 2


class TestTaskServiceStart:
    """Tests for TaskService.start() method."""

    def test_start_task(self, task_service: TaskService, mock_client: MagicMock):
        """Start returns report ID."""
        response = Element("start_task_response", {"status": "202", "status_text": "OK"})
        SubElement(response, "report_id").text = "report-uuid-1234"
        mock_client.execute.return_value = response

        report_id = task_service.start("12345678-1234-1234-1234-123456789abc")

        assert report_id == "report-uuid-1234"

    def test_start_task_failure(self, task_service: TaskService, mock_client: MagicMock):
        """Start raises OperationError on failure."""
        response = Element(
            "start_task_response", {"status": "400", "status_text": "Task is already running"}
        )
        mock_client.execute.return_value = response

        with pytest.raises(OperationError):
            task_service.start("12345678-1234-1234-1234-123456789abc")


class TestTaskServiceStop:
    """Tests for TaskService.stop() method."""

    def test_stop_task(self, task_service: TaskService, mock_client: MagicMock):
        """Stop returns True on success."""
        response = Element("stop_task_response", {"status": "200", "status_text": "OK"})
        mock_client.execute.return_value = response

        result = task_service.stop("12345678-1234-1234-1234-123456789abc")

        assert result is True

    def test_stop_task_failure(self, task_service: TaskService, mock_client: MagicMock):
        """Stop raises OperationError on failure."""
        response = Element(
            "stop_task_response", {"status": "400", "status_text": "Task is not running"}
        )
        mock_client.execute.return_value = response

        with pytest.raises(OperationError):
            task_service.stop("12345678-1234-1234-1234-123456789abc")


class TestTaskServiceResume:
    """Tests for TaskService.resume() method."""

    def test_resume_task(self, task_service: TaskService, mock_client: MagicMock):
        """Resume returns report ID."""
        response = Element("resume_task_response", {"status": "202", "status_text": "OK"})
        SubElement(response, "report_id").text = "report-uuid-5678"
        mock_client.execute.return_value = response

        report_id = task_service.resume("12345678-1234-1234-1234-123456789abc")

        assert report_id == "report-uuid-5678"


class TestTaskServiceDelete:
    """Tests for TaskService.delete() method."""

    def test_delete_task(self, task_service: TaskService, mock_client: MagicMock):
        """Delete returns True on success."""
        response = Element("delete_task_response", {"status": "200", "status_text": "OK"})
        mock_client.execute.return_value = response

        result = task_service.delete("12345678-1234-1234-1234-123456789abc")

        assert result is True

    def test_delete_nonexistent(self, task_service: TaskService, mock_client: MagicMock):
        """Delete raises ResourceNotFoundError for nonexistent task."""
        response = Element("delete_task_response", {"status": "404", "status_text": "Not Found"})
        mock_client.execute.return_value = response

        with pytest.raises(ResourceNotFoundError):
            task_service.delete("12345678-1234-1234-1234-123456789abc")


class TestTaskServiceClone:
    """Tests for TaskService.clone() method."""

    def test_clone_task(self, task_service: TaskService, mock_client: MagicMock):
        """Clone creates copy of task."""
        cloned_uuid = "cccccccc-dddd-eeee-ffff-111111111111"
        clone_response = Element("clone_task_response", {"status": "201", "id": cloned_uuid})

        task_xml = _create_task_xml(task_id=cloned_uuid, name="Test Task Clone")
        get_response = _create_get_task_response(task_xml)

        mock_client.execute.side_effect = [clone_response, get_response]

        task = task_service.clone("12345678-1234-1234-1234-123456789abc")

        assert task.id == cloned_uuid
