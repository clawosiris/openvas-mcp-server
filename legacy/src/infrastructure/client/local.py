# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Local client using Unix socket connection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gvm.connections import UnixSocketConnection

from .base import GvmClient

if TYPE_CHECKING:
    from src.infrastructure.config import GvmConfig


class LocalClient(GvmClient):
    """Client for local Unix socket connections.

    Usage:
        config = GvmConfig(
            style=ConnectionStyle.LOCAL,
            socket_path="/run/gvmd/gvmd.sock",
            gmp_username="admin",
            gmp_password="secret"
        )
        client = LocalClient(config)
        result = client.execute(lambda gmp: gmp.get_version())
    """

    def __init__(self, config: GvmConfig) -> None:
        """Initialize local client.

        Args:
            config: GVM configuration with socket_path set.
        """
        super().__init__(config)

    def _create_connection(self) -> UnixSocketConnection:
        """Create Unix socket connection.

        Returns:
            UnixSocketConnection instance.
        """
        return UnixSocketConnection(
            path=self._config.socket_path,
            timeout=self._config.timeout,
        )
