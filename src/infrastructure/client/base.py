"""Abstract base client for GVM connections.

Provides thread-safe operation execution with retry on error.
"""

from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from contextlib import suppress
from typing import TYPE_CHECKING, TypeVar

from gvm.errors import GvmError
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeCheckCommandTransform

if TYPE_CHECKING:
    from src.infrastructure.config import GvmConfig

logger = logging.getLogger(__name__)

T = TypeVar("T")


class GvmClientError(Exception):
    """Base exception for GVM client errors."""

    pass


class ConnectionError(GvmClientError):
    """Failed to connect to GVM server."""

    pass


class AuthenticationError(GvmClientError):
    """GVM authentication failed."""

    pass


class GvmClient(ABC):
    """Abstract base client for GVM connections.

    Provides:
    - Thread-safe operation execution
    - Retry on error
    - Auto-reconnect on connection failure

    Usage:
        client = LocalClient(config)  # or RemoteClient
        result = client.execute(lambda gmp: gmp.get_targets())
    """

    def __init__(self, config: GvmConfig) -> None:
        """Initialize client.

        Args:
            config: GVM connection configuration.

        Raises:
            ValueError: If configuration is invalid.
        """
        errors = config.validate()
        if errors:
            raise ValueError(f"Invalid configuration: {'; '.join(errors)}")

        self._config = config
        self._gmp: Gmp | None = None
        self._lock = threading.RLock()
        self._last_used: float = 0.0

    @abstractmethod
    def _create_connection(self):
        """Create the underlying GVM connection.

        Returns:
            Connection object (UnixSocketConnection or TLSConnection).
        """
        pass

    def execute(self, operation: Callable[[Gmp], T], timeout: float | None = None) -> T:
        """Execute a GMP operation with retry.

        Args:
            operation: Callable that takes a Gmp instance and returns a result.
            timeout: Optional timeout for acquiring the lock.

        Returns:
            The result of the operation.

        Raises:
            ConnectionError: If connection cannot be established after retries.
            GvmError: If the GMP operation fails after retries.
            TimeoutError: If lock cannot be acquired within timeout.
        """
        timeout = timeout or self._config.timeout

        acquired = self._lock.acquire(timeout=timeout)
        if not acquired:
            raise TimeoutError(
                "Timeout waiting for GVM connection. Another operation is in progress."
            )

        try:
            return self._execute_with_retry(operation)
        finally:
            self._lock.release()

    def _execute_with_retry(self, operation: Callable[[Gmp], T]) -> T:
        """Execute with retry on error."""
        last_error: Exception | None = None

        for attempt in range(self._config.retry_max_attempts):
            try:
                self._ensure_connected()
                result = operation(self._gmp)  # type: ignore
                self._last_used = time.time()
                return result
            except GvmError as e:
                last_error = e
                if not self._is_retryable(e):
                    raise

                if attempt < self._config.retry_max_attempts - 1:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    self._reconnect()

        raise last_error  # type: ignore

    def _ensure_connected(self) -> None:
        """Ensure connection is alive, reconnect if needed."""
        if self._gmp is None or not self._gmp.is_connected():
            self._connect()

    def _connect(self) -> None:
        """Establish connection and authenticate."""
        # Disconnect existing if any
        if self._gmp is not None:
            with suppress(Exception):
                self._gmp.disconnect()
            self._gmp = None

        # Create connection
        connection = self._create_connection()
        transform = EtreeCheckCommandTransform()

        try:
            self._gmp = Gmp(connection=connection, transform=transform)
            self._gmp.connect()
            logger.info(f"Connected to GVM via {self._config.style.value}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to GVM: {e}") from e

        # Authenticate
        try:
            self._gmp.authenticate(
                username=self._config.gmp_username,
                password=self._config.gmp_password,
            )
            logger.info(f"Authenticated as {self._config.gmp_username}")
        except GvmError as e:
            self._gmp.disconnect()
            self._gmp = None
            raise AuthenticationError(f"Authentication failed: {e}") from e

    def _reconnect(self) -> None:
        """Force reconnection."""
        self._disconnect()
        self._connect()

    def _disconnect(self) -> None:
        """Clean disconnect."""
        if self._gmp is not None:
            with suppress(Exception):
                self._gmp.disconnect()
            self._gmp = None

    def disconnect(self) -> None:
        """Public disconnect method."""
        with self._lock:
            self._disconnect()
            logger.info("Disconnected from GVM")

    def _is_retryable(self, error: GvmError) -> bool:
        """Check if error should trigger retry."""
        error_msg = str(error).lower()
        retryable_patterns = [
            "remote closed the connection",
            "timeout while reading",
            "connection refused",
            "connection reset",
        ]
        return any(pattern in error_msg for pattern in retryable_patterns)

    @property
    def is_connected(self) -> bool:
        """Check if client is currently connected."""
        return self._gmp is not None and self._gmp.is_connected()

    @property
    def config(self) -> GvmConfig:
        """Get the client configuration."""
        return self._config
