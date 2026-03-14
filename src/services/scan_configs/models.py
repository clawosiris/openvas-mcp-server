# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Scan config domain models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ScanConfig(BaseModel):
    """Scan configuration model."""

    id: str = Field(description="Scan config UUID")
    name: str = Field(description="Config name")
    family_count: int = Field(default=0, description="NVT family count")
    nvt_count: int = Field(default=0, description="NVT count")
    comment: str = Field(default="", description="Optional description")


class ScanConfigListResponse(BaseModel):
    """Response model for scan config list."""

    scan_configs: list[ScanConfig] = Field(description="List of scan configs")
    total: int = Field(description="Total number of scan configs")
    filtered: int = Field(description="Number returned in response")
