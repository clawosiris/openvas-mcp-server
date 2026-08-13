# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Tests for report service."""

from unittest.mock import MagicMock
from xml.etree.ElementTree import Element, SubElement

import pytest

from src.errors import ResourceNotFoundError
from src.services.reports import ReportService
from src.utils import InvalidUuidError


@pytest.fixture
def mock_client() -> MagicMock:
    """Create mock GVM client."""
    return MagicMock()


@pytest.fixture
def report_service(mock_client: MagicMock) -> ReportService:
    """Create report service with mock client."""
    return ReportService(mock_client)


def _create_report_xml(
    report_id: str = "12345678-1234-1234-1234-123456789abc",
    task_name: str = "Test Task",
    high: int = 5,
    medium: int = 10,
    low: int = 20,
) -> Element:
    """Create a report XML element for testing."""
    report = Element("report", {"id": report_id})
    SubElement(report, "scan_start").text = "2024-01-15T10:00:00Z"
    SubElement(report, "scan_end").text = "2024-01-15T11:30:00Z"
    SubElement(report, "timestamp").text = "2024-01-15T11:30:00Z"
    SubElement(report, "creation_time").text = "2024-01-15T11:30:00Z"

    # Add task
    task = SubElement(report, "task", {"id": "task-uuid-1234"})
    SubElement(task, "name").text = task_name

    # Add result counts
    result_count = SubElement(report, "result_count")
    SubElement(result_count, "high").text = str(high)
    SubElement(result_count, "medium").text = str(medium)
    SubElement(result_count, "low").text = str(low)
    SubElement(result_count, "log").text = "50"
    SubElement(result_count, "false_positive").text = "2"

    # Add host count
    SubElement(report, "host_count").text = "10"

    return report


def _create_get_report_response(report: Element) -> Element:
    """Wrap report in get_report response."""
    response = Element("get_reports_response", {"status": "200", "status_text": "OK"})
    response.append(report)
    return response


def _create_reports_response(reports: list[Element]) -> Element:
    """Create get_reports response."""
    response = Element("get_reports_response", {"status": "200", "status_text": "OK"})
    for report in reports:
        response.append(report)
    return response


class TestReportServiceGet:
    """Tests for ReportService.get() method."""

    def test_get_existing_report(self, report_service: ReportService, mock_client: MagicMock):
        """Get returns report when it exists."""
        report_xml = _create_report_xml()
        response = _create_get_report_response(report_xml)
        mock_client.execute.return_value = response

        report = report_service.get("12345678-1234-1234-1234-123456789abc")

        assert report.id == "12345678-1234-1234-1234-123456789abc"
        assert report.task is not None
        assert report.task.name == "Test Task"
        assert report.summary.vulnerabilities.high == 5
        assert report.summary.vulnerabilities.medium == 10

    def test_get_invalid_uuid(self, report_service: ReportService):
        """Get raises InvalidUuidError for invalid UUID."""
        with pytest.raises(InvalidUuidError):
            report_service.get("not-a-valid-uuid")

    def test_get_nonexistent_report(self, report_service: ReportService, mock_client: MagicMock):
        """Get raises ResourceNotFoundError when report doesn't exist."""
        response = Element("get_reports_response", {"status": "404", "status_text": "Not Found"})
        mock_client.execute.return_value = response

        with pytest.raises(ResourceNotFoundError) as exc_info:
            report_service.get("12345678-1234-1234-1234-123456789abc")

        assert exc_info.value.details.resource_type == "report"


class TestReportServiceList:
    """Tests for ReportService.list() method."""

    def test_list_returns_reports(self, report_service: ReportService, mock_client: MagicMock):
        """List returns all reports."""
        report1 = _create_report_xml(report_id="uuid-1", task_name="Task 1")
        report2 = _create_report_xml(report_id="uuid-2", task_name="Task 2")
        response = _create_reports_response([report1, report2])
        mock_client.execute.return_value = response

        result = report_service.list()

        assert len(result.reports) == 2
        assert result.reports[0].task.name == "Task 1"
        assert result.reports[1].task.name == "Task 2"

    def test_list_empty(self, report_service: ReportService, mock_client: MagicMock):
        """List returns empty list when no reports."""
        response = _create_reports_response([])
        mock_client.execute.return_value = response

        result = report_service.list()

        assert result.reports == []
        assert result.filtered == 0


class TestReportServiceDelete:
    """Tests for ReportService.delete() method."""

    def test_delete_report(self, report_service: ReportService, mock_client: MagicMock):
        """Delete returns True on success."""
        response = Element("delete_report_response", {"status": "200", "status_text": "OK"})
        mock_client.execute.return_value = response

        result = report_service.delete("12345678-1234-1234-1234-123456789abc")

        assert result is True

    def test_delete_nonexistent(self, report_service: ReportService, mock_client: MagicMock):
        """Delete raises ResourceNotFoundError for nonexistent report."""
        response = Element("delete_report_response", {"status": "404", "status_text": "Not Found"})
        mock_client.execute.return_value = response

        with pytest.raises(ResourceNotFoundError):
            report_service.delete("12345678-1234-1234-1234-123456789abc")


class TestReportServiceExport:
    """Tests for ReportService.export() method."""

    def test_export_pdf(self, report_service: ReportService, mock_client: MagicMock):
        """Export returns bytes content."""
        import base64

        pdf_content = b"%PDF-1.4 test content"
        encoded = base64.b64encode(pdf_content).decode()

        report_xml = Element("report", {"id": "test-uuid"})
        report_xml.text = encoded
        response = _create_get_report_response(report_xml)
        mock_client.execute.return_value = response

        content = report_service.export("12345678-1234-1234-1234-123456789abc")

        assert isinstance(content, bytes)
        assert content == pdf_content


class TestReportServiceSummary:
    """Tests for ReportService.get_summary() method."""

    def test_get_summary(self, report_service: ReportService, mock_client: MagicMock):
        """Get summary returns statistics."""
        report_xml = _create_report_xml(high=3, medium=7, low=15)
        response = _create_get_report_response(report_xml)
        mock_client.execute.return_value = response

        summary = report_service.get_summary("12345678-1234-1234-1234-123456789abc")

        assert summary.vulnerabilities.high == 3
        assert summary.vulnerabilities.medium == 7
        assert summary.vulnerabilities.low == 15
        assert summary.vulnerabilities.total == 25
        assert summary.hosts_count == 10
