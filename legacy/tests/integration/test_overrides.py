# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

from uuid import uuid4

import pytest

from src.errors import ResourceNotFoundError
from src.services.overrides import OverrideService

pytestmark = pytest.mark.integration

TEST_NVT_OID = "1.3.6.1.4.1.25623.1.0.100000"


def _make_override_text() -> str:
    return f"integration-override-{uuid4().hex[:8]}"


def test_create_override(override_service: OverrideService) -> None:
    override = override_service.create(_make_override_text(), nvt_oid=TEST_NVT_OID)

    try:
        assert override.id
        assert override.text.startswith("integration-override-")
    finally:
        override_service.delete(override.id)


def test_list_overrides(override_service: OverrideService) -> None:
    override = override_service.create(_make_override_text(), nvt_oid=TEST_NVT_OID)

    try:
        result = override_service.list()
        assert any(item.id == override.id for item in result.overrides)
    finally:
        override_service.delete(override.id)


def test_delete_override(override_service: OverrideService) -> None:
    override = override_service.create(_make_override_text(), nvt_oid=TEST_NVT_OID)

    assert override_service.delete(override.id) is True
    with pytest.raises(ResourceNotFoundError):
        override_service.get(override.id)
