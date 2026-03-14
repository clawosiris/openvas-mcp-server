# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Tests for report models."""

from src.services.reports import (
    Report,
    ReportFormat,
    ReportListResponse,
    ReportSummary,
    SeverityCount,
    Vulnerability,
)
from src.services.reports.models import SeverityLevel, TaskRef


class TestSeverityCount:
    """Tests for SeverityCount model."""

    def test_default_values(self):
        """Default values are zero."""
        count = SeverityCount()
        assert count.high == 0
        assert count.medium == 0
        assert count.low == 0
        assert count.log == 0
        assert count.false_positive == 0

    def test_total_property(self):
        """Total excludes log and false positive."""
        count = SeverityCount(high=5, medium=10, low=20, log=100, false_positive=5)
        assert count.total == 35  # 5 + 10 + 20


class TestReportSummary:
    """Tests for ReportSummary model."""

    def test_default_values(self):
        """Default values are sensible."""
        summary = ReportSummary()
        assert summary.hosts_count == 0
        assert summary.vulnerabilities.total == 0

    def test_with_values(self):
        """Can create with all values."""
        summary = ReportSummary(
            hosts_count=10,
            hosts_alive=8,
            vulnerabilities=SeverityCount(high=5, medium=10, low=20),
            scan_duration_seconds=3600,
        )
        assert summary.hosts_count == 10
        assert summary.vulnerabilities.total == 35


class TestVulnerability:
    """Tests for Vulnerability model."""

    def test_minimal_vuln(self):
        """Vulnerability with minimal fields."""
        vuln = Vulnerability(
            id="vuln-uuid",
            name="Test Vuln",
            host="192.168.1.1",
            severity=7.5,
            severity_level=SeverityLevel.HIGH,
        )
        assert vuln.id == "vuln-uuid"
        assert vuln.severity == 7.5
        assert vuln.severity_level == SeverityLevel.HIGH
        assert vuln.cve == []

    def test_full_vuln(self):
        """Vulnerability with all fields."""
        vuln = Vulnerability(
            id="vuln-uuid",
            name="SQL Injection",
            host="192.168.1.1",
            port="443/tcp",
            severity=9.8,
            severity_level=SeverityLevel.HIGH,
            qod=95,
            description="SQL injection vulnerability found",
            solution="Update to latest version",
            nvt_oid="1.3.6.1.4.1.25623.1.0.12345",
            cve=["CVE-2024-1234", "CVE-2024-1235"],
        )
        assert vuln.port == "443/tcp"
        assert len(vuln.cve) == 2


class TestReport:
    """Tests for Report model."""

    def test_minimal_report(self):
        """Report with minimal fields."""
        report = Report(id="report-uuid")
        assert report.id == "report-uuid"
        assert report.task is None
        assert report.summary.vulnerabilities.total == 0

    def test_full_report(self):
        """Report with all fields."""
        report = Report(
            id="report-uuid",
            task=TaskRef(id="task-uuid", name="Scan Task"),
            summary=ReportSummary(
                hosts_count=5,
                vulnerabilities=SeverityCount(high=2, medium=5, low=10),
            ),
        )
        assert report.task.name == "Scan Task"
        assert report.summary.vulnerabilities.total == 17


class TestReportListResponse:
    """Tests for ReportListResponse model."""

    def test_empty_response(self):
        """Empty list response."""
        response = ReportListResponse(
            reports=[],
            total=0,
            filtered=0,
        )
        assert response.reports == []

    def test_with_reports(self):
        """Response with reports."""
        report = Report(id="uuid")
        response = ReportListResponse(
            reports=[report],
            total=10,
            filtered=1,
        )
        assert len(response.reports) == 1


class TestReportFormat:
    """Tests for ReportFormat enum."""

    def test_values(self):
        """All expected formats exist."""
        assert ReportFormat.PDF.value == "pdf"
        assert ReportFormat.CSV.value == "csv"
        assert ReportFormat.XML.value == "xml"
        assert ReportFormat.HTML.value == "html"

    def test_from_string(self):
        """Can create from string value."""
        fmt = ReportFormat("pdf")
        assert fmt == ReportFormat.PDF


class TestSeverityLevel:
    """Tests for SeverityLevel enum."""

    def test_values(self):
        """All expected levels exist."""
        assert SeverityLevel.HIGH.value == "High"
        assert SeverityLevel.MEDIUM.value == "Medium"
        assert SeverityLevel.LOW.value == "Low"
        assert SeverityLevel.LOG.value == "Log"
