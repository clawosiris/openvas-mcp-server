# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

import pytest

from src.services.compliance import ComplianceService

pytestmark = pytest.mark.integration


def test_list_policies(compliance_service: ComplianceService) -> None:
    """List compliance policies (mock server may return empty list)."""
    result = compliance_service.list_policies()
    # Just verify the call succeeds and returns a valid response
    assert result is not None
    assert hasattr(result, "policies")


def test_list_audits(compliance_service: ComplianceService) -> None:
    """List compliance audits (mock server may return empty list)."""
    result = compliance_service.list_audits()
    assert isinstance(result, list)


def test_get_audit(compliance_service: ComplianceService, audit_id: str) -> None:
    """Get a specific audit by ID."""
    audit = compliance_service.get_audit(audit_id)
    assert audit is not None
    assert "id" in audit or audit.get("id") == audit_id
