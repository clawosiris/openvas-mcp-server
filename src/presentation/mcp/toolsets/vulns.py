"""MCP tools for vulnerability operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.services.vulns import VulnerabilityService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_vuln_tools(server: FastMCP, service: VulnerabilityService) -> None:
    """Register vulnerability tools."""

    @server.tool(name="openvas_list_vulnerabilities")
    def list_vulnerabilities(report_id: str, min_qod: int = 70) -> dict[str, Any]:
        result = service.list(report_id=report_id, min_qod=min_qod)
        return result.model_dump()

    @server.tool(name="openvas_search_nvts")
    def search_nvts(query: str) -> dict[str, Any]:
        result = service.search_nvts(query)
        return {"query": query, "results": [n.model_dump() for n in result], "total": len(result)}
