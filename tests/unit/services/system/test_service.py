"""Tests for system service."""

from unittest.mock import MagicMock
from xml.etree.ElementTree import Element, SubElement

import pytest

from src.services.system import GvmVersion, SystemService


@pytest.fixture
def mock_client() -> MagicMock:
    """Create mock GVM client."""
    return MagicMock()


@pytest.fixture
def system_service(mock_client: MagicMock) -> SystemService:
    """Create system service with mock client."""
    return SystemService(mock_client)


def _create_version_response(version: str = "22.4") -> Element:
    """Create a version XML response."""
    response = Element("get_version_response", {"status": "200", "status_text": "OK"})
    SubElement(response, "version").text = version
    return response


class TestSystemServiceGetVersion:
    """Tests for SystemService.get_version() method."""

    def test_get_version(self, system_service: SystemService, mock_client: MagicMock):
        """Get version returns version info."""
        response = _create_version_response("22.4")
        mock_client.execute.return_value = response

        version = system_service.get_version()

        assert isinstance(version, GvmVersion)
        assert version.gmp_version == "22.4"
        assert version.backend_name == "gvmd"

    def test_get_version_empty(self, system_service: SystemService, mock_client: MagicMock):
        """Get version handles empty response gracefully."""
        response = Element("get_version_response", {"status": "200"})
        mock_client.execute.return_value = response

        version = system_service.get_version()

        assert version.gmp_version == ""


class TestSystemServiceIsConnected:
    """Tests for SystemService.is_connected() method."""

    def test_is_connected_true(self, system_service: SystemService, mock_client: MagicMock):
        """Is connected returns True when client is connected."""
        mock_client.is_connected = True

        assert system_service.is_connected() is True

    def test_is_connected_false(self, system_service: SystemService, mock_client: MagicMock):
        """Is connected returns False when client is not connected."""
        mock_client.is_connected = False

        assert system_service.is_connected() is False


class TestGvmVersionModel:
    """Tests for GvmVersion model."""

    def test_minimal_version(self):
        """Version with minimal fields."""
        version = GvmVersion(gmp_version="22.4")
        assert version.gmp_version == "22.4"
        assert version.backend_version == ""
        assert version.backend_name == ""

    def test_full_version(self):
        """Version with all fields."""
        version = GvmVersion(
            gmp_version="22.4",
            backend_version="22.4.1",
            backend_name="gvmd",
        )
        assert version.gmp_version == "22.4"
        assert version.backend_version == "22.4.1"
        assert version.backend_name == "gvmd"

    def test_serialization(self):
        """Version can be serialized."""
        version = GvmVersion(gmp_version="22.4")
        data = version.model_dump()
        assert data["gmp_version"] == "22.4"
