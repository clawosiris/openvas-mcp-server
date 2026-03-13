"""Task (scan) domain models."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status."""

    NEW = "New"
    REQUESTED = "Requested"
    RUNNING = "Running"
    STOP_REQUESTED = "Stop Requested"
    STOPPED = "Stopped"
    PAUSE_REQUESTED = "Pause Requested"
    PAUSED = "Paused"
    RESUME_REQUESTED = "Resume Requested"
    DONE = "Done"
    DELETE_REQUESTED = "Delete Requested"
    INTERRUPTED = "Interrupted"


class Scanner(BaseModel):
    """Scanner reference."""

    id: str
    name: str


class ScanConfig(BaseModel):
    """Scan configuration reference."""

    id: str
    name: str


class TargetRef(BaseModel):
    """Target reference."""

    id: str
    name: str


class LastReport(BaseModel):
    """Last report reference."""

    id: str
    timestamp: datetime | None = None


class Task(BaseModel):
    """Task (scan) domain model.

    Represents a scan task in GVM.
    """

    id: str = Field(description="Task UUID")
    name: str = Field(description="Task name")
    comment: str = Field(default="", description="Optional comment")
    status: TaskStatus = Field(description="Current task status")
    progress: int = Field(default=0, description="Scan progress (0-100)")
    target: TargetRef | None = Field(default=None, description="Associated target")
    scanner: Scanner | None = Field(default=None, description="Scanner used")
    config: ScanConfig | None = Field(default=None, description="Scan configuration")
    last_report: LastReport | None = Field(default=None, description="Most recent report")
    report_count: int = Field(default=0, description="Total number of reports")
    trend: str = Field(default="", description="Vulnerability trend")
    in_use: bool = Field(default=False, description="Whether task is in use")
    creation_time: datetime | None = Field(default=None, description="Creation timestamp")
    modification_time: datetime | None = Field(
        default=None, description="Last modification timestamp"
    )


class TaskCreateRequest(BaseModel):
    """Request model for creating a task."""

    name: str = Field(description="Task name", min_length=1)
    target_id: str = Field(description="Target UUID")
    config_id: str = Field(description="Scan config UUID")
    scanner_id: str | None = Field(default=None, description="Scanner UUID (optional)")
    comment: str = Field(default="", description="Optional comment")
    schedule_id: str | None = Field(default=None, description="Schedule UUID (optional)")
    alert_ids: list[str] = Field(default_factory=list, description="Alert UUIDs")


class TaskListResponse(BaseModel):
    """Response model for listing tasks."""

    tasks: list[Task] = Field(description="List of tasks")
    total: int = Field(description="Total number of tasks matching filter")
    filtered: int = Field(description="Number of tasks in this response")
