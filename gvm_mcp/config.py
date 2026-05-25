from __future__ import annotations

import os
from dataclasses import dataclass
from enum import StrEnum


class ConnectionStyle(StrEnum):
    LOCAL = "local"
    REMOTE = "remote"


@dataclass(frozen=True)
class GvmMcpConfig:
    style: ConnectionStyle = ConnectionStyle.LOCAL
    socket_path: str = "/run/gvmd/gvmd.sock"
    hostname: str = "127.0.0.1"
    port: int = 9390
    username: str = ""
    password: str = ""
    timeout: int = 60
    cafile: str | None = None
    certfile: str | None = None
    keyfile: str | None = None
    key_password: str | None = None

    def validate(self) -> None:
        if self.style == ConnectionStyle.LOCAL and not self.socket_path:
            raise ValueError("GVM_SOCKET_PATH is required for local style")
        if self.style == ConnectionStyle.REMOTE and not self.hostname:
            raise ValueError("GVM_HOSTNAME is required for remote style")
        if not self.username:
            raise ValueError("GVM_USERNAME is required")
        if not self.password:
            raise ValueError("GVM_PASSWORD is required")
        if self.port <= 0:
            raise ValueError("GVM_PORT must be > 0")
        if self.timeout <= 0:
            raise ValueError("GVM_TIMEOUT must be > 0")


def load_config() -> GvmMcpConfig:
    style = ConnectionStyle(os.getenv("GVM_STYLE", "local").lower())
    cfg = GvmMcpConfig(
        style=style,
        socket_path=os.getenv("GVM_SOCKET_PATH", "/run/gvmd/gvmd.sock"),
        hostname=os.getenv("GVM_HOSTNAME", "127.0.0.1"),
        port=int(os.getenv("GVM_PORT", "9390")),
        username=os.getenv("GVM_USERNAME", ""),
        password=os.getenv("GVM_PASSWORD", ""),
        timeout=int(os.getenv("GVM_TIMEOUT", "60")),
        cafile=os.getenv("GVM_CAFILE"),
        certfile=os.getenv("GVM_CERTFILE"),
        keyfile=os.getenv("GVM_KEYFILE"),
        key_password=os.getenv("GVM_KEY_PASSWORD"),
    )
    cfg.validate()
    return cfg
