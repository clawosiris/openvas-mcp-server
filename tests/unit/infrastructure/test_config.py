# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Tests for configuration loading."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from src.infrastructure import ConfigLoader, ConnectionStyle, GvmConfig


class TestGvmConfig:
    """Tests for GvmConfig dataclass."""

    def test_default_values(self):
        """Default configuration has sensible values."""
        config = GvmConfig()
        assert config.style == ConnectionStyle.LOCAL
        assert config.socket_path == "/run/gvmd/gvmd.sock"
        assert config.port == 9390
        assert config.timeout == 60
        assert config.retry_max_attempts == 3

    def test_frozen_immutable(self):
        """Config is immutable after creation."""
        config = GvmConfig(hostname="test.example.com")
        with pytest.raises(AttributeError):
            config.hostname = "other.example.com"  # type: ignore

    def test_custom_values(self):
        """Custom values are preserved."""
        config = GvmConfig(
            style=ConnectionStyle.REMOTE,
            hostname="gvm.test.com",
            port=9391,
            gmp_username="testuser",
            gmp_password="testpass",
            timeout=120,
        )
        assert config.style == ConnectionStyle.REMOTE
        assert config.hostname == "gvm.test.com"
        assert config.port == 9391
        assert config.gmp_username == "testuser"
        assert config.timeout == 120


class TestGvmConfigValidation:
    """Tests for GvmConfig.validate() method."""

    def test_valid_local_config(self):
        """Valid local configuration passes validation."""
        config = GvmConfig(
            style=ConnectionStyle.LOCAL,
            socket_path="/run/gvmd/gvmd.sock",
            gmp_username="admin",
            gmp_password="secret",
        )
        errors = config.validate()
        assert errors == []

    def test_valid_remote_config(self):
        """Valid remote configuration passes validation."""
        config = GvmConfig(
            style=ConnectionStyle.REMOTE,
            hostname="gvm.example.com",
            gmp_username="admin",
            gmp_password="secret",
        )
        errors = config.validate()
        assert errors == []

    def test_local_missing_socket(self):
        """Local connection requires socket_path."""
        config = GvmConfig(
            style=ConnectionStyle.LOCAL,
            socket_path="",
            gmp_username="admin",
            gmp_password="secret",
        )
        errors = config.validate()
        assert any("socket_path" in e for e in errors)

    def test_remote_missing_hostname(self):
        """Remote connection requires hostname."""
        config = GvmConfig(
            style=ConnectionStyle.REMOTE,
            hostname="",
            gmp_username="admin",
            gmp_password="secret",
        )
        errors = config.validate()
        assert any("hostname" in e for e in errors)

    def test_missing_username(self):
        """Username is required."""
        config = GvmConfig(
            style=ConnectionStyle.LOCAL,
            gmp_password="secret",
        )
        errors = config.validate()
        assert any("gmp_username" in e for e in errors)

    def test_missing_password(self):
        """Password is required."""
        config = GvmConfig(
            style=ConnectionStyle.LOCAL,
            gmp_username="admin",
        )
        errors = config.validate()
        assert any("gmp_password" in e for e in errors)

    def test_invalid_timeout(self):
        """Timeout must be positive."""
        config = GvmConfig(
            style=ConnectionStyle.LOCAL,
            gmp_username="admin",
            gmp_password="secret",
            timeout=0,
        )
        errors = config.validate()
        assert any("timeout" in e for e in errors)

    def test_invalid_retry(self):
        """Retry must be non-negative."""
        config = GvmConfig(
            style=ConnectionStyle.LOCAL,
            gmp_username="admin",
            gmp_password="secret",
            retry_max_attempts=-1,
        )
        errors = config.validate()
        assert any("retry" in e for e in errors)


