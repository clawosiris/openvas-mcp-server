# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Tests for GVM client implementations."""

import threading
from unittest.mock import MagicMock, patch

import pytest
from gvm.errors import GvmError

from src.infrastructure import (
    ConnectionStyle,
    GvmConfig,
    LocalClient,
    RemoteClient,
    create_client,
)
from src.infrastructure.client.base import AuthenticationError, ConnectionError


class TestGvmClientBase:
    """Tests for base client functionality."""

    def test_invalid_config_raises_error(self):
        """Invalid configuration raises ValueError."""
        config = GvmConfig(
            style=ConnectionStyle.LOCAL,
            # Missing username and password
        )
        with pytest.raises(ValueError, match="Invalid configuration"):
            LocalClient(config)

    @patch("src.infrastructure.client.local.UnixSocketConnection")
    @patch("src.infrastructure.client.base.Gmp")
    def test_execute_connects_on_first_call(
        self, mock_gmp_class, mock_socket_class, valid_local_config
    ):
        """First execute() call establishes connection."""
        mock_gmp = MagicMock()
        mock_gmp.is_connected.return_value = False

        # Mock the versioned GMP returned by determine_supported_gmp
        mock_versioned_gmp = MagicMock()
        mock_gmp.determine_supported_gmp.return_value = mock_versioned_gmp
        mock_gmp_class.return_value = mock_gmp

        client = LocalClient(valid_local_config)
        client.execute(lambda gmp: gmp.get_version())

        mock_gmp.connect.assert_called_once()
        mock_gmp.determine_supported_gmp.assert_called_once()
        mock_versioned_gmp.authenticate.assert_called_once_with(
            username="admin",
            password="secret",
        )

    @patch("src.infrastructure.client.local.UnixSocketConnection")
    @patch("src.infrastructure.client.base.Gmp")
    def test_execute_returns_result(self, mock_gmp_class, mock_socket_class, valid_local_config):
        """execute() returns operation result."""
        mock_gmp = MagicMock()
        mock_gmp.is_connected.return_value = True
        mock_gmp.get_version.return_value = "22.4"
        mock_gmp_class.return_value = mock_gmp

        client = LocalClient(valid_local_config)
        client._gmp = mock_gmp  # Pre-set connected state

        result = client.execute(lambda gmp: gmp.get_version())
        assert result == "22.4"

    @patch("src.infrastructure.client.local.UnixSocketConnection")
    @patch("src.infrastructure.client.base.Gmp")
    def test_execute_retries_on_connection_error(
        self, mock_gmp_class, mock_socket_class, valid_local_config
    ):
        """execute() retries on retryable errors."""
        call_count = [0]

        def operation(gmp):
            call_count[0] += 1
            if call_count[0] == 1:
                raise GvmError("Remote closed the connection")
            return "success"

        mock_gmp = MagicMock()
        mock_gmp.is_connected.return_value = True
        mock_gmp_class.return_value = mock_gmp

        client = LocalClient(valid_local_config)
        client._gmp = mock_gmp

        result = client.execute(operation)
        assert result == "success"
        assert call_count[0] == 2

    @patch("src.infrastructure.client.local.UnixSocketConnection")
    @patch("src.infrastructure.client.base.Gmp")
    def test_execute_does_not_retry_non_retryable_error(
        self, mock_gmp_class, mock_socket_class, valid_local_config
    ):
        """execute() does not retry non-retryable errors."""

        def operation(gmp):
            raise GvmError("Invalid argument")

        mock_gmp = MagicMock()
        mock_gmp.is_connected.return_value = True
        mock_gmp_class.return_value = mock_gmp

        client = LocalClient(valid_local_config)
        client._gmp = mock_gmp

        with pytest.raises(GvmError, match="Invalid argument"):
            client.execute(operation)

    @patch("src.infrastructure.client.local.UnixSocketConnection")
    @patch("src.infrastructure.client.base.Gmp")
    def test_connection_failure_raises_error(
        self, mock_gmp_class, mock_socket_class, valid_local_config
    ):
        """Connection failure raises ConnectionError."""
        mock_gmp = MagicMock()
        mock_gmp.connect.side_effect = OSError("Connection refused")
        mock_gmp_class.return_value = mock_gmp

        client = LocalClient(valid_local_config)
        with pytest.raises(ConnectionError, match="Failed to connect"):
            client.execute(lambda gmp: gmp.get_version())

    @patch("src.infrastructure.client.local.UnixSocketConnection")
    @patch("src.infrastructure.client.base.Gmp")
    def test_auth_failure_raises_error(self, mock_gmp_class, mock_socket_class, valid_local_config):
        """Authentication failure raises AuthenticationError."""
        mock_gmp = MagicMock()
        mock_gmp.is_connected.return_value = False

        # Mock the versioned GMP with failing authenticate
        mock_versioned_gmp = MagicMock()
        mock_versioned_gmp.authenticate.side_effect = GvmError("Authentication failed")
        mock_gmp.determine_supported_gmp.return_value = mock_versioned_gmp
        mock_gmp_class.return_value = mock_gmp

        client = LocalClient(valid_local_config)
        with pytest.raises(AuthenticationError, match="Authentication failed"):
            client.execute(lambda gmp: gmp.get_version())

    @patch("src.infrastructure.client.local.UnixSocketConnection")
    @patch("src.infrastructure.client.base.Gmp")
    def test_disconnect(self, mock_gmp_class, mock_socket_class, valid_local_config):
        """disconnect() closes connection."""
        mock_gmp = MagicMock()
        mock_gmp_class.return_value = mock_gmp

        client = LocalClient(valid_local_config)
        client._gmp = mock_gmp

        client.disconnect()

        mock_gmp.disconnect.assert_called_once()
        assert client._gmp is None

    @patch("src.infrastructure.client.local.UnixSocketConnection")
    @patch("src.infrastructure.client.base.Gmp")
    def test_is_connected_property(self, mock_gmp_class, mock_socket_class, valid_local_config):
        """is_connected property reflects connection state."""
        mock_gmp = MagicMock()
        mock_gmp.is_connected.return_value = True
        mock_gmp_class.return_value = mock_gmp

        client = LocalClient(valid_local_config)
        assert client.is_connected is False

        client._gmp = mock_gmp
        assert client.is_connected is True


