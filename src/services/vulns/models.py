"""Vulnerability domain models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class VulnerabilityFinding(BaseModel):
    """A vulnerability finding from report results."""

    id: str = Field(description="Result UUID")
    name: str = Field(description="Vulnerability name")
    host: str = Field(default="", description="Affected host")
    port: str = Field(default="", description="Affected port")
    severity: float = Field(default=0.0, description="CVSS severity")
    qod: int = Field(default=0, description="Quality of Detection")
    nvt_oid: str = Field(default="", description="NVT OID")
    cves: list[str] = Field(default_factory=list, description="Associated CVEs")


class VulnerabilityListResponse(BaseModel):
    """List response for vulnerability findings."""

    findings: list[VulnerabilityFinding] = Field(default_factory=list)
    total: int = Field(description="Total findings")
    filtered: int = Field(description="Returned findings")


class NvtInfo(BaseModel):
    """NVT metadata model."""

    oid: str = Field(description="NVT OID")
    name: str = Field(description="NVT name")
    family: str = Field(default="", description="NVT family")
    cvss_base: float = Field(default=0.0, description="Base CVSS")
    tags: str = Field(default="", description="NVT tags")
