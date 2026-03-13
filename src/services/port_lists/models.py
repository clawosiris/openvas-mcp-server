"""Port list domain models."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PortList(BaseModel):
    """Port list model."""

    id: str = Field(description="Port list UUID")
    name: str = Field(description="Port list name")
    port_count: int = Field(default=0, description="Number of ports in list")
    comment: str = Field(default="", description="Optional description")


class PortListListResponse(BaseModel):
    """Response model for port list list."""

    port_lists: list[PortList] = Field(description="List of port lists")
    total: int = Field(description="Total number of port lists")
    filtered: int = Field(description="Number returned in response")
