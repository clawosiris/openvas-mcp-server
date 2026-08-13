# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Target service implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from gvm.errors import GvmResponseError

from src.errors import ResourceInUseError, ResourceNotFoundError
from src.utils import (
    attr,
    collect,
    response_ok,
    split_csv,
    text,
    to_bool,
    to_datetime,
    validate_filter,
    validate_hosts,
    validate_uuid,
)

from .models import (
    AliveTest,
    Credential,
    PortList,
    Target,
    TargetCreateRequest,
    TargetListResponse,
    TargetUpdateRequest,
)

if TYPE_CHECKING:
    from src.infrastructure.client import GvmClient


class TargetService:
    """Service for managing scan targets.

    Provides CRUD operations for GVM targets.
    """

    def __init__(self, client: GvmClient) -> None:
        """Initialize target service.

        Args:
            client: GVM client for executing GMP operations.
        """
        self._client = client

    def get(self, target_id: str) -> Target:
        """Get a target by ID.

        Args:
            target_id: Target UUID.

        Returns:
            Target details.

        Raises:
            InvalidUuidError: If target_id is not a valid UUID.
            ResourceNotFoundError: If target doesn't exist.
        """
        target_id = validate_uuid(target_id, "target_id")

        def operation(gmp: Any) -> Any:
            return gmp.get_target(target_id=target_id)

        try:
            response: Element = self._client.execute(operation)
        except GvmResponseError as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise ResourceNotFoundError("target", target_id) from e
            raise

        if not response_ok(response):
            raise ResourceNotFoundError("target", target_id)

        target_elem = response.find("target")
        if target_elem is None:
            raise ResourceNotFoundError("target", target_id)

        return self._parse_target(target_elem)

    def list(self, filter_string: str = "") -> TargetListResponse:
        """List targets with optional filter.

        Args:
            filter_string: GMP filter string (e.g., "name~web").

        Returns:
            List of targets with pagination info.

        Raises:
            InvalidFilterError: If filter contains invalid characters.
        """
        filter_string = validate_filter(filter_string)

        def operation(gmp: Any) -> Any:
            return gmp.get_targets(filter_string=filter_string or None)

        response = self._client.execute(operation)

        targets = collect(response, "target", self._parse_target)

        # Extract counts from response attributes
        targets_elem = response.find("targets")
        total = int(attr(targets_elem, "start", "0")) if targets_elem is not None else 0
        # GVM returns max attribute for total count
        if targets_elem is not None:
            total = int(attr(targets_elem, "max", str(len(targets))))

        return TargetListResponse(
            targets=targets,
            total=total,
            filtered=len(targets),
        )

    def create(self, request: TargetCreateRequest) -> Target:
        """Create a new target.

        Args:
            request: Target creation request.

        Returns:
            Created target details.

        Raises:
            InvalidHostError: If any host format is invalid.
        """
        # Validate hosts
        validate_hosts(request.hosts)
        if request.exclude_hosts:
            validate_hosts(request.exclude_hosts)

        # Build hosts string
        hosts_str = ", ".join(request.hosts)
        exclude_hosts_str = ", ".join(request.exclude_hosts) if request.exclude_hosts else None

        def operation(gmp: Any) -> Any:
            return gmp.create_target(
                name=request.name,
                hosts=[hosts_str],
                comment=request.comment or None,
                exclude_hosts=[exclude_hosts_str] if exclude_hosts_str else None,
                alive_test=self._alive_test_to_gvm(request.alive_test),
                reverse_lookup_only=request.reverse_lookup_only,
                reverse_lookup_unify=request.reverse_lookup_unify,
                port_list_id=request.port_list_id,
                ssh_credential_id=request.ssh_credential_id,
                smb_credential_id=request.smb_credential_id,
                esxi_credential_id=request.esxi_credential_id,
                snmp_credential_id=request.snmp_credential_id,
            )

        response = self._client.execute(operation)

        # Extract created target ID
        target_id = attr(response, "id")
        if not target_id:
            # Fallback: some GVM versions return id differently
            target_id = text(response, "id")

        # Fetch and return the created target
        return self.get(target_id)

    def update(self, target_id: str, request: TargetUpdateRequest) -> Target:
        """Update an existing target.

        Args:
            target_id: Target UUID.
            request: Update request with fields to modify.

        Returns:
            Updated target details.

        Raises:
            InvalidUuidError: If target_id is not a valid UUID.
            ResourceNotFoundError: If target doesn't exist.
        """
        target_id = validate_uuid(target_id, "target_id")

        # Validate hosts if provided
        if request.hosts is not None:
            validate_hosts(request.hosts)
        if request.exclude_hosts is not None and request.exclude_hosts:
            validate_hosts(request.exclude_hosts)

        # Build update kwargs - only include non-None values
        kwargs: dict[str, Any] = {"target_id": target_id}

        if request.name is not None:
            kwargs["name"] = request.name
        if request.hosts is not None:
            kwargs["hosts"] = [", ".join(request.hosts)]
        if request.comment is not None:
            kwargs["comment"] = request.comment
        if request.exclude_hosts is not None:
            kwargs["exclude_hosts"] = (
                [", ".join(request.exclude_hosts)] if request.exclude_hosts else []
            )
        if request.alive_test is not None:
            kwargs["alive_test"] = self._alive_test_to_gvm(request.alive_test)
        if request.reverse_lookup_only is not None:
            kwargs["reverse_lookup_only"] = request.reverse_lookup_only
        if request.reverse_lookup_unify is not None:
            kwargs["reverse_lookup_unify"] = request.reverse_lookup_unify
        if request.port_list_id is not None:
            kwargs["port_list_id"] = request.port_list_id

        def operation(gmp: Any) -> Any:
            return gmp.modify_target(**kwargs)

        self._client.execute(operation)

        # Fetch and return updated target
        return self.get(target_id)

    def delete(self, target_id: str, *, ultimate: bool = False) -> bool:
        """Delete a target.

        Args:
            target_id: Target UUID.
            ultimate: If True, permanently delete (no trash).

        Returns:
            True if deleted successfully.

        Raises:
            InvalidUuidError: If target_id is not a valid UUID.
            ResourceNotFoundError: If target doesn't exist.
            ResourceInUseError: If target is in use by a task.
        """
        target_id = validate_uuid(target_id, "target_id")

        def operation(gmp: Any) -> Any:
            return gmp.delete_target(target_id=target_id, ultimate=ultimate)

        response = self._client.execute(operation)

        status = attr(response, "status")
        if status == "404":
            raise ResourceNotFoundError("target", target_id)
        if status == "400":
            status_text = attr(response, "status_text")
            if "in use" in status_text.lower():
                raise ResourceInUseError(
                    f"Target {target_id} is in use by a task and cannot be deleted."
                )

        return response_ok(response)

    def clone(self, target_id: str) -> Target:
        """Clone an existing target.

        Args:
            target_id: Target UUID to clone.

        Returns:
            Cloned target details.

        Raises:
            InvalidUuidError: If target_id is not a valid UUID.
            ResourceNotFoundError: If target doesn't exist.
        """
        target_id = validate_uuid(target_id, "target_id")

        def operation(gmp: Any) -> Any:
            return gmp.clone_target(target_id=target_id)

        response = self._client.execute(operation)

        if not response_ok(response):
            raise ResourceNotFoundError("target", target_id)

        new_target_id = attr(response, "id")
        return self.get(new_target_id)

    def _parse_target(self, elem: Element) -> Target:
        """Parse target XML element into Target model."""
        # Parse port list if present
        port_list = None
        port_list_elem = elem.find("port_list")
        if port_list_elem is not None:
            port_list = PortList(
                id=attr(port_list_elem, "id"),
                name=text(port_list_elem, "name"),
            )

        # Parse credentials
        ssh_credential = self._parse_credential(elem, "ssh_credential")
        smb_credential = self._parse_credential(elem, "smb_credential")
        esxi_credential = self._parse_credential(elem, "esxi_credential")
        snmp_credential = self._parse_credential(elem, "snmp_credential")

        # Parse alive test
        alive_test_str = text(elem, "alive_tests")
        alive_test = self._parse_alive_test(alive_test_str)

        return Target(
            id=attr(elem, "id"),
            name=text(elem, "name"),
            comment=text(elem, "comment"),
            hosts=split_csv(text(elem, "hosts")),
            exclude_hosts=split_csv(text(elem, "exclude_hosts")),
            alive_test=alive_test,
            reverse_lookup_only=to_bool(text(elem, "reverse_lookup_only")),
            reverse_lookup_unify=to_bool(text(elem, "reverse_lookup_unify")),
            port_list=port_list,
            ssh_credential=ssh_credential,
            smb_credential=smb_credential,
            esxi_credential=esxi_credential,
            snmp_credential=snmp_credential,
            in_use=to_bool(text(elem, "in_use")),
            creation_time=to_datetime(text(elem, "creation_time")),
            modification_time=to_datetime(text(elem, "modification_time")),
        )

    def _parse_credential(self, elem: Element, tag: str) -> Credential | None:
        """Parse a credential element."""
        cred_elem = elem.find(tag)
        if cred_elem is None:
            return None
        cred_id = attr(cred_elem, "id")
        if not cred_id:
            return None
        return Credential(
            id=cred_id,
            name=text(cred_elem, "name"),
        )

    def _parse_alive_test(self, value: str) -> AliveTest:
        """Parse alive test string to enum."""
        if not value:
            return AliveTest.SCAN_CONFIG_DEFAULT
        # Try direct match
        for member in AliveTest:
            if member.value.lower() == value.lower():
                return member
        return AliveTest.SCAN_CONFIG_DEFAULT

    def _alive_test_to_gvm(self, alive_test: AliveTest) -> str:
        """Convert AliveTest enum to GMP string value.

        GMP accepts string values for alive_test directly, avoiding
        version-specific enum imports (v224, v225, v226, v227).
        """
        return alive_test.value
