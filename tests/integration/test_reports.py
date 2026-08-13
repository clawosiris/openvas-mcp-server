# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

import pytest

from src.services.reports import ReportService

pytestmark = pytest.mark.integration


def test_list_reports(report_service: ReportService) -> None:
    """List reports (mock server may return empty list)."""
    result = report_service.list()
    # Just verify the call succeeds and returns a valid response
    assert result is not None
    assert hasattr(result, "reports")


def test_get_report(report_service: ReportService, report_id: str) -> None:
    """Get a specific report by ID."""
    report = report_service.get(report_id)
    assert report.id == report_id


def test_get_report_detail(report_service: ReportService, report_id: str) -> None:
    """Get detailed report with vulnerabilities."""
    detail = report_service.get_detail(report_id)
    assert detail.id == report_id
    assert hasattr(detail, "results")


def test_get_report_summary(report_service: ReportService, report_id: str) -> None:
    """Get report summary with severity counts."""
    summary = report_service.get_summary(report_id)
    assert summary is not None
    assert hasattr(summary, "total")
