"""System domain models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GvmVersion(BaseModel):
    """GVM version information."""

    gmp_version: str = Field(description="GMP protocol version")
    backend_version: str = Field(default="", description="Backend (gvmd) version")
    backend_name: str = Field(default="", description="Backend name")
