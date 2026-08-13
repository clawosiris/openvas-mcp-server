# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

import pytest

from src.services.vulns import VulnerabilityService

pytestmark = pytest.mark.integration


def test_list_vulns(vuln_service: VulnerabilityService, report_id: str) -> None:
    """List vulnerabilities from a report."""
    result = vuln_service.list(report_id)
    # Just verify the call succeeds and returns a valid response
    assert result is not None
    assert hasattr(result, "vulnerabilities")


def test_search_nvts(vuln_service: VulnerabilityService) -> None:
    """Search NVT database."""
    # Search for a common term that should return results
    results = vuln_service.search_nvts("ssh")
    # Mock server may not have NVT data, just verify the call works
    assert isinstance(results, list)
