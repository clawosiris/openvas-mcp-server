# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Tests for target service."""

from unittest.mock import MagicMock
from xml.etree.ElementTree import Element, SubElement

import pytest

from src.errors import ResourceInUseError, ResourceNotFoundError
from src.services.targets import (
    AliveTest,
    TargetCreateRequest,
    TargetService,
    TargetUpdateRequest,
)
from src.utils import InvalidUuidError


@pytest.fixture
def mock_client() -> MagicMock:
    """Create mock GVM client."""
    return MagicMock()


@pytest.fixture
def target_service(mock_client: MagicMock) -> TargetService:
    """Create target service with mock client."""
    return TargetService(mock_client)


def _create_target_xml(
    target_id: str = "12345678-1234-1234-1234-123456789abc",
    name: str = "Test Target",
    hosts: str = "192.168.1.1, 192.168.1.2",
    comment: str = "Test comment",
    in_use: str = "0",
) -> Element:
    """Create a target XML element for testing."""
    target = Element("target", {"id": target_id})
    SubElement(target, "name").text = name
    SubElement(target, "comment").text = comment
    SubElement(target, "hosts").text = hosts
    SubElement(target, "exclude_hosts").text = ""
    SubElement(target, "alive_tests").text = "ICMP Ping"
    SubElement(target, "reverse_lookup_only").text = "0"
    SubElement(target, "reverse_lookup_unify").text = "0"
    SubElement(target, "in_use").text = in_use
    SubElement(target, "creation_time").text = "2024-01-15T10:30:00Z"
    SubElement(target, "modification_time").text = "2024-01-15T10:30:00Z"

    # Add port list
    port_list = SubElement(target, "port_list", {"id": "portlist-uuid-here"})
    SubElement(port_list, "name").text = "Default"

    return target


def _create_get_target_response(target: Element) -> Element:
    """Wrap target in get_target response."""
    response = Element("get_targets_response", {"status": "200", "status_text": "OK"})
    response.append(target)
    return response


def _create_targets_response(targets: list[Element]) -> Element:
    """Create get_targets response with multiple targets."""
    response = Element("get_targets_response", {"status": "200", "status_text": "OK"})
    targets_elem = SubElement(response, "targets", {"start": "1", "max": str(len(targets))})
    for target in targets:
        response.append(target)
    return response


class TestTargetServiceGet:
    """Tests for TargetService.get() method."""

    def test_get_existing_target(self, target_service: TargetService, mock_client: MagicMock):
        """Get returns target when it exists."""
        target_xml = _create_target_xml()
        response = _create_get_target_response(target_xml)
        mock_client.execute.return_value = response

        target = target_service.get("12345678-1234-1234-1234-123456789abc")

        assert target.id == "12345678-1234-1234-1234-123456789abc"
        assert target.name == "Test Target"
        assert target.hosts == ["192.168.1.1", "192.168.1.2"]
        assert target.comment == "Test comment"
        assert target.alive_test == AliveTest.ICMP_PING

    def test_get_invalid_uuid(self, target_service: TargetService):
        """Get raises InvalidUuidError for invalid UUID."""
        with pytest.raises(InvalidUuidError):
            target_service.get("not-a-valid-uuid")

    def test_get_nonexistent_target(self, target_service: TargetService, mock_client: MagicMock):
        """Get raises ResourceNotFoundError when target doesn't exist."""
        response = Element("get_targets_response", {"status": "404", "status_text": "Not Found"})
        mock_client.execute.return_value = response

        with pytest.raises(ResourceNotFoundError) as exc_info:
            target_service.get("12345678-1234-1234-1234-123456789abc")

        assert exc_info.value.details.resource_type == "target"


class TestTargetServiceList:
    """Tests for TargetService.list() method."""

    def test_list_returns_targets(self, target_service: TargetService, mock_client: MagicMock):
        """List returns all targets."""
        target1 = _create_target_xml(target_id="uuid-1", name="Target 1")
        target2 = _create_target_xml(target_id="uuid-2", name="Target 2")
        response = _create_targets_response([target1, target2])
        mock_client.execute.return_value = response

        result = target_service.list()

        assert len(result.targets) == 2
        assert result.targets[0].name == "Target 1"
        assert result.targets[1].name == "Target 2"

    def test_list_with_filter(self, target_service: TargetService, mock_client: MagicMock):
        """List passes filter to GMP."""
        response = _create_targets_response([])
        mock_client.execute.return_value = response

        target_service.list("name~web")

        # Verify the operation was called
        mock_client.execute.assert_called_once()

    def test_list_empty(self, target_service: TargetService, mock_client: MagicMock):
        """List returns empty list when no targets."""
        response = _create_targets_response([])
        mock_client.execute.return_value = response

        result = target_service.list()

        assert result.targets == []
        assert result.filtered == 0


