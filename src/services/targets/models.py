# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Target domain models."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class AliveTest(StrEnum):
    """Methods for checking if hosts are alive."""

    SCAN_CONFIG_DEFAULT = "Scan Config Default"
    ICMP_PING = "ICMP Ping"
    TCP_ACK_SERVICE_PING = "TCP-ACK Service Ping"
    TCP_SYN_SERVICE_PING = "TCP-SYN Service Ping"
    ICMP_AND_TCP_ACK_SERVICE_PING = "ICMP & TCP-ACK Service Ping"
    ICMP_AND_ARP_PING = "ICMP & ARP Ping"
    ARP_PING = "ARP Ping"
    CONSIDER_ALIVE = "Consider Alive"


class PortList(BaseModel):
    """Port list reference."""

    id: str
    name: str


class Credential(BaseModel):
    """Credential reference."""

    id: str
    name: str


class Target(BaseModel):
    """Target domain model.

    Represents a scan target in GVM.
    """

    id: str = Field(description="Target UUID")
    name: str = Field(description="Target name")
    comment: str = Field(default="", description="Optional comment")
    hosts: list[str] = Field(description="List of hosts (IP, CIDR, or hostname)")
    exclude_hosts: list[str] = Field(default_factory=list, description="Hosts to exclude from scan")
    alive_test: AliveTest = Field(
        default=AliveTest.SCAN_CONFIG_DEFAULT,
        description="Method to check if hosts are alive",
    )
    reverse_lookup_only: bool = Field(default=False, description="Only scan hosts with reverse DNS")
    reverse_lookup_unify: bool = Field(default=False, description="Unify hosts by reverse DNS")
    port_list: PortList | None = Field(default=None, description="Associated port list")
    ssh_credential: Credential | None = Field(
        default=None, description="SSH credential for authenticated scans"
    )
    smb_credential: Credential | None = Field(
        default=None, description="SMB credential for authenticated scans"
    )
    esxi_credential: Credential | None = Field(
        default=None, description="ESXi credential for authenticated scans"
    )
    snmp_credential: Credential | None = Field(
        default=None, description="SNMP credential for authenticated scans"
    )
    in_use: bool = Field(default=False, description="Whether target is used by a task")
    creation_time: datetime | None = Field(default=None, description="Creation timestamp")
    modification_time: datetime | None = Field(
        default=None, description="Last modification timestamp"
    )


class TargetCreateRequest(BaseModel):
    """Request model for creating a target."""

    name: str = Field(description="Target name", min_length=1)
    hosts: list[str] = Field(description="List of hosts (IP, CIDR, or hostname)")
    comment: str = Field(default="", description="Optional comment")
    exclude_hosts: list[str] = Field(default_factory=list, description="Hosts to exclude")
    alive_test: AliveTest = Field(
        default=AliveTest.SCAN_CONFIG_DEFAULT,
        description="Method to check if hosts are alive",
    )
    reverse_lookup_only: bool = Field(default=False)
    reverse_lookup_unify: bool = Field(default=False)
    port_list_id: str | None = Field(default=None, description="Port list UUID")
    ssh_credential_id: str | None = Field(default=None, description="SSH credential UUID")
    smb_credential_id: str | None = Field(default=None, description="SMB credential UUID")
    esxi_credential_id: str | None = Field(default=None, description="ESXi credential UUID")
    snmp_credential_id: str | None = Field(default=None, description="SNMP credential UUID")


class TargetUpdateRequest(BaseModel):
    """Request model for updating a target.

    All fields are optional - only provided fields will be updated.
    """

    name: str | None = Field(default=None, description="New target name")
    hosts: list[str] | None = Field(default=None, description="New host list")
    comment: str | None = Field(default=None, description="New comment")
    exclude_hosts: list[str] | None = Field(default=None, description="New exclude list")
    alive_test: AliveTest | None = Field(default=None, description="New alive test method")
    reverse_lookup_only: bool | None = Field(default=None)
    reverse_lookup_unify: bool | None = Field(default=None)
    port_list_id: str | None = Field(default=None, description="New port list UUID")


class TargetListResponse(BaseModel):
    """Response model for listing targets."""

    targets: list[Target] = Field(description="List of targets")
    total: int = Field(description="Total number of targets matching filter")
    filtered: int = Field(description="Number of targets in this response")
