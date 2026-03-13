"""Schedule service implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from src.errors import ResourceNotFoundError
from src.utils import (
    attr,
    collect,
    response_ok,
    text,
    to_datetime,
    to_int,
    validate_filter,
    validate_uuid,
)

from .models import Schedule, ScheduleListResponse

if TYPE_CHECKING:
    from src.infrastructure.client import GvmClient


class ScheduleService:
    """Service for managing schedules."""

    def __init__(self, client: GvmClient) -> None:
        self._client = client

    def get(self, schedule_id: str) -> Schedule:
        schedule_id = validate_uuid(schedule_id, "schedule_id")

        def operation(gmp: Any) -> Any:
            return gmp.get_schedule(schedule_id=schedule_id)

        response: Element = self._client.execute(operation)
        if not response_ok(response):
            raise ResourceNotFoundError("schedule", schedule_id)

        schedule_elem = response.find("schedule")
        if schedule_elem is None:
            raise ResourceNotFoundError("schedule", schedule_id)

        return self._parse_schedule(schedule_elem)

    def list(self, filter_string: str = "") -> ScheduleListResponse:
        filter_string = validate_filter(filter_string)

        def operation(gmp: Any) -> Any:
            return gmp.get_schedules(filter_string=filter_string or None)

        response: Element = self._client.execute(operation)
        schedules = collect(response, "schedule", self._parse_schedule)

        return ScheduleListResponse(
            schedules=schedules,
            total=len(schedules),
            filtered=len(schedules),
        )

    def _parse_schedule(self, elem: Element) -> Schedule:
        return Schedule(
            id=attr(elem, "id"),
            name=text(elem, "name"),
            first_time=to_datetime(text(elem, "first_time")),
            period_months=to_int(text(elem, "period/months"), 0),
            period_days=to_int(text(elem, "period/days"), 0),
            period_hours=to_int(text(elem, "period/hours"), 0),
            period_minutes=to_int(text(elem, "period/minutes"), 0),
            timezone=text(elem, "timezone", "UTC"),
            comment=text(elem, "comment"),
        )
