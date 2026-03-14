# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

"""Note service module."""

from .models import Note, NoteListResponse
from .service import NoteService

__all__ = ["Note", "NoteListResponse", "NoteService"]
