# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

import pytest

from src.services.schedules import ScheduleService

pytestmark = pytest.mark.integration


def test_list_schedules(schedule_service: ScheduleService) -> None:
    """List schedules (mock server may return empty list)."""
    result = schedule_service.list()
    # Just verify the call succeeds and returns a valid response
    assert result is not None
    assert hasattr(result, "schedules")


def test_get_schedule(schedule_service: ScheduleService, schedule_id: str) -> None:
    """Get a specific schedule by ID."""
    schedule = schedule_service.get(schedule_id)
    assert schedule.id == schedule_id
