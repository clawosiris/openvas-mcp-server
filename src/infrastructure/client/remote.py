"""Remote client using TLS connection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gvm.connections import TLSConnection

from .base import GvmClient

if TYPE_CHECKING:
    from src.infrastructure.config import GvmConfig


class RemoteClient(GvmClient):
    """Client for remote TLS connections.

    Usage:
        config = GvmConfig(
            style=ConnectionStyle.REMOTE,
            hostname="gvm.example.com",
            port=9390,
            gmp_username="admin",
            gmp_password="secret",
            cafile="/path/to/ca.pem"  # optional
        )
        client = RemoteClient(config)
        result = client.execute(lambda gmp: gmp.get_version())
    """

    def __init__(self, config: GvmConfig) -> None:
        """Initialize remote client.

        Args:
            config: GVM configuration with hostname set.
        """
        super().__init__(config)

    def _create_connection(self) -> TLSConnection:
        """Create TLS connection.

        Returns:
            TLSConnection instance.
        """
        return TLSConnection(
            hostname=self._config.hostname,
            port=self._config.port,
            timeout=self._config.timeout,
            certfile=self._config.certfile,
            cafile=self._config.cafile,
            keyfile=self._config.keyfile,
            password=self._config.key_password,
        )
