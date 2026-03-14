# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Report domain models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ReportFormat(str, Enum):
    """Report export formats."""

    XML = "xml"
    PDF = "pdf"
    CSV = "csv"
    TXT = "txt"
    HTML = "html"
    ITG = "itg"
    VERINICE_ITG = "verinice-itg"
    VERINICE_ISM = "verinice-ism"


class SeverityLevel(str, Enum):
    """Vulnerability severity levels."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    LOG = "Log"
    FALSE_POSITIVE = "False Positive"


class SeverityCount(BaseModel):
    """Count of vulnerabilities by severity."""

    high: int = Field(default=0, description="High severity count")
    medium: int = Field(default=0, description="Medium severity count")
    low: int = Field(default=0, description="Low severity count")
    log: int = Field(default=0, description="Log/info count")
    false_positive: int = Field(default=0, description="False positive count")

    @property
    def total(self) -> int:
        """Total vulnerability count (excluding false positives and logs)."""
        return self.high + self.medium + self.low


class TaskRef(BaseModel):
    """Task reference in report."""

    id: str
    name: str


class Vulnerability(BaseModel):
    """Vulnerability finding in a report."""

    id: str = Field(description="Result UUID")
    name: str = Field(description="Vulnerability name")
    host: str = Field(description="Affected host IP/hostname")
    port: str = Field(default="", description="Affected port")
    severity: float = Field(description="CVSS severity score (0-10)")
    severity_level: SeverityLevel = Field(description="Severity classification")
    qod: int = Field(default=0, description="Quality of Detection (0-100)")
    description: str = Field(default="", description="Vulnerability description")
    solution: str = Field(default="", description="Recommended solution")
    nvt_oid: str = Field(default="", description="NVT OID")
    cve: list[str] = Field(default_factory=list, description="Associated CVEs")


class ReportSummary(BaseModel):
    """Summary statistics for a report."""

    hosts_count: int = Field(default=0, description="Number of hosts scanned")
    hosts_alive: int = Field(default=0, description="Number of hosts responding")
    vulnerabilities: SeverityCount = Field(
        default_factory=SeverityCount, description="Vulnerability counts by severity"
    )
    scan_start: datetime | None = Field(default=None, description="Scan start time")
    scan_end: datetime | None = Field(default=None, description="Scan end time")
    scan_duration_seconds: int | None = Field(default=None, description="Scan duration")


class Report(BaseModel):
    """Report domain model.

    Represents a scan report in GVM.
    """

    id: str = Field(description="Report UUID")
    task: TaskRef | None = Field(default=None, description="Associated task")
    scan_start: datetime | None = Field(default=None, description="Scan start time")
    scan_end: datetime | None = Field(default=None, description="Scan end time")
    timestamp: datetime | None = Field(default=None, description="Report timestamp")
    summary: ReportSummary = Field(default_factory=ReportSummary, description="Report summary")
    creation_time: datetime | None = Field(default=None, description="Creation timestamp")
    modification_time: datetime | None = Field(
        default=None, description="Last modification timestamp"
    )


class ReportListResponse(BaseModel):
    """Response model for listing reports."""

    reports: list[Report] = Field(description="List of reports")
    total: int = Field(description="Total number of reports matching filter")
    filtered: int = Field(description="Number of reports in this response")


class ReportDetail(BaseModel):
    """Detailed report with vulnerabilities."""

    report: Report = Field(description="Report metadata")
    vulnerabilities: list[Vulnerability] = Field(
        default_factory=list, description="List of vulnerability findings"
    )
    hosts: list[str] = Field(default_factory=list, description="Scanned hosts")
