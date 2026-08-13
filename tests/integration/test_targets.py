# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

from uuid import uuid4

import pytest

from src.errors import ResourceNotFoundError
from src.services.targets import TargetCreateRequest, TargetService

pytestmark = pytest.mark.integration


def _make_target_request() -> TargetCreateRequest:
    suffix = uuid4().hex[:8]
    return TargetCreateRequest(
        name=f"integration-target-{suffix}",
        hosts=["127.0.0.1", "192.0.2.10"],
        comment="integration target",
    )


def test_create_target(target_service: TargetService) -> None:
    target = target_service.create(_make_target_request())

    try:
        assert target.id
        assert target.name.startswith("integration-target-")
        assert "127.0.0.1" in target.hosts
        assert "192.0.2.10" in target.hosts
    finally:
        target_service.delete(target.id, ultimate=True)


def test_list_targets(target_service: TargetService) -> None:
    target = target_service.create(_make_target_request())

    try:
        result = target_service.list()
        assert any(item.id == target.id for item in result.targets)
    finally:
        target_service.delete(target.id, ultimate=True)


def test_get_target(target_service: TargetService) -> None:
    target = target_service.create(_make_target_request())

    try:
        fetched = target_service.get(target.id)
        assert fetched.id == target.id
        assert fetched.name == target.name
        assert fetched.hosts == target.hosts
    finally:
        target_service.delete(target.id, ultimate=True)


def test_delete_target(target_service: TargetService) -> None:
    target = target_service.create(_make_target_request())

    assert target_service.delete(target.id, ultimate=True) is True
    with pytest.raises(ResourceNotFoundError):
        target_service.get(target.id)
