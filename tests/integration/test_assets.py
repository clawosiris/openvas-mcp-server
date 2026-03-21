# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

import pytest

from src.services.assets import AssetService

pytestmark = pytest.mark.integration


def test_list_hosts(asset_service: AssetService) -> None:
    """List host assets (mock server may return empty list)."""
    result = asset_service.list_hosts()
    # Just verify the call succeeds and returns a valid response
    assert isinstance(result, list)


def test_list_os(asset_service: AssetService) -> None:
    """List OS assets (mock server may return empty list)."""
    result = asset_service.list_os()
    assert isinstance(result, list)


def test_list_tls_certificates(asset_service: AssetService) -> None:
    """List TLS certificate assets (mock server may return empty list)."""
    result = asset_service.list_tls_certificates()
    assert isinstance(result, list)
