# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Scan config service module."""

from .models import ScanConfig, ScanConfigListResponse
from .service import ScanConfigService

__all__ = ["ScanConfig", "ScanConfigListResponse", "ScanConfigService"]
