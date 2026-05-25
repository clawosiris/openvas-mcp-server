"""Tool registration for gvm_mcp."""

from .extraction import register_extraction_tools
from .reports import register_report_tools
from .scans import register_scan_tools
from .targets import register_target_tools
from .vulns import register_vulnerability_tools

__all__ = [
    "register_target_tools",
    "register_scan_tools",
    "register_report_tools",
    "register_vulnerability_tools",
    "register_extraction_tools",
]
