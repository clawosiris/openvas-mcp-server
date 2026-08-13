# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Integration fixtures for the local GMP mock server."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import Element

import pytest

from src.infrastructure import ConnectionStyle, GvmConfig, LocalClient
from src.services.assets import AssetService
from src.services.compliance import ComplianceService
from src.services.notes import NoteService
from src.services.overrides import OverrideService
from src.services.port_lists import PortListService
from src.services.reports import ReportService
from src.services.scan_configs import ScanConfigService
from src.services.schedules import ScheduleService
from src.services.system import SystemService
from src.services.targets import TargetService
from src.services.tasks import TaskService
from src.services.tickets import TicketService
from src.services.vulns import VulnerabilityService

MOCK_SERVER_BIN = Path(
    os.environ.get(
        "GVM_MOCK_SERVER_BIN",
        "/home/clawd/.openclaw/workspace-thoth/rust-gvm/target/release/gvm-mock-server",
    )
)


def _extract_first_id(response: Element, tag: str) -> str | None:
    elem = response.find(tag)
    if elem is None:
        return None
    return elem.attrib.get("id")


@pytest.fixture(scope="session")
def mock_server_socket(tmp_path_factory: pytest.TempPathFactory) -> str:
    """Start the mock GMP server and return the socket path."""
    if not MOCK_SERVER_BIN.exists():
        pytest.skip(f"gvm-mock-server not found at {MOCK_SERVER_BIN}")

    socket_dir = tmp_path_factory.mktemp("gvm-mock-server")
    socket_path = socket_dir / "gvmd.sock"
    proc = subprocess.Popen(
        [
            str(MOCK_SERVER_BIN),
            "--mode",
            "stateful",
            "--version",
            "22.5",
            "--socket",
            str(socket_path),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        for _ in range(100):
            if socket_path.exists():
                break
            if proc.poll() is not None:
                break
            time.sleep(0.05)
        else:
            proc.terminate()
            pytest.fail("Timed out waiting for gvm-mock-server socket")

        if not socket_path.exists():
            stderr = ""
            if proc.stderr is not None:
                stderr = proc.stderr.read()
            if "Operation not permitted" in stderr:
                pytest.skip(
                    f"mock server cannot create a Unix socket in this environment: {stderr}"
                )
            pytest.fail(f"gvm-mock-server failed to create socket. stderr: {stderr}")

        yield str(socket_path)
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)


@pytest.fixture(scope="session")
def gvm_config(mock_server_socket: str) -> GvmConfig:
    """Build a local config pointed at the mock socket."""
    return GvmConfig(
        style=ConnectionStyle.LOCAL,
        socket_path=mock_server_socket,
        gmp_username="admin",
        gmp_password="admin",
        timeout=30,
    )


@pytest.fixture(scope="session")
def gvm_client(gvm_config: GvmConfig) -> LocalClient:
    """Create a real LocalClient and verify the socket is reachable."""
    client = LocalClient(gvm_config)
    try:
        SystemService(client).get_version()
    except Exception as exc:
        client.disconnect()
        pytest.skip(f"mock GMP server is not reachable from this environment: {exc}")

    yield client
    client.disconnect()


@pytest.fixture
def target_service(gvm_client: LocalClient) -> TargetService:
    return TargetService(gvm_client)


@pytest.fixture
def task_service(gvm_client: LocalClient) -> TaskService:
    return TaskService(gvm_client)


@pytest.fixture
def note_service(gvm_client: LocalClient) -> NoteService:
    return NoteService(gvm_client)


@pytest.fixture
def system_service(gvm_client: LocalClient) -> SystemService:
    return SystemService(gvm_client)


@pytest.fixture
def scan_config_service(gvm_client: LocalClient) -> ScanConfigService:
    return ScanConfigService(gvm_client)


@pytest.fixture
def scan_config_id(gvm_client: LocalClient) -> str:
    """Return a scan config ID if the mock exposes one."""

    def operation(gmp: Any) -> Any:
        return gmp.get_scan_configs()

    config_id = _extract_first_id(gvm_client.execute(operation), "config")
    if config_id is None:
        pytest.skip("mock server returned no scan configs")
    return config_id


@pytest.fixture
def scanner_id(gvm_client: LocalClient) -> str:
    """Return a scanner ID if the mock exposes one."""

    def operation(gmp: Any) -> Any:
        return gmp.get_scanners()

    scanner_id = _extract_first_id(gvm_client.execute(operation), "scanner")
    if scanner_id is None:
        pytest.skip("mock server returned no scanners")
    return scanner_id


# Additional service fixtures


@pytest.fixture
def override_service(gvm_client: LocalClient) -> OverrideService:
    return OverrideService(gvm_client)


@pytest.fixture
def port_list_service(gvm_client: LocalClient) -> PortListService:
    return PortListService(gvm_client)


@pytest.fixture
def schedule_service(gvm_client: LocalClient) -> ScheduleService:
    return ScheduleService(gvm_client)


@pytest.fixture
def ticket_service(gvm_client: LocalClient) -> TicketService:
    return TicketService(gvm_client)


@pytest.fixture
def report_service(gvm_client: LocalClient) -> ReportService:
    return ReportService(gvm_client)


@pytest.fixture
def vuln_service(gvm_client: LocalClient) -> VulnerabilityService:
    return VulnerabilityService(gvm_client)


@pytest.fixture
def asset_service(gvm_client: LocalClient) -> AssetService:
    return AssetService(gvm_client)


@pytest.fixture
def compliance_service(gvm_client: LocalClient) -> ComplianceService:
    return ComplianceService(gvm_client)


# ID fixtures for resources that require existing data


@pytest.fixture
def port_list_id(gvm_client: LocalClient) -> str:
    """Return a port list ID if the mock exposes one."""

    def operation(gmp: Any) -> Any:
        return gmp.get_port_lists()

    port_list_id = _extract_first_id(gvm_client.execute(operation), "port_list")
    if port_list_id is None:
        pytest.skip("mock server returned no port lists")
    return port_list_id


@pytest.fixture
def schedule_id(gvm_client: LocalClient) -> str:
    """Return a schedule ID if the mock exposes one."""

    def operation(gmp: Any) -> Any:
        return gmp.get_schedules()

    schedule_id = _extract_first_id(gvm_client.execute(operation), "schedule")
    if schedule_id is None:
        pytest.skip("mock server returned no schedules")
    return schedule_id


@pytest.fixture
def report_id(gvm_client: LocalClient) -> str:
    """Return a report ID if the mock exposes one."""

    def operation(gmp: Any) -> Any:
        return gmp.get_reports()

    report_id = _extract_first_id(gvm_client.execute(operation), "report")
    if report_id is None:
        pytest.skip("mock server returned no reports")
    return report_id


@pytest.fixture
def result_id(gvm_client: LocalClient) -> str:
    """Return a result ID if the mock exposes one (for tickets)."""

    def operation(gmp: Any) -> Any:
        return gmp.get_results()

    result_id = _extract_first_id(gvm_client.execute(operation), "result")
    if result_id is None:
        pytest.skip("mock server returned no results")
    return result_id


@pytest.fixture
def audit_id(gvm_client: LocalClient) -> str:
    """Return an audit ID if the mock exposes one."""

    def operation(gmp: Any) -> Any:
        return gmp.get_audits()

    audit_id = _extract_first_id(gvm_client.execute(operation), "task")
    if audit_id is None:
        pytest.skip("mock server returned no audits")
    return audit_id
