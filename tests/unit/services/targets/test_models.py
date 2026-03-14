"""Tests for target models."""

import pytest
from pydantic import ValidationError

from src.services.targets import (
    AliveTest,
    PortList,
    Target,
    TargetCreateRequest,
    TargetListResponse,
    TargetUpdateRequest,
)


class TestTargetModel:
    """Tests for Target model."""

    def test_minimal_target(self):
        """Target can be created with minimal fields."""
        target = Target(
            id="test-uuid",
            name="Test",
            hosts=["192.168.1.1"],
        )
        assert target.id == "test-uuid"
        assert target.name == "Test"
        assert target.hosts == ["192.168.1.1"]
        assert target.comment == ""
        assert target.exclude_hosts == []
        assert target.alive_test == AliveTest.SCAN_CONFIG_DEFAULT

    def test_full_target(self):
        """Target can be created with all fields."""
        target = Target(
            id="test-uuid",
            name="Full Target",
            comment="A test target",
            hosts=["192.168.1.0/24", "10.0.0.1"],
            exclude_hosts=["192.168.1.1"],
            alive_test=AliveTest.ICMP_PING,
            reverse_lookup_only=True,
            reverse_lookup_unify=False,
            port_list=PortList(id="port-uuid", name="Default"),
            in_use=True,
        )
        assert target.comment == "A test target"
        assert len(target.hosts) == 2
        assert target.port_list is not None
        assert target.port_list.name == "Default"

    def test_target_serialization(self):
        """Target can be serialized to dict."""
        target = Target(
            id="test-uuid",
            name="Test",
            hosts=["192.168.1.1"],
        )
        data = target.model_dump()
        assert data["id"] == "test-uuid"
        assert data["name"] == "Test"
        assert data["hosts"] == ["192.168.1.1"]


class TestTargetCreateRequest:
    """Tests for TargetCreateRequest model."""

    def test_valid_request(self):
        """Valid create request is accepted."""
        request = TargetCreateRequest(
            name="Test Target",
            hosts=["192.168.1.1"],
        )
        assert request.name == "Test Target"
        assert request.hosts == ["192.168.1.1"]

    def test_name_required(self):
        """Name is required."""
        with pytest.raises(ValidationError):
            TargetCreateRequest(hosts=["192.168.1.1"])  # type: ignore

    def test_hosts_required(self):
        """Hosts is required."""
        with pytest.raises(ValidationError):
            TargetCreateRequest(name="Test")  # type: ignore

    def test_name_min_length(self):
        """Name must have at least 1 character."""
        with pytest.raises(ValidationError):
            TargetCreateRequest(name="", hosts=["192.168.1.1"])

    def test_defaults(self):
        """Default values are set correctly."""
        request = TargetCreateRequest(
            name="Test",
            hosts=["192.168.1.1"],
        )
        assert request.comment == ""
        assert request.exclude_hosts == []
        assert request.alive_test == AliveTest.SCAN_CONFIG_DEFAULT
        assert request.port_list_id is None


class TestTargetUpdateRequest:
    """Tests for TargetUpdateRequest model."""

    def test_all_fields_optional(self):
        """All fields are optional."""
        request = TargetUpdateRequest()
        assert request.name is None
        assert request.hosts is None
        assert request.comment is None

    def test_partial_update(self):
        """Can specify only fields to update."""
        request = TargetUpdateRequest(name="New Name")
        assert request.name == "New Name"
        assert request.hosts is None


class TestTargetListResponse:
    """Tests for TargetListResponse model."""

    def test_empty_response(self):
        """Empty list response."""
        response = TargetListResponse(
            targets=[],
            total=0,
            filtered=0,
        )
        assert response.targets == []
        assert response.total == 0

    def test_with_targets(self):
        """Response with targets."""
        target = Target(
            id="uuid",
            name="Test",
            hosts=["192.168.1.1"],
        )
        response = TargetListResponse(
            targets=[target],
            total=10,
            filtered=1,
        )
        assert len(response.targets) == 1
        assert response.total == 10
        assert response.filtered == 1


class TestAliveTestEnum:
    """Tests for AliveTest enum."""

    def test_values(self):
        """All expected values exist."""
        assert AliveTest.SCAN_CONFIG_DEFAULT.value == "Scan Config Default"
        assert AliveTest.ICMP_PING.value == "ICMP Ping"
        assert AliveTest.CONSIDER_ALIVE.value == "Consider Alive"

    def test_from_string(self):
        """Can create from string value."""
        alive_test = AliveTest("ICMP Ping")
        assert alive_test == AliveTest.ICMP_PING
