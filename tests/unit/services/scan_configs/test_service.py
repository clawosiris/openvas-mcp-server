# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Tests for scan config service."""

from unittest.mock import MagicMock
from xml.etree.ElementTree import Element, SubElement

import pytest

from src.errors import ResourceNotFoundError
from src.services.scan_configs import ScanConfigService
from src.utils import InvalidUuidError


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(mock_client: MagicMock) -> ScanConfigService:
    return ScanConfigService(mock_client)


def test_list_scan_configs(service: ScanConfigService, mock_client: MagicMock) -> None:
    response = Element("get_configs_response", {"status": "200"})
    c1 = SubElement(response, "config", {"id": "11111111-1111-1111-1111-111111111111"})
    SubElement(c1, "name").text = "Full and fast"
    SubElement(c1, "family_count").text = "50"
    SubElement(c1, "nvt_count").text = "50000"

    mock_client.execute.return_value = response
    result = service.list()

    assert len(result.scan_configs) == 1
    assert result.scan_configs[0].name == "Full and fast"


def test_get_scan_config(service: ScanConfigService, mock_client: MagicMock) -> None:
    response = Element("get_config_response", {"status": "200"})
    c1 = SubElement(response, "config", {"id": "11111111-1111-1111-1111-111111111111"})
    SubElement(c1, "name").text = "Base"

    mock_client.execute.return_value = response
    result = service.get("11111111-1111-1111-1111-111111111111")
    assert result.name == "Base"


def test_get_scan_config_invalid_uuid(service: ScanConfigService) -> None:
    with pytest.raises(InvalidUuidError):
        service.get("bad-id")


def test_get_scan_config_not_found(service: ScanConfigService, mock_client: MagicMock) -> None:
    mock_client.execute.return_value = Element("get_config_response", {"status": "404"})
    with pytest.raises(ResourceNotFoundError):
        service.get("11111111-1111-1111-1111-111111111111")
