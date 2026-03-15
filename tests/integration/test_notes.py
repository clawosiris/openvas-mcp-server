# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

from uuid import uuid4

import pytest

from src.errors import ResourceNotFoundError
from src.services.notes import NoteService

pytestmark = pytest.mark.integration

TEST_NVT_OID = "1.3.6.1.4.1.25623.1.0.100000"


def _make_note_text() -> str:
    return f"integration-note-{uuid4().hex[:8]}"


def test_create_note(note_service: NoteService) -> None:
    note = note_service.create(_make_note_text(), nvt_oid=TEST_NVT_OID, hosts=["127.0.0.1"])

    try:
        assert note.id
        assert note.text.startswith("integration-note-")
        assert note.nvt_oid == TEST_NVT_OID
    finally:
        note_service.delete(note.id)


def test_list_notes(note_service: NoteService) -> None:
    note = note_service.create(_make_note_text(), nvt_oid=TEST_NVT_OID, hosts=["127.0.0.1"])

    try:
        result = note_service.list()
        assert any(item.id == note.id for item in result.notes)
    finally:
        note_service.delete(note.id)


def test_delete_note(note_service: NoteService) -> None:
    note = note_service.create(_make_note_text(), nvt_oid=TEST_NVT_OID, hosts=["127.0.0.1"])

    assert note_service.delete(note.id) is True
    with pytest.raises(ResourceNotFoundError):
        note_service.get(note.id)
