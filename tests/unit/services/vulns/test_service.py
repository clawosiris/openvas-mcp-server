"""Tests for vulnerability service."""

from unittest.mock import MagicMock
from xml.etree.ElementTree import Element, SubElement

import pytest

from src.services.vulns import VulnerabilityService
from src.utils import InvalidFilterError, InvalidUuidError


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(mock_client: MagicMock) -> VulnerabilityService:
    return VulnerabilityService(mock_client)


def test_list_vulnerabilities(service: VulnerabilityService, mock_client: MagicMock) -> None:
    response = Element("get_report_response", {"status": "200"})
    result = SubElement(response, "result", {"id": "r-1"})
    SubElement(result, "name").text = "Test vuln"
    SubElement(result, "host").text = "192.168.1.10"
    SubElement(result, "severity").text = "8.5"
    qod = SubElement(result, "qod")
    SubElement(qod, "value").text = "95"

    mock_client.execute.return_value = response

    out = service.list("11111111-1111-1111-1111-111111111111")
    assert out.total == 1
    assert out.findings[0].name == "Test vuln"
    assert out.findings[0].severity == 8.5


def test_list_vulnerabilities_invalid_uuid(service: VulnerabilityService) -> None:
    with pytest.raises(InvalidUuidError):
        service.list("bad")


def test_search_nvts(service: VulnerabilityService, mock_client: MagicMock) -> None:
    response = Element("get_nvts_response", {"status": "200"})
    nvt = SubElement(response, "nvt", {"oid": "1.3.6.1.4.1.25623.1.0.12345"})
    SubElement(nvt, "name").text = "OpenSSL vuln"
    SubElement(nvt, "family").text = "General"
    SubElement(nvt, "cvss_base").text = "7.5"

    mock_client.execute.return_value = response

    out = service.search_nvts("openssl")
    assert len(out) == 1
    assert out[0].name == "OpenSSL vuln"


def test_search_nvts_invalid_filter(service: VulnerabilityService) -> None:
    with pytest.raises(InvalidFilterError):
        service.search_nvts("bad<script>")
