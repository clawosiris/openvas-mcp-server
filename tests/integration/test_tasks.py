# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

from collections.abc import Iterator
from uuid import uuid4

import pytest

from src.errors import ResourceNotFoundError
from src.services.targets import TargetCreateRequest, TargetService
from src.services.tasks import TaskCreateRequest, TaskService, TaskStatus

pytestmark = pytest.mark.integration


@pytest.fixture
def task_target(target_service: TargetService) -> Iterator[str]:
    target = target_service.create(
        TargetCreateRequest(
            name=f"integration-task-target-{uuid4().hex[:8]}",
            hosts=["127.0.0.1"],
        )
    )
    try:
        yield target.id
    finally:
        target_service.delete(target.id, ultimate=True)


def _create_task(
    task_service: TaskService,
    *,
    task_target: str,
    scan_config_id: str,
    scanner_id: str,
) -> tuple[str, str]:
    task = task_service.create(
        TaskCreateRequest(
            name=f"integration-task-{uuid4().hex[:8]}",
            target_id=task_target,
            config_id=scan_config_id,
            scanner_id=scanner_id,
            comment="integration task",
        )
    )
    return task.id, task.name


def test_create_task(
    task_service: TaskService,
    task_target: str,
    scan_config_id: str,
    scanner_id: str,
) -> None:
    task_id, task_name = _create_task(
        task_service,
        task_target=task_target,
        scan_config_id=scan_config_id,
        scanner_id=scanner_id,
    )

    try:
        task = task_service.get(task_id)
        assert task.id == task_id
        assert task.name == task_name
        assert task.target is not None
        assert task.target.id == task_target
        assert task.config is not None
        assert task.config.id == scan_config_id
    finally:
        task_service.delete(task_id, ultimate=True)


def test_list_tasks(
    task_service: TaskService,
    task_target: str,
    scan_config_id: str,
    scanner_id: str,
) -> None:
    task_id, _ = _create_task(
        task_service,
        task_target=task_target,
        scan_config_id=scan_config_id,
        scanner_id=scanner_id,
    )

    try:
        result = task_service.list()
        assert any(item.id == task_id for item in result.tasks)
    finally:
        task_service.delete(task_id, ultimate=True)


def test_start_task(
    task_service: TaskService,
    task_target: str,
    scan_config_id: str,
    scanner_id: str,
) -> None:
    task_id, _ = _create_task(
        task_service,
        task_target=task_target,
        scan_config_id=scan_config_id,
        scanner_id=scanner_id,
    )

    try:
        report_id = task_service.start(task_id)
        assert report_id

        task = task_service.get(task_id)
        assert task.status in {TaskStatus.RUNNING, TaskStatus.REQUESTED, TaskStatus.DONE}
    finally:
        try:
            task_service.stop(task_id)
        except Exception:
            pass
        task_service.delete(task_id, ultimate=True)


def test_stop_task(
    task_service: TaskService,
    task_target: str,
    scan_config_id: str,
    scanner_id: str,
) -> None:
    task_id, _ = _create_task(
        task_service,
        task_target=task_target,
        scan_config_id=scan_config_id,
        scanner_id=scanner_id,
    )

    try:
        task_service.start(task_id)
        assert task_service.stop(task_id) is True
    finally:
        task_service.delete(task_id, ultimate=True)


def test_delete_task(
    task_service: TaskService,
    task_target: str,
    scan_config_id: str,
    scanner_id: str,
) -> None:
    task_id, _ = _create_task(
        task_service,
        task_target=task_target,
        scan_config_id=scan_config_id,
        scanner_id=scanner_id,
    )

    assert task_service.delete(task_id, ultimate=True) is True
    with pytest.raises(ResourceNotFoundError):
        task_service.get(task_id)
