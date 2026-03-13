"""Vulnerability service implementation."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from src.utils import attr, text, to_float, to_int, validate_filter, validate_uuid

from .models import NvtInfo, VulnerabilityFinding, VulnerabilityListResponse

if TYPE_CHECKING:
    from src.infrastructure.client import GvmClient


class VulnerabilityService:
    """Service for vulnerability findings and NVT search."""

    def __init__(self, client: GvmClient) -> None:
        self._client = client

    def list(self, report_id: str, min_qod: int = 70) -> VulnerabilityListResponse:
        """List vulnerability findings for a report."""
        report_id = validate_uuid(report_id, "report_id")

        def operation(gmp: Any) -> Any:
            return gmp.get_report(
                report_id=report_id,
                details=True,
                ignore_pagination=True,
                filter_string=f"min_qod={min_qod}",
            )

        response: Element = self._client.execute(operation)

        findings: list[VulnerabilityFinding] = []
        for result in response.findall(".//result"):
            findings.append(self._parse_result(result))

        return VulnerabilityListResponse(
            findings=findings,
            total=len(findings),
            filtered=len(findings),
        )

    def search_nvts(self, query: str) -> builtins.list[NvtInfo]:
        """Search NVTs using GMP filter syntax."""
        query = validate_filter(query)

        def operation(gmp: Any) -> Any:
            filter_string = f"name~{query}" if query else None
            return gmp.get_nvts(filter_string=filter_string)

        response: Element = self._client.execute(operation)

        nvts: builtins.list[NvtInfo] = []
        for nvt in response.findall("nvt"):
            nvts.append(
                NvtInfo(
                    oid=attr(nvt, "oid"),
                    name=text(nvt, "name"),
                    family=text(nvt, "family"),
                    cvss_base=to_float(text(nvt, "cvss_base"), 0.0),
                    tags=text(nvt, "tags"),
                )
            )

        return nvts

    def _parse_result(self, result: Element) -> VulnerabilityFinding:
        cves: list[str] = []
        for ref in result.findall(".//ref[@type='cve']"):
            cve = attr(ref, "id")
            if cve:
                cves.append(cve)

        nvt = result.find("nvt")

        return VulnerabilityFinding(
            id=attr(result, "id"),
            name=text(result, "name"),
            host=text(result, "host"),
            port=text(result, "port"),
            severity=to_float(text(result, "severity"), 0.0),
            qod=to_int(text(result, "qod/value"), 0),
            nvt_oid=attr(nvt, "oid") if nvt is not None else "",
            cves=cves,
        )
