# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from src.errors import ResourceNotFoundError
from src.utils import attr, collect, response_ok, text, to_int, validate_filter, validate_uuid

from .models import ComplianceStatus, Policy, PolicyListResponse

if TYPE_CHECKING:
    from src.infrastructure.client import GvmClient


class ComplianceService:
    def __init__(self, client: GvmClient) -> None:
        self._client = client

    def list_policies(self) -> PolicyListResponse:
        def operation(gmp: Any) -> Any:
            return gmp.get_scan_configs(filter_string="usage_type=policy")

        response: Element = self._client.execute(operation)
        policies = collect(response, "config", self._parse_policy)
        return PolicyListResponse(policies=policies, total=len(policies))

    def list_audits(self, filter_string: str = "") -> list[dict[str, str]]:
        filter_string = validate_filter(filter_string)

        def operation(gmp: Any) -> Any:
            return gmp.get_tasks(filter_string=filter_string or None)

        response: Element = self._client.execute(operation)
        audits: list[dict[str, str]] = []
        for task in response.findall("task"):
            audits.append(
                {
                    "id": attr(task, "id"),
                    "name": text(task, "name"),
                    "status": text(task, "status"),
                }
            )
        return audits

    def get_audit(self, audit_id: str) -> dict[str, str]:
        audit_id = validate_uuid(audit_id, "audit_id")

        def operation(gmp: Any) -> Any:
            return gmp.get_task(task_id=audit_id)

        response: Element = self._client.execute(operation)
        if not response_ok(response):
            raise ResourceNotFoundError("audit", audit_id)
        task = response.find("task")
        if task is None:
            raise ResourceNotFoundError("audit", audit_id)
        return {"id": attr(task, "id"), "name": text(task, "name"), "status": text(task, "status")}

    def start_audit(self, audit_id: str) -> str:
        audit_id = validate_uuid(audit_id, "audit_id")

        def operation(gmp: Any) -> Any:
            return gmp.start_task(task_id=audit_id)

        response: Element = self._client.execute(operation)
        return text(response, "report_id")

    def stop_audit(self, audit_id: str) -> bool:
        audit_id = validate_uuid(audit_id, "audit_id")

        def operation(gmp: Any) -> Any:
            return gmp.stop_task(task_id=audit_id)

        response: Element = self._client.execute(operation)
        return response_ok(response)

    def get_compliance_status(self, target_id: str) -> ComplianceStatus:
        target_id = validate_uuid(target_id, "target_id")

        def operation(gmp: Any) -> Any:
            return gmp.get_results(filter_string=f"target_id={target_id}")

        response: Element = self._client.execute(operation)
        passed = to_int(text(response, "result_count/log"), 0)
        failed = to_int(text(response, "result_count/high"), 0) + to_int(
            text(response, "result_count/medium"),
            0,
        )
        return ComplianceStatus(
            target_id=target_id, compliant=failed == 0, passed=passed, failed=failed
        )

    def _parse_policy(self, elem: Element) -> Policy:
        return Policy(id=attr(elem, "id"), name=text(elem, "name"))
