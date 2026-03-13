"""Input validation utilities."""

from __future__ import annotations

import ipaddress
import re
from typing import Sequence

from openvas_mcp.errors import InvalidFilterError, InvalidHostError, InvalidUuidError

# UUID pattern (GMP uses standard UUIDs)
UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

# Hostname pattern
HOSTNAME_PATTERN = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
)

# Dangerous characters in filter strings
FILTER_DANGEROUS_CHARS = re.compile(r"[<>&;'\"]")


def validate_uuid(value: str, field_name: str = "id") -> str:
    """Validate that value is a valid UUID.

    Args:
        value: String to validate.
        field_name: Name of field for error messages.

    Returns:
        Validated UUID string (lowercase).

    Raises:
        InvalidUuidError: If not a valid UUID.
    """
    if not value:
        raise InvalidUuidError(f"{field_name} is required")

    value = value.strip().lower()
    if not UUID_PATTERN.match(value):
        raise InvalidUuidError(f"Invalid UUID for {field_name}: {value}")

    return value


def validate_host(host: str) -> str:
    """Validate a single host (IP, CIDR, or hostname).

    Args:
        host: Host string to validate.

    Returns:
        Validated host string.

    Raises:
        InvalidHostError: If host format is invalid.
    """
    host = host.strip()
    if not host:
        raise InvalidHostError("Host cannot be empty")

    # Try IP address
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass

    # Try CIDR notation
    try:
        ipaddress.ip_network(host, strict=False)
        return host
    except ValueError:
        pass

    # Try hostname
    if HOSTNAME_PATTERN.match(host):
        return host

    raise InvalidHostError(f"Invalid host format: {host}")


def validate_hosts(hosts: Sequence[str], field_name: str = "hosts") -> list[str]:
    """Validate a list of hosts.

    Args:
        hosts: List of host strings.
        field_name: Name of field for error messages.

    Returns:
        List of validated host strings.

    Raises:
        InvalidHostError: If any host is invalid.
    """
    if not hosts:
        raise InvalidHostError(f"{field_name} cannot be empty")

    return [validate_host(h) for h in hosts]


def validate_filter(filter_string: str) -> str:
    """Validate and sanitize a GMP filter string.

    Args:
        filter_string: Filter string to validate.

    Returns:
        Sanitized filter string.

    Raises:
        InvalidFilterError: If filter contains dangerous characters.
    """
    if not filter_string:
        return ""

    if FILTER_DANGEROUS_CHARS.search(filter_string):
        raise InvalidFilterError("Filter contains invalid characters")

    return filter_string.strip()