class TestTargetServiceCreate:
    """Tests for TargetService.create() method."""

    def test_create_target(self, target_service: TargetService, mock_client: MagicMock):
        """Create creates target and returns it."""
        new_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        # Mock create response
        create_response = Element(
            "create_target_response",
            {"status": "201", "status_text": "OK", "id": new_uuid},
        )

        # Mock get response for fetching created target
        target_xml = _create_target_xml(target_id=new_uuid, name="New Target")
        get_response = _create_get_target_response(target_xml)

        mock_client.execute.side_effect = [create_response, get_response]

        request = TargetCreateRequest(
            name="New Target",
            hosts=["192.168.1.0/24"],
        )

        target = target_service.create(request)

        assert target.id == new_uuid
        assert mock_client.execute.call_count == 2

    def test_create_with_all_options(self, target_service: TargetService, mock_client: MagicMock):
        """Create handles all optional parameters."""
        new_uuid = "bbbbbbbb-cccc-dddd-eeee-ffffffffffff"
        create_response = Element(
            "create_target_response",
            {"status": "201", "id": new_uuid},
        )
        target_xml = _create_target_xml(target_id=new_uuid)
        get_response = _create_get_target_response(target_xml)

        mock_client.execute.side_effect = [create_response, get_response]

        request = TargetCreateRequest(
            name="Full Target",
            hosts=["10.0.0.1", "10.0.0.2"],
            comment="Test comment",
            exclude_hosts=["10.0.0.99"],
            alive_test=AliveTest.ICMP_PING,
            port_list_id="port-list-uuid",
            ssh_credential_id="ssh-cred-uuid",
        )

        target_service.create(request)
        mock_client.execute.assert_called()


class TestTargetServiceUpdate:
    """Tests for TargetService.update() method."""

    def test_update_target(self, target_service: TargetService, mock_client: MagicMock):
        """Update modifies target and returns updated version."""
        modify_response = Element(
            "modify_target_response",
            {"status": "200", "status_text": "OK"},
        )
        target_xml = _create_target_xml(name="Updated Name")
        get_response = _create_get_target_response(target_xml)

        mock_client.execute.side_effect = [modify_response, get_response]

        request = TargetUpdateRequest(name="Updated Name")
        target = target_service.update("12345678-1234-1234-1234-123456789abc", request)

        assert target.name == "Updated Name"

    def test_update_invalid_uuid(self, target_service: TargetService):
        """Update raises InvalidUuidError for invalid UUID."""
        request = TargetUpdateRequest(name="New Name")
        with pytest.raises(InvalidUuidError):
            target_service.update("invalid", request)


class TestTargetServiceDelete:
    """Tests for TargetService.delete() method."""

    def test_delete_target(self, target_service: TargetService, mock_client: MagicMock):
        """Delete removes target."""
        response = Element(
            "delete_target_response",
            {"status": "200", "status_text": "OK"},
        )
        mock_client.execute.return_value = response

        result = target_service.delete("12345678-1234-1234-1234-123456789abc")

        assert result is True

    def test_delete_target_in_use(self, target_service: TargetService, mock_client: MagicMock):
        """Delete raises ResourceInUseError when target is in use."""
        response = Element(
            "delete_target_response",
            {"status": "400", "status_text": "Target is in use"},
        )
        mock_client.execute.return_value = response

        with pytest.raises(ResourceInUseError):
            target_service.delete("12345678-1234-1234-1234-123456789abc")

    def test_delete_nonexistent(self, target_service: TargetService, mock_client: MagicMock):
        """Delete raises ResourceNotFoundError when target doesn't exist."""
        response = Element(
            "delete_target_response",
            {"status": "404", "status_text": "Not Found"},
        )
        mock_client.execute.return_value = response

        with pytest.raises(ResourceNotFoundError):
            target_service.delete("12345678-1234-1234-1234-123456789abc")


class TestTargetServiceClone:
    """Tests for TargetService.clone() method."""

    def test_clone_target(self, target_service: TargetService, mock_client: MagicMock):
        """Clone creates copy of target."""
        cloned_uuid = "cccccccc-dddd-eeee-ffff-111111111111"
        clone_response = Element(
            "clone_target_response",
            {"status": "201", "id": cloned_uuid},
        )
        target_xml = _create_target_xml(target_id=cloned_uuid, name="Test Target Clone")
        get_response = _create_get_target_response(target_xml)

        mock_client.execute.side_effect = [clone_response, get_response]

        target = target_service.clone("12345678-1234-1234-1234-123456789abc")

        assert target.id == cloned_uuid
