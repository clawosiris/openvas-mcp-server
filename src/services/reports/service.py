# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Report service implementation."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from src.errors import ResourceNotFoundError
from src.utils import (
    attr,
    response_ok,
    text,
    to_datetime,
    to_float,
    to_int,
    validate_filter,
    validate_uuid,
)

from .models import (
    Report,
    ReportDetail,
    ReportFormat,
    ReportListResponse,
    ReportSummary,
    SeverityCount,
    SeverityLevel,
    TaskRef,
    Vulnerability,
)

if TYPE_CHECKING:
    from src.infrastructure.client import GvmClient


class ReportService:
    """Service for managing scan reports.

    Provides operations for viewing, exporting, and analyzing reports.
    """

    def __init__(self, client: GvmClient) -> None:
        """Initialize report service.

        Args:
            client: GVM client for executing GMP operations.
        """
        self._client = client

    def get(self, report_id: str) -> Report:
        """Get a report by ID.

        Args:
            report_id: Report UUID.

        Returns:
            Report metadata.

        Raises:
            InvalidUuidError: If report_id is not a valid UUID.
            ResourceNotFoundError: If report doesn't exist.
        """
        report_id = validate_uuid(report_id, "report_id")

        def operation(gmp: Any) -> Any:
            return gmp.get_report(
                report_id=report_id,
                ignore_pagination=True,
                details=False,
            )

        response: Element = self._client.execute(operation)

        if not response_ok(response):
            raise ResourceNotFoundError("report", report_id)

        report_elem = response.find("report")
        if report_elem is None:
            raise ResourceNotFoundError("report", report_id)

        # Handle nested report element
        inner_report = report_elem.find("report")
        if inner_report is not None:
            report_elem = inner_report

        return self._parse_report(report_elem)

    def get_detail(self, report_id: str, min_qod: int = 70) -> ReportDetail:
        """Get detailed report with vulnerabilities.

        Args:
            report_id: Report UUID.
            min_qod: Minimum Quality of Detection threshold (0-100).

        Returns:
            Detailed report with vulnerability list.

        Raises:
            InvalidUuidError: If report_id is not a valid UUID.
            ResourceNotFoundError: If report doesn't exist.
        """
        report_id = validate_uuid(report_id, "report_id")

        def operation(gmp: Any) -> Any:
            return gmp.get_report(
                report_id=report_id,
                ignore_pagination=True,
                details=True,
                filter_string=f"min_qod={min_qod}",
            )

        response: Element = self._client.execute(operation)

        if not response_ok(response):
            raise ResourceNotFoundError("report", report_id)

        report_elem = response.find("report")
        if report_elem is None:
            raise ResourceNotFoundError("report", report_id)

        # Handle nested report element
        inner_report = report_elem.find("report")
        if inner_report is not None:
            report_elem = inner_report

        report = self._parse_report(report_elem)
        vulnerabilities = self._parse_vulnerabilities(report_elem)
        hosts = self._parse_hosts(report_elem)

        return ReportDetail(
            report=report,
            vulnerabilities=vulnerabilities,
            hosts=hosts,
        )

    def list(self, filter_string: str = "") -> ReportListResponse:
        """List reports with optional filter.

        Args:
            filter_string: GMP filter string.

        Returns:
            List of reports with pagination info.

        Raises:
            InvalidFilterError: If filter contains invalid characters.
        """
        filter_string = validate_filter(filter_string)

        def operation(gmp: Any) -> Any:
            return gmp.get_reports(
                filter_string=filter_string or None,
                ignore_pagination=True,
                details=False,
            )

        response: Element = self._client.execute(operation)

        reports = []
        for report_elem in response.findall("report"):
            # Handle nested report element
            inner_report = report_elem.find("report")
            if inner_report is not None:
                report_elem = inner_report
            reports.append(self._parse_report(report_elem))

        return ReportListResponse(
            reports=reports,
            total=len(reports),
            filtered=len(reports),
        )

    def delete(self, report_id: str) -> bool:
        """Delete a report.

        Args:
            report_id: Report UUID.

        Returns:
            True if deleted successfully.

        Raises:
            InvalidUuidError: If report_id is not a valid UUID.
            ResourceNotFoundError: If report doesn't exist.
        """
        report_id = validate_uuid(report_id, "report_id")

        def operation(gmp: Any) -> Any:
            return gmp.delete_report(report_id=report_id)

        response: Element = self._client.execute(operation)

        status = attr(response, "status")
        if status == "404":
            raise ResourceNotFoundError("report", report_id)

        return response_ok(response)

    def export(
        self,
        report_id: str,
        report_format: ReportFormat = ReportFormat.PDF,
    ) -> bytes:
        """Export a report in specified format.

        Args:
            report_id: Report UUID.
            report_format: Export format (PDF, CSV, XML, etc.).

        Returns:
            Report content as bytes.

        Raises:
            InvalidUuidError: If report_id is not a valid UUID.
            ResourceNotFoundError: If report doesn't exist.
        """
        report_id = validate_uuid(report_id, "report_id")

        # Get report format ID
        format_id = self._get_report_format_id(report_format)

        def operation(gmp: Any) -> Any:
            return gmp.get_report(
                report_id=report_id,
                report_format_id=format_id,
                ignore_pagination=True,
                details=True,
            )

        response: Element = self._client.execute(operation)

        if not response_ok(response):
            raise ResourceNotFoundError("report", report_id)

        # Extract report data
        report_elem = response.find("report")
        if report_elem is None:
            raise ResourceNotFoundError("report", report_id)

        # The actual report content may be base64 encoded or in different locations
        # depending on format and GVM version
        import base64

        # Try to find the report content
        content = report_elem.text or ""

        # If it looks like base64, decode it
        try:
            return base64.b64decode(content)
        except Exception:
            return content.encode("utf-8")

    def get_summary(self, report_id: str) -> ReportSummary:
        """Get report summary statistics.

        Args:
            report_id: Report UUID.

        Returns:
            Summary statistics for the report.
        """
        report = self.get(report_id)
        return report.summary

    def _parse_report(self, elem: Element) -> Report:
        """Parse report XML element into Report model."""
        # Parse task reference
        task = None
        task_elem = elem.find("task")
        if task_elem is not None:
            task_id = attr(task_elem, "id")
            if task_id:
                task = TaskRef(
                    id=task_id,
                    name=text(task_elem, "name"),
                )

        # Parse timestamps
        scan_start = to_datetime(text(elem, "scan_start"))
        scan_end = to_datetime(text(elem, "scan_end"))
        timestamp = to_datetime(text(elem, "timestamp"))
        creation_time = to_datetime(text(elem, "creation_time"))
        modification_time = to_datetime(text(elem, "modification_time"))

        # Parse summary
        summary = self._parse_summary(elem, scan_start, scan_end)

        return Report(
            id=attr(elem, "id"),
            task=task,
            scan_start=scan_start,
            scan_end=scan_end,
            timestamp=timestamp,
            summary=summary,
            creation_time=creation_time,
            modification_time=modification_time,
        )

    def _parse_summary(
        self,
        elem: Element,
        scan_start: Any,
        scan_end: Any,
    ) -> ReportSummary:
        """Parse report summary from XML."""
        # Parse host counts
        hosts_elem = elem.find("hosts")
        hosts_count = to_int(text(hosts_elem, "count") if hosts_elem is not None else "", 0)

        host_elem = elem.find("host_count")
        if host_elem is not None:
            hosts_count = to_int(host_elem.text, hosts_count)

        # Parse severity counts
        severity = SeverityCount()

        # Try different XML structures for severity counts
        result_count_elem = elem.find("result_count")
        if result_count_elem is not None:
            severity = SeverityCount(
                high=to_int(text(result_count_elem, "high"), 0),
                medium=to_int(text(result_count_elem, "medium"), 0),
                low=to_int(text(result_count_elem, "low"), 0),
                log=to_int(text(result_count_elem, "log"), 0),
                false_positive=to_int(text(result_count_elem, "false_positive"), 0),
            )
        else:
            # Alternative: look in severity element
            severity_elem = elem.find("severity")
            if severity_elem is not None:
                # Parse from filtered counts
                severity = SeverityCount(
                    high=to_int(text(severity_elem, "filtered"), 0),
                )

        # Calculate duration
        duration = None
        if scan_start and scan_end:
            duration = int((scan_end - scan_start).total_seconds())

        return ReportSummary(
            hosts_count=hosts_count,
            hosts_alive=hosts_count,  # Approximation
            vulnerabilities=severity,
            scan_start=scan_start,
            scan_end=scan_end,
            scan_duration_seconds=duration,
        )

    def _parse_vulnerabilities(self, elem: Element) -> builtins.list[Vulnerability]:
        """Parse vulnerability results from report."""
        vulnerabilities = []

        for result in elem.findall(".//result"):
            # Parse severity
            severity_str = text(result, "severity")
            severity = to_float(severity_str, 0.0)
            severity_level = self._severity_to_level(severity)

            # Parse CVEs
            cves = []
            for ref in result.findall(".//ref[@type='cve']"):
                cve_id = attr(ref, "id")
                if cve_id:
                    cves.append(cve_id)

            nvt_elem = result.find("nvt")
            nvt_oid = attr(nvt_elem, "oid") if nvt_elem is not None else ""

            vuln = Vulnerability(
                id=attr(result, "id"),
                name=text(result, "name"),
                host=text(result, "host"),
                port=text(result, "port"),
                severity=severity,
                severity_level=severity_level,
                qod=to_int(text(result, "qod/value"), 0),
                description=text(result, "description"),
                solution=text(result, "solution"),
                nvt_oid=nvt_oid,
                cve=cves,
            )
            vulnerabilities.append(vuln)

        return vulnerabilities

    def _parse_hosts(self, elem: Element) -> builtins.list[str]:
        """Parse host list from report."""
        hosts = []
        for host in elem.findall(".//host"):
            # Try getting IP from different locations
            ip = host.text or text(host, "ip") or attr(host, "ip")
            if ip:
                hosts.append(ip.strip())
        return list(set(hosts))  # Deduplicate

    def _severity_to_level(self, severity: float) -> SeverityLevel:
        """Convert CVSS score to severity level."""
        if severity >= 7.0:
            return SeverityLevel.HIGH
        elif severity >= 4.0:
            return SeverityLevel.MEDIUM
        elif severity > 0:
            return SeverityLevel.LOW
        else:
            return SeverityLevel.LOG

    def _get_report_format_id(self, report_format: ReportFormat) -> str:
        """Get GVM report format UUID for given format type.

        These are the default report format UUIDs in GVM.
        """
        format_ids = {
            ReportFormat.XML: "a994b278-1f62-11e1-96ac-406186ea4fc5",
            ReportFormat.PDF: "c402cc3e-b531-11e1-9163-406186ea4fc5",
            ReportFormat.CSV: "c1645568-627a-11e3-a660-406186ea4fc5",
            ReportFormat.TXT: "a3810a62-1f62-11e1-9219-406186ea4fc5",
            ReportFormat.HTML: "6c248850-1f62-11e1-b082-406186ea4fc5",
            ReportFormat.ITG: "77bd6c4a-1f62-11e1-abf0-406186ea4fc5",
            ReportFormat.VERINICE_ITG: "7c9ac5c0-1f62-11e1-86bf-406186ea4fc5",
            ReportFormat.VERINICE_ISM: "50c9950a-f326-11e4-800c-28d24461215b",
        }
        return format_ids.get(report_format, format_ids[ReportFormat.PDF])
