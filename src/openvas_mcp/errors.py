"""Custom exception hierarchy for OpenVAS MCP.

All errors provide:
- Machine-readable error code
- User-friendly message
- Optional structured details
- Suggested HTTP status code
- CLI hint for command-line users
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ErrorDetails:
    """Structured error details."""

    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    field_name: Optional[str] = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        result = {}
        for key, value in vars(self).items():
            if value is not None and key != "extra":
                result[key] = value
        result.update(self.extra)
        return result


class OpenvasMcpError(Exception):
    """Base exception for all OpenVAS MCP errors."""

    code: str = "UNKNOWN_ERROR"
    http_status: int = 500
    default_message: str = "An unexpected error occurred."

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[ErrorDetails] = None,
    ):
        self.message = message or self.default_message
        self.details = details or ErrorDetails()
        super().__init__(self.message)

    @property
    def cli_hint(self) -> Optional[str]:
        """Hint for CLI users. Override in subclasses."""
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"code": self.code, "message": self.message}
        details = self.details.to_dict()
        if details:
            result["details"] = details
        return result


# =============================================================================
# Configuration Errors
# =============================================================================


class ConfigurationError(OpenvasMcpError):
    """Base class for configuration errors."""

    http_status = 500


class MissingConfigError(ConfigurationError):
    """Required configuration is missing."""

    code = "CONFIG_MISSING"
    default_message = "GVM connection is not configured."

    @property
    def cli_hint(self) -> str:
        return "Run 'openvas configure' to set up the connection."


class InvalidConfigError(ConfigurationError):
    """Configuration value is invalid."""

    code = "CONFIG_INVALID"
    default_message = "Invalid configuration value."


# =============================================================================
# Connection Errors
# =============================================================================


class ConnectionError(OpenvasMcpError):
    """Base class for connection errors."""

    http_status = 503


class SocketNotFoundError(ConnectionError):
    """Unix socket does not exist."""

    code = "SOCKET_NOT_FOUND"
    default_message = "GVM socket not found. Is gvmd running?"

    @property
    def cli_hint(self) -> str:
        return "Check that gvmd is running: 'systemctl status gvmd'"


class HostUnreachableError(ConnectionError):
    """Cannot reach remote host."""

    code = "HOST_UNREACHABLE"
    default_message = "Cannot reach GVM server. Check network connectivity."


class TlsError(ConnectionError):
    """TLS/SSL connection error."""

    code = "TLS_ERROR"
    default_message = "TLS connection failed. Check certificates."


class ConnectionTimeoutError(ConnectionError):
    """Connection timed out."""

    code = "CONNECTION_TIMEOUT"
    http_status = 504
    default_message = "Connection to GVM timed out."


class ConnectionRefusedError(ConnectionError):
    """Connection actively refused."""

    code = "CONNECTION_REFUSED"
    default_message = "Connection refused. Check if gvmd is running."


# =============================================================================
# Authentication Errors
# =============================================================================


class AuthenticationError(OpenvasMcpError):
    """Base class for authentication errors."""

    http_status = 401


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password."""

    code = "INVALID_CREDENTIALS"
    default_message = "Invalid username or password."

    @property
    def cli_hint(self) -> str:
        return "Check GVM_USERNAME and GVM_PASSWORD or run 'openvas configure'."


class PermissionDeniedError(AuthenticationError):
    """User lacks permission."""

    code = "PERMISSION_DENIED"
    http_status = 403
    default_message = "You don't have permission to perform this action."


# =============================================================================
# Validation Errors
# =============================================================================


class ValidationError(OpenvasMcpError):
    """Base class for validation errors."""

    http_status = 400


class InvalidUuidError(ValidationError):
    """Invalid UUID format."""

    code = "INVALID_UUID"
    default_message = "Invalid ID format. Expected UUID."


class InvalidHostError(ValidationError):
    """Invalid host format."""

    code = "INVALID_HOST"
    default_message = "Invalid host format. Use IP, CIDR, or hostname."


class InvalidFilterError(ValidationError):
    """Invalid filter syntax."""

    code = "INVALID_FILTER"
    default_message = "Invalid filter syntax."


class RequiredFieldError(ValidationError):
    """Required field is missing."""

    code = "REQUIRED_FIELD"
    default_message = "Required field is missing."


# =============================================================================
# Resource Errors
# =============================================================================


class ResourceError(OpenvasMcpError):
    """Base class for resource-related errors."""

    http_status = 404


class ResourceNotFoundError(ResourceError):
    """Resource does not exist."""

    code = "NOT_FOUND"
    default_message = "Resource not found."

    def __init__(
        self,
        resource_type: str,
        resource_id: Optional[str] = None,
        message: Optional[str] = None,
    ):
        if message is None:
            if resource_id:
                message = f"{resource_type.title()} not found: {resource_id}"
            else:
                message = f"{resource_type.title()} not found."
        details = ErrorDetails(resource_type=resource_type, resource_id=resource_id)
        super().__init__(message, details)

    @property
    def cli_hint(self) -> str:
        rt = self.details.resource_type or "resource"
        return f"Use 'openvas {rt} list' to see available {rt}s."


class ResourceInUseError(ResourceError):
    """Resource is in use and cannot be deleted."""

    code = "IN_USE"
    http_status = 409
    default_message = "Resource is in use and cannot be deleted."


class ResourceExistsError(ResourceError):
    """Resource already exists."""

    code = "ALREADY_EXISTS"
    http_status = 409
    default_message = "Resource already exists."


# =============================================================================
# Operation Errors
# =============================================================================


class OperationError(OpenvasMcpError):
    """Base class for operation errors."""

    http_status = 409


class ScanRunningError(OperationError):
    """Cannot modify while scan is running."""

    code = "SCAN_RUNNING"
    default_message = "Cannot modify task while scan is running."

    @property
    def cli_hint(self) -> str:
        return "Stop the scan first with 'openvas scan stop <id>'"


class ScanNotRunningError(OperationError):
    """Task is not running."""

    code = "SCAN_NOT_RUNNING"
    default_message = "Task is not running."


class ReportNotReadyError(OperationError):
    """Report is still being generated."""

    code = "REPORT_NOT_READY"
    default_message = "Report is still being generated. Try again later."


# =============================================================================
# Server Errors
# =============================================================================


class ServerError(OpenvasMcpError):
    """Base class for GVM server errors."""

    http_status = 502


class GvmInternalError(ServerError):
    """GVM server internal error."""

    code = "GVM_INTERNAL"
    default_message = "GVM server encountered an internal error."


class GvmUnavailableError(ServerError):
    """GVM server is unavailable."""

    code = "GVM_UNAVAILABLE"
    http_status = 503
    default_message = "GVM server is currently unavailable."


class GvmTimeoutError(ServerError):
    """GVM operation timed out."""

    code = "GVM_TIMEOUT"
    http_status = 504
    default_message = "GVM operation timed out."
