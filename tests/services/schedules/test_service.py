"""Tests for schedule service."""

from unittest.mock import MagicMock
from xml.etree.ElementTree import Element, SubElement

import pytest

from src.errors import ResourceNotFoundError
from src.services.schedules import ScheduleService
from src.utils import InvalidUuidError


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(mock_client: MagicMock) -> ScheduleService:
    return ScheduleService(mock_client)


def test_list_schedules(service: ScheduleService, mock_client: MagicMock) -> None:
    response = Element("get_schedules_response", {"status": "200"})
    sch = SubElement(response, "schedule", {"id": "11111111-1111-1111-1111-111111111111"})
    SubElement(sch, "name").text = "Daily"
    SubElement(sch, "timezone").text = "UTC"

    mock_client.execute.return_value = response
    result = service.list()

    assert len(result.schedules) == 1
    assert result.schedules[0].name == "Daily"


def test_get_schedule(service: ScheduleService, mock_client: MagicMock) -> None:
    response = Element("get_schedule_response", {"status": "200"})
    sch = SubElement(response, "schedule", {"id": "11111111-1111-1111-1111-111111111111"})
    SubElement(sch, "name").text = "Weekly"

    mock_client.execute.return_value = response
    result = service.get("11111111-1111-1111-1111-111111111111")

    assert result.name == "Weekly"


def test_get_schedule_invalid_uuid(service: ScheduleService) -> None:
    with pytest.raises(InvalidUuidError):
        service.get("bad-id")


def test_get_schedule_not_found(service: ScheduleService, mock_client: MagicMock) -> None:
    mock_client.execute.return_value = Element("get_schedule_response", {"status": "404"})
    with pytest.raises(ResourceNotFoundError):
        service.get("11111111-1111-1111-1111-111111111111")
