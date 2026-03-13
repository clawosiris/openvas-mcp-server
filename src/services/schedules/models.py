"""Schedule domain models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Schedule(BaseModel):
    """Schedule model."""

    id: str = Field(description="Schedule UUID")
    name: str = Field(description="Schedule name")
    first_time: datetime | None = Field(default=None, description="First run time")
    period_months: int = Field(default=0, description="Period months")
    period_days: int = Field(default=0, description="Period days")
    period_hours: int = Field(default=0, description="Period hours")
    period_minutes: int = Field(default=0, description="Period minutes")
    timezone: str = Field(default="UTC", description="Schedule timezone")
    comment: str = Field(default="", description="Optional description")


class ScheduleListResponse(BaseModel):
    """Response model for schedule list."""

    schedules: list[Schedule] = Field(description="List of schedules")
    total: int = Field(description="Total number of schedules")
    filtered: int = Field(description="Number returned in response")