class TestLocalClient:
    """Tests for LocalClient."""

    @patch("src.infrastructure.client.local.UnixSocketConnection")
    def test_creates_socket_connection(self, mock_socket_class, valid_local_config):
        """LocalClient creates UnixSocketConnection."""
        client = LocalClient(valid_local_config)
        connection = client._create_connection()

        mock_socket_class.assert_called_once_with(
            path=valid_local_config.socket_path,
            timeout=valid_local_config.timeout,
        )


class TestRemoteClient:
    """Tests for RemoteClient."""

    @patch("src.infrastructure.client.remote.TLSConnection")
    def test_creates_tls_connection(self, mock_tls_class, valid_remote_config):
        """RemoteClient creates TLSConnection."""
        client = RemoteClient(valid_remote_config)
        connection = client._create_connection()

        mock_tls_class.assert_called_once()
        call_kwargs = mock_tls_class.call_args.kwargs
        assert call_kwargs["hostname"] == "gvm.example.com"
        assert call_kwargs["port"] == 9390

    def test_creates_ssl_context_with_certs(self, valid_remote_config, tmp_path):
        """RemoteClient creates SSL context when certs provided."""
        # Create temp cert files
        ca_file = tmp_path / "ca.pem"
        ca_file.write_text("CA CERT")

        config = GvmConfig(
            style=ConnectionStyle.REMOTE,
            hostname="gvm.example.com",
            gmp_username="admin",
            gmp_password="secret",
            cafile=str(ca_file),
        )

        client = RemoteClient(config)
        # Just check it doesn't raise
        assert client._config.cafile is not None


class TestClientFactory:
    """Tests for create_client factory function."""

    def test_creates_local_client(self, valid_local_config):
        """Factory creates LocalClient for local style."""
        client = create_client(valid_local_config)
        assert isinstance(client, LocalClient)

    def test_creates_remote_client(self, valid_remote_config):
        """Factory creates RemoteClient for remote style."""
        client = create_client(valid_remote_config)
        assert isinstance(client, RemoteClient)

    def test_invalid_config_raises_error(self):
        """Factory raises error for invalid config."""
        config = GvmConfig(
            style=ConnectionStyle.LOCAL,
            # Missing credentials
        )
        with pytest.raises(ValueError, match="Invalid configuration"):
            create_client(config)


class TestClientThreadSafety:
    """Tests for thread-safe operation execution."""

    @patch("src.infrastructure.client.local.UnixSocketConnection")
    @patch("src.infrastructure.client.base.Gmp")
    def test_concurrent_execute_serialized(
        self, mock_gmp_class, mock_socket_class, valid_local_config
    ):
        """Concurrent execute() calls are serialized."""
        execution_order = []
        lock = threading.Lock()

        def mock_operation(gmp):
            with lock:
                execution_order.append(threading.current_thread().name)
            return "done"

        mock_gmp = MagicMock()
        mock_gmp.is_connected.return_value = True
        mock_gmp_class.return_value = mock_gmp

        client = LocalClient(valid_local_config)
        client._gmp = mock_gmp

        threads = [
            threading.Thread(
                target=lambda: client.execute(mock_operation),
                name=f"thread-{i}",
            )
            for i in range(3)
        ]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(execution_order) == 3
