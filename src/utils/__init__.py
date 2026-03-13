"""Utility functions."""

from src.errors import InvalidFilterError, InvalidHostError, InvalidUuidError

from .validators import validate_filter, validate_host, validate_hosts, validate_uuid
from .xml_helpers import (
    attr,
    child_attr,
    collect,
    response_ok,
    response_status,
    split_csv,
    text,
    to_bool,
    to_datetime,
    to_float,
    to_int,
)

__all__ = [
    # Errors (re-exported for convenience)
    "InvalidUuidError",
    "InvalidHostError",
    "InvalidFilterError",
    # Validators
    "validate_uuid",
    "validate_host",
    "validate_hosts",
    "validate_filter",
    # XML helpers
    "text",
    "attr",
    "child_attr",
    "to_int",
    "to_float",
    "to_bool",
    "to_datetime",
    "split_csv",
    "collect",
    "response_ok",
    "response_status",
]
