# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from pydantic import BaseModel, Field


class Note(BaseModel):
    id: str
    text: str = ""
    hosts: list[str] = Field(default_factory=list)
    nvt_oid: str = ""
    active: bool = True


class NoteListResponse(BaseModel):
    notes: list[Note]
    total: int
    filtered: int
