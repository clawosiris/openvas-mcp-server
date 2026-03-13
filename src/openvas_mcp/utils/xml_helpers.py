"""XML to model conversion utilities."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional, TypeVar
from xml.etree.ElementTree import Element

T = TypeVar("T")


def text(element: Element, path: str, default: str = "") -> str:
    """Get text content of first matching child element.

    Args:
        element: Parent XML element.
        path: XPath-like path to child element.
        default: Default value if not found.

    Returns:
        Text content or default.
    """
    child = element.find(path)
    if child is not None and child.text:
        return child.text.strip()
    return default


def attr(element: Element, name: str, default: str = "") -> str:
    """Get attribute value from element.

    Args:
        element: XML element.
        name: Attribute name.
        default: Default value if not found.

    Returns:
        Attribute value or default.
    """
    return element.get(name, default)


def child_attr(element: Element, path: str, name: str = "id") -> Optional[str]:
    """Get attribute from first matching child element.

    Args:
        element: Parent XML element.
        path: XPath to child element.
        name: Attribute name to retrieve.

    Returns:
        Attribute value or None.
    """
    child = element.find(path)
    if child is not None:
        return child.get(name)
    return None


def to_int(value: Optional[str], default: int = 0) -> int:
    """Convert string to integer with default.

    Args:
        value: String value to convert.
        default: Default if value is None or invalid.

    Returns:
        Integer value.
    """
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def to_float(value: Optional[str], default: float = 0.0) -> float:
    """Convert string to float with default.

    Args:
        value: String value to convert.
        default: Default if value is None or invalid.

    Returns:
        Float value.
    """
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def to_bool(value: Optional[str], default: bool = False) -> bool:
    """Convert string to boolean.

    Args:
        value: String value ('1', 'true', 'yes' for True).
        default: Default if value is None.

    Returns:
        Boolean value.
    """
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes")


def to_datetime(value: Optional[str]) -> Optional[datetime]:
    """Parse ISO datetime string.

    Args:
        value: ISO format datetime string.

    Returns:
        datetime object or None if invalid.
    """
    if not value:
        return None
    try:
        # Handle GMP datetime format
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def split_csv(value: str, separator: str = ",") -> list[str]:
    """Split CSV string into list, stripping whitespace.

    Args:
        value: Comma-separated string.
        separator: Separator character.

    Returns:
        List of stripped values, empty strings excluded.
    """
    if not value:
        return []
    return [v.strip() for v in value.split(separator) if v.strip()]


def collect(
    element: Element,
    path: str,
    converter: Callable[[Element], T],
) -> list[T]:
    """Collect and convert all matching elements.

    Args:
        element: Parent XML element.
        path: XPath to child elements.
        converter: Function to convert each element.

    Returns:
        List of converted objects.
    """
    return [converter(e) for e in element.findall(path)]


def response_ok(element: Element) -> bool:
    """Check if GMP response indicates success.

    Args:
        element: GMP response element.

    Returns:
        True if status starts with '2'.
    """
    status = element.get("status", "")
    return status.startswith("2")


def response_status(element: Element) -> dict[str, Any]:
    """Extract status information from GMP response.

    Args:
        element: GMP response element.

    Returns:
        Dict with status, status_text, and success flag.
    """
    status = element.get("status", "")
    status_text = element.get("status_text", "")
    return {
        "status": status,
        "status_text": status_text,
        "success": status.startswith("2"),
    }
