# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from unittest.mock import MagicMock
from xml.etree.ElementTree import Element, SubElement

from src.services.notes import NoteService


def test_list_notes() -> None:
    svc = NoteService(MagicMock())
    response = Element("get_notes_response", {"status": "200"})
    n = SubElement(response, "note", {"id": "11111111-1111-1111-1111-111111111111"})
    SubElement(n, "text").text = "x"
    svc._client.execute.return_value = response
    out = svc.list()
    assert out.total == 1
