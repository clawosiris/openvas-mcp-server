from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from gvm_mcp.connection import GvmConnectionManager


def _safe_int(value: object) -> int:
    try:
        return int(str(value))
    except (ValueError, TypeError):
        return 0


def register_extraction_tools(server: FastMCP, connection: GvmConnectionManager) -> None:
    @server.tool(name="gvm_extract_report_summary", structured_output=False)
    def extract_report_summary(report_id: str) -> dict[str, Any]:
        report = connection.execute(lambda gmp: gmp.get_report(report_id=report_id, details=True))

        result_nodes = report.findall(".//result")
        severity_values = []
        for node in result_nodes:
            sev = node.findtext("severity", default="0")
            try:
                severity_values.append(float(sev))
            except (ValueError, TypeError):
                severity_values.append(0.0)

        summary = {
            "report_id": report_id,
            "results_total": len(result_nodes),
            "severity": {
                "critical": sum(1 for s in severity_values if s >= 9.0),
                "high": sum(1 for s in severity_values if 7.0 <= s < 9.0),
                "medium": sum(1 for s in severity_values if 4.0 <= s < 7.0),
                "low": sum(1 for s in severity_values if 0.1 <= s < 4.0),
                "none": sum(1 for s in severity_values if s == 0.0),
            },
            "host_count": _safe_int(report.findtext(".//host_count", default="0")),
        }

        return summary
