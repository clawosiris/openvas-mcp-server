# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG


from typing import TYPE_CHECKING, Any

from src.services.compliance import ComplianceService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_compliance_tools(server: FastMCP, service: ComplianceService) -> None:
    @server.tool(name="openvas_list_compliance_policies")
    def list_compliance_policies() -> dict[str, Any]:
        return service.list_policies().model_dump()

    @server.tool(name="openvas_list_compliance_audits")
    def list_compliance_audits(filter: str = "") -> dict[str, Any]:
        items = service.list_audits(filter)
        return {"items": items, "total": len(items)}

    @server.tool(name="openvas_get_compliance_audit")
    def get_compliance_audit(audit_id: str) -> dict[str, Any]:
        return service.get_audit(audit_id)

    @server.tool(name="openvas_start_compliance_audit")
    def start_compliance_audit(audit_id: str) -> dict[str, Any]:
        return {"audit_id": audit_id, "report_id": service.start_audit(audit_id)}

    @server.tool(name="openvas_stop_compliance_audit")
    def stop_compliance_audit(audit_id: str) -> dict[str, Any]:
        return {"audit_id": audit_id, "success": service.stop_audit(audit_id)}

    @server.tool(name="openvas_get_compliance_status")
    def get_compliance_status(target_id: str) -> dict[str, Any]:
        return service.get_compliance_status(target_id).model_dump()
