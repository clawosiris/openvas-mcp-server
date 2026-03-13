"""Remote client using TLS connection."""

from __future__ import annotations

import ssl
from typing import TYPE_CHECKING, Optional

from gvm.connections import TLSConnection

from .base import GvmClient

if TYPE_CHECKING:
    from openvas_mcp.infrastructure.config import GvmConfig


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

    def __init__(self, config: "GvmConfig") -> None:
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
        ssl_context = self._create_ssl_context()

        return TLSConnection(
            hostname=self._config.hostname,
            port=self._config.port,
            timeout=self._config.timeout,
            **({"ssl_context": ssl_context} if ssl_context else {}),
        )

    def _create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Create SSL context for TLS connection.

        Returns:
            Configured SSLContext or None for default.
        """
        # Check if we need custom context
        has_custom_config = any([
            self._config.cafile,
            self._config.certfile,
            self._config.keyfile,
        ])

        if not has_custom_config:
            return None

        context = ssl.create_default_context()

        # Load CA certificate
        if self._config.cafile:
            context.load_verify_locations(cafile=self._config.cafile)

        # Load client certificate for mutual TLS
        if self._config.certfile:
            context.load_cert_chain(
                certfile=self._config.certfile,
                keyfile=self._config.keyfile,
                password=self._config.key_password,
            )

        return context
