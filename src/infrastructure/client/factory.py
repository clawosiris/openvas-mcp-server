"""Client factory for creating appropriate client based on config."""

from __future__ import annotations

from src.infrastructure.config import ConnectionStyle, GvmConfig

from .base import GvmClient
from .local import LocalClient
from .remote import RemoteClient


def create_client(config: GvmConfig) -> GvmClient:
    """Create appropriate client based on configuration.

    Args:
        config: GVM configuration.

    Returns:
        LocalClient or RemoteClient instance.

    Raises:
        ValueError: If configuration is invalid or style is unknown.
    """
    errors = config.validate()
    if errors:
        raise ValueError(f"Invalid configuration: {'; '.join(errors)}")

    if config.style == ConnectionStyle.LOCAL:
        return LocalClient(config)
    elif config.style == ConnectionStyle.REMOTE:
        return RemoteClient(config)
    else:
        raise ValueError(f"Unknown connection style: {config.style}")
