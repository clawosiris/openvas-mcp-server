# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

import pytest

from src.services.port_lists import PortListService

pytestmark = pytest.mark.integration


def test_list_port_lists(port_list_service: PortListService) -> None:
    """List port lists (mock server may return empty list)."""
    result = port_list_service.list()
    # Just verify the call succeeds and returns a valid response
    assert result is not None
    assert hasattr(result, "port_lists")


def test_get_port_list(port_list_service: PortListService, port_list_id: str) -> None:
    """Get a specific port list by ID."""
    port_list = port_list_service.get(port_list_id)
    assert port_list.id == port_list_id
    assert port_list.name
