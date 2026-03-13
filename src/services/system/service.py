"""System service implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .models import GvmVersion

if TYPE_CHECKING:
    from src.infrastructure.client import GvmClient


class SystemService:
    """Service for system-level GVM operations."""

    def __init__(self, client: GvmClient) -> None:
        """Initialize system service.

        Args:
            client: GVM client for executing GMP operations.
        """
        self._client = client

    def get_version(self) -> GvmVersion:
        """Get GVM version information.

        Returns:
            GVM version details including GMP protocol and backend versions.
        """

        def operation(gmp: Any) -> Any:
            return gmp.get_version()

        response = self._client.execute(operation)

        # Parse version response
        version_elem = response.find("version")
        gmp_version = version_elem.text if version_elem is not None else ""

        return GvmVersion(
            gmp_version=gmp_version or "",
            backend_version="",  # Not always available in basic version call
            backend_name="gvmd",
        )

    def is_connected(self) -> bool:
        """Check if connected to GVM.

        Returns:
            True if connected, False otherwise.
        """
        return self._client.is_connected
