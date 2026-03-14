# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Configuration loading and management.

Supports loading from environment variables or TOML config file.
Environment variables take precedence over config file values.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any


class ConnectionStyle(str, Enum):
    """Connection style to GVM."""

    LOCAL = "local"
    REMOTE = "remote"


@dataclass(frozen=True)
class GvmConfig:
    """Complete GVM configuration.

    Attributes:
        style: Connection style (local or remote)
        socket_path: Unix socket path (for local style)
        hostname: Remote host (for remote style)
        port: Remote port (for remote style)
        certfile: Client certificate path (for remote style)
        cafile: CA certificate path (for remote style)
        keyfile: Client key path (for remote style)
        key_password: Password for client key (for remote style)
        gmp_username: GMP authentication username
        gmp_password: GMP authentication password
        timeout: Operation timeout in seconds
        retry_max_attempts: Maximum retry attempts on error
    """

    # Connection style
    style: ConnectionStyle = ConnectionStyle.LOCAL

    # Local (Unix socket) settings
    socket_path: str = "/run/gvmd/gvmd.sock"

    # Remote (TLS) settings
    hostname: str = "127.0.0.1"
    port: int = 9390
    certfile: str | None = None
    cafile: str | None = None
    keyfile: str | None = None
    key_password: str | None = None

    # GMP Authentication
    gmp_username: str = ""
    gmp_password: str = ""

    # Common settings
    timeout: int = 60
    retry_max_attempts: int = 3

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors.

        Returns:
            List of validation error messages. Empty if valid.
        """
        errors: list[str] = []

        if self.style == ConnectionStyle.LOCAL:
            if not self.socket_path:
                errors.append("socket_path is required for local connection")
        elif self.style == ConnectionStyle.REMOTE:
            if not self.hostname:
                errors.append("hostname is required for remote connection")
        else:
            errors.append(f"Invalid connection style: {self.style}")

        if not self.gmp_username:
            errors.append("gmp_username is required")
        if not self.gmp_password:
            errors.append("gmp_password is required")

        if self.timeout <= 0:
            errors.append(f"Invalid timeout: {self.timeout}")
        if self.retry_max_attempts < 0:
            errors.append(f"Invalid retry_max_attempts: {self.retry_max_attempts}")

        return errors


class ConfigLoader:
    """Load configuration from environment and/or config file."""

    # Default config file paths
    DEFAULT_CONFIG_PATHS = [
        Path.home() / ".config" / "openvas-mcp" / "config.toml",
        Path("/etc/openvas-mcp/config.toml"),
    ]

    @classmethod
    def from_env(cls) -> GvmConfig:
        """Load configuration from environment variables only.

        Returns:
            GvmConfig instance populated from environment.
        """
        return cls._build_config(cls._load_env())

    @classmethod
    def from_file(cls, path: str | Path) -> GvmConfig:
        """Load configuration from TOML file.

        Args:
            path: Path to TOML config file.

        Returns:
            GvmConfig instance populated from file.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            tomllib.TOMLDecodeError: If config file is invalid TOML.
        """
        return cls._build_config(cls._load_file(path))

    @classmethod
    def from_env_and_file(cls, path: str | Path | None = None) -> GvmConfig:
        """Load configuration from file with environment overrides.

        Environment variables take precedence over file values.

        Args:
            path: Optional path to TOML config file. If None, checks
                  default locations.

        Returns:
            GvmConfig instance with merged configuration.
        """
        values: dict[str, Any] = {}

        # Try to load from file
        config_path = cls._find_config_file(path)
        if config_path:
            values = cls._load_file(config_path)

        # Override with environment
        env_values = cls._load_env()
        values.update(env_values)

        return cls._build_config(values)

    @classmethod
    def _find_config_file(cls, explicit_path: str | Path | None) -> Path | None:
        """Find config file from explicit path or defaults."""
        if explicit_path:
            path = Path(explicit_path)
            return path if path.exists() else None

        for path in cls.DEFAULT_CONFIG_PATHS:
            if path.exists():
                return path

        return None

    @classmethod
    def _load_env(cls) -> dict[str, Any]:
        """Extract configuration from environment variables."""
        values: dict[str, Any] = {}

        # Style
        style = os.getenv("GVM_STYLE")
        if style:
            values["style"] = ConnectionStyle(style.lower())

        # Local
        if socket_path := os.getenv("GVM_SOCKET_PATH"):
            values["socket_path"] = socket_path

        # Remote
        if hostname := os.getenv("GVM_HOSTNAME"):
            values["hostname"] = hostname
        if port := os.getenv("GVM_PORT"):
            values["port"] = int(port)
        if certfile := os.getenv("GVM_CERTFILE"):
            values["certfile"] = certfile
        if cafile := os.getenv("GVM_CAFILE"):
            values["cafile"] = cafile
        if keyfile := os.getenv("GVM_KEYFILE"):
            values["keyfile"] = keyfile
        if key_password := os.getenv("GVM_KEY_PASSWORD"):
            values["key_password"] = key_password

        # Auth
        if username := os.getenv("GVM_USERNAME"):
            values["gmp_username"] = username
        if password := os.getenv("GVM_PASSWORD"):
            values["gmp_password"] = password

        # Common
        if timeout := os.getenv("GVM_TIMEOUT"):
            values["timeout"] = int(timeout)
        if retry := os.getenv("GVM_RETRY_MAX_ATTEMPTS"):
            values["retry_max_attempts"] = int(retry)

        return values

    @classmethod
    def _load_file(cls, path: str | Path) -> dict[str, Any]:
        """Load and flatten TOML config file."""
        with open(path, "rb") as f:
            data = tomllib.load(f)

        values: dict[str, Any] = {}

        # [connection] section
        if conn := data.get("connection"):
            if style := conn.get("style"):
                values["style"] = ConnectionStyle(style.lower())
            for key in ("socket_path", "hostname", "port", "timeout"):
                if key in conn:
                    values[key] = conn[key]

        # [tls] section
        if tls := data.get("tls"):
            for key in ("certfile", "cafile", "keyfile", "key_password"):
                if key in tls:
                    values[key] = tls[key]

        # [auth] section
        if auth := data.get("auth"):
            if username := auth.get("username"):
                values["gmp_username"] = username
            if password := auth.get("password"):
                values["gmp_password"] = password

        # [retry] section
        if (retry := data.get("retry")) and "max_attempts" in retry:
            values["retry_max_attempts"] = retry["max_attempts"]

        return values

    @classmethod
    def _build_config(cls, values: dict[str, Any]) -> GvmConfig:
        """Build GvmConfig from dictionary of values."""
        return GvmConfig(**values)
