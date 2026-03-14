# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""MCP tools for report management."""

import base64
from typing import Any

from mcp.server.fastmcp import FastMCP

from src.services.reports import ReportFormat, ReportService


def register_report_tools(server: FastMCP, service: ReportService) -> None:
    """Register report management tools with MCP server.

    Args:
        server: FastMCP server instance.
        service: Report service instance.
    """

    @server.tool(structured_output=False, name="openvas_list_reports")
    def list_reports(filter: str = "") -> dict[str, Any]:
        """List all scan reports.

        Args:
            filter: Optional GMP filter string.

        Returns:
            List of reports with summary info.
        """
        result = service.list(filter)
        return result.model_dump()

    @server.tool(structured_output=False, name="openvas_get_report")
    def get_report(report_id: str) -> dict[str, Any]:
        """Get report metadata by ID.

        Args:
            report_id: Report UUID.

        Returns:
            Report metadata and summary statistics.
        """
        result = service.get(report_id)
        return result.model_dump()

    @server.tool(structured_output=False, name="openvas_get_report_detail")
    def get_report_detail(report_id: str, min_qod: int = 70) -> dict[str, Any]:
        """Get detailed report with all vulnerabilities.

        Args:
            report_id: Report UUID.
            min_qod: Minimum Quality of Detection (0-100). Default 70.

        Returns:
            Full report with vulnerability list, hosts, and statistics.
        """
        result = service.get_detail(report_id, min_qod=min_qod)
        return result.model_dump()

    @server.tool(structured_output=False, name="openvas_get_report_summary")
    def get_report_summary(report_id: str) -> dict[str, Any]:
        """Get report summary statistics.

        Args:
            report_id: Report UUID.

        Returns:
            Summary with host counts, vulnerability counts by severity,
            and scan duration.
        """
        result = service.get_summary(report_id)
        return result.model_dump()

    @server.tool(structured_output=False, name="openvas_export_report")
    def export_report(
        report_id: str,
        format: str = "pdf",
    ) -> dict[str, Any]:
        """Export report in specified format.

        Args:
            report_id: Report UUID.
            format: Export format (pdf, csv, xml, txt, html). Default: pdf.

        Returns:
            Base64 encoded report content with metadata.
        """
        # Parse format
        try:
            report_format = ReportFormat(format.lower())
        except ValueError:
            report_format = ReportFormat.PDF

        content = service.export(report_id, report_format=report_format)

        return {
            "report_id": report_id,
            "format": report_format.value,
            "content_base64": base64.b64encode(content).decode("utf-8"),
            "size_bytes": len(content),
        }

    @server.tool(structured_output=False, name="openvas_delete_report")
    def delete_report(report_id: str) -> dict[str, Any]:
        """Delete a report.

        Args:
            report_id: Report UUID to delete.

        Returns:
            Success status.
        """
        success = service.delete(report_id)
        return {"report_id": report_id, "success": success}
