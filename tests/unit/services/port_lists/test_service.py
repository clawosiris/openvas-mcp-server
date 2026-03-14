"""Tests for port list service."""

from unittest.mock import MagicMock
from xml.etree.ElementTree import Element, SubElement

import pytest

from src.errors import ResourceNotFoundError
from src.services.port_lists import PortListService
from src.utils import InvalidUuidError


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(mock_client: MagicMock) -> PortListService:
    return PortListService(mock_client)


def test_list_port_lists(service: PortListService, mock_client: MagicMock) -> None:
    response = Element("get_port_lists_response", {"status": "200"})
    pl = SubElement(response, "port_list", {"id": "11111111-1111-1111-1111-111111111111"})
    SubElement(pl, "name").text = "All TCP"
    SubElement(pl, "port_count").text = "65535"

    mock_client.execute.return_value = response
    result = service.list()

    assert len(result.port_lists) == 1
    assert result.port_lists[0].name == "All TCP"


def test_get_port_list(service: PortListService, mock_client: MagicMock) -> None:
    response = Element("get_port_list_response", {"status": "200"})
    pl = SubElement(response, "port_list", {"id": "11111111-1111-1111-1111-111111111111"})
    SubElement(pl, "name").text = "All IANA"

    mock_client.execute.return_value = response
    result = service.get("11111111-1111-1111-1111-111111111111")

    assert result.name == "All IANA"


def test_get_port_list_invalid_uuid(service: PortListService) -> None:
    with pytest.raises(InvalidUuidError):
        service.get("bad-id")


def test_get_port_list_not_found(service: PortListService, mock_client: MagicMock) -> None:
    mock_client.execute.return_value = Element("get_port_list_response", {"status": "404"})
    with pytest.raises(ResourceNotFoundError):
        service.get("11111111-1111-1111-1111-111111111111")
