from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, TypeVar

from gvm.connections import TLSConnection, UnixSocketConnection
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeCheckCommandTransform

from .config import ConnectionStyle, GvmMcpConfig

T = TypeVar("T")


class GvmConnectionManager(AbstractContextManager["GvmConnectionManager"]):
    """Context-managed authenticated GMP connection."""

    def __init__(self, config: GvmMcpConfig) -> None:
        self.config = config
        self._gmp: Any | None = None

    def connect(self) -> Any:
        if self.config.style == ConnectionStyle.LOCAL:
            conn = UnixSocketConnection(path=self.config.socket_path, timeout=self.config.timeout)
        else:
            conn = TLSConnection(
                hostname=self.config.hostname,
                port=self.config.port,
                timeout=self.config.timeout,
                cafile=self.config.cafile,
                certfile=self.config.certfile,
                keyfile=self.config.keyfile,
                password=self.config.key_password,
            )

        gmp = Gmp(connection=conn, transform=EtreeCheckCommandTransform())
        gmp.connect()
        self._gmp = gmp.determine_supported_gmp()
        self._gmp.authenticate(username=self.config.username, password=self.config.password)
        return self._gmp

    def disconnect(self) -> None:
        if self._gmp is not None:
            self._gmp.disconnect()
            self._gmp = None

    def execute(self, operation: Callable[[Any], T]) -> T:
        if self._gmp is None:
            self.connect()
        return operation(self._gmp)

    def __enter__(self) -> GvmConnectionManager:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.disconnect()
