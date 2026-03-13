"""Shared test fixtures."""

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.infrastructure import ConnectionStyle, GvmConfig


@pytest.fixture
def valid_local_config(tmp_path: Path) -> GvmConfig:
    """Create a valid local socket configuration."""
    socket_path = tmp_path / "gvmd.sock"
    socket_path.touch()
    return GvmConfig(
        style=ConnectionStyle.LOCAL,
        socket_path=str(socket_path),
        gmp_username="admin",
        gmp_password="secret",
        timeout=30,
    )


@pytest.fixture
def valid_remote_config() -> GvmConfig:
    """Create a valid remote TLS configuration."""
    return GvmConfig(
        style=ConnectionStyle.REMOTE,
        hostname="gvm.example.com",
        port=9390,
        gmp_username="admin",
        gmp_password="secret",
        timeout=30,
    )


@pytest.fixture
def mock_gmp() -> MagicMock:
    """Create a mock GMP instance."""
    gmp = MagicMock()
    gmp.is_connected.return_value = True
    return gmp


@pytest.fixture
def clean_env():
    """Clean environment variables for config tests."""
    gvm_vars = [k for k in os.environ if k.startswith("GVM_")]
    original = {k: os.environ.pop(k) for k in gvm_vars}
    yield
    os.environ.update(original)