class TestConfigLoaderFromEnv:
    """Tests for ConfigLoader.from_env() method."""

    def test_empty_env(self, clean_env):
        """Empty environment returns defaults."""
        config = ConfigLoader.from_env()
        assert config.style == ConnectionStyle.LOCAL
        assert config.gmp_username == ""

    def test_all_env_vars(self, clean_env):
        """All environment variables are loaded."""
        env = {
            "GVM_STYLE": "remote",
            "GVM_HOSTNAME": "gvm.test.com",
            "GVM_PORT": "9391",
            "GVM_SOCKET_PATH": "/custom/path.sock",
            "GVM_USERNAME": "testuser",
            "GVM_PASSWORD": "testpass",
            "GVM_CERTFILE": "/path/to/cert.pem",
            "GVM_CAFILE": "/path/to/ca.pem",
            "GVM_KEYFILE": "/path/to/key.pem",
            "GVM_TIMEOUT": "120",
            "GVM_RETRY_MAX_ATTEMPTS": "5",
        }
        with patch.dict(os.environ, env):
            config = ConfigLoader.from_env()
            assert config.style == ConnectionStyle.REMOTE
            assert config.hostname == "gvm.test.com"
            assert config.port == 9391
            assert config.socket_path == "/custom/path.sock"
            assert config.gmp_username == "testuser"
            assert config.gmp_password == "testpass"
            assert config.certfile == "/path/to/cert.pem"
            assert config.timeout == 120
            assert config.retry_max_attempts == 5

    def test_partial_env(self, clean_env):
        """Partial environment fills only specified values."""
        with patch.dict(os.environ, {"GVM_HOSTNAME": "partial.test.com"}):
            config = ConfigLoader.from_env()
            assert config.hostname == "partial.test.com"
            assert config.port == 9390  # default


class TestConfigLoaderFromFile:
    """Tests for ConfigLoader.from_file() method."""

    def test_full_config_file(self, tmp_path: Path):
        """Full TOML config file is loaded correctly."""
        config_content = """
[connection]
style = "remote"
hostname = "gvm.file.com"
port = 9393
timeout = 180

[tls]
cafile = "/file/ca.pem"
certfile = "/file/client.pem"
keyfile = "/file/client.key"

[auth]
username = "fileuser"
password = "filepass"

[retry]
max_attempts = 5
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config_content)

        config = ConfigLoader.from_file(config_file)
        assert config.style == ConnectionStyle.REMOTE
        assert config.hostname == "gvm.file.com"
        assert config.port == 9393
        assert config.gmp_username == "fileuser"
        assert config.gmp_password == "filepass"
        assert config.cafile == "/file/ca.pem"
        assert config.timeout == 180
        assert config.retry_max_attempts == 5

    def test_minimal_config_file(self, tmp_path: Path):
        """Minimal config file with defaults."""
        config_content = """
[connection]
style = "local"

[auth]
username = "admin"
password = "admin"
"""
        config_file = tmp_path / "minimal.toml"
        config_file.write_text(config_content)

        config = ConfigLoader.from_file(config_file)
        assert config.style == ConnectionStyle.LOCAL
        assert config.timeout == 60  # default

    def test_file_not_found(self):
        """FileNotFoundError for missing config file."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.from_file("/nonexistent/config.toml")


class TestConfigLoaderMerged:
    """Tests for ConfigLoader.from_env_and_file() method."""

    def test_env_overrides_file(self, tmp_path: Path, clean_env):
        """Environment variables override file values."""
        config_content = """
[connection]
style = "local"
hostname = "file.host.com"

[auth]
username = "fileuser"
password = "filepass"
"""
        config_file = tmp_path / "config.toml"
        config_file.write_text(config_content)

        env = {
            "GVM_HOSTNAME": "env.host.com",
            "GVM_USERNAME": "envuser",
        }
        with patch.dict(os.environ, env):
            config = ConfigLoader.from_env_and_file(path=config_file)
            # Overridden by env
            assert config.hostname == "env.host.com"
            assert config.gmp_username == "envuser"
            # From file
            assert config.style == ConnectionStyle.LOCAL
            assert config.gmp_password == "filepass"
