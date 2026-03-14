# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from unittest.mock import MagicMock
from xml.etree.ElementTree import Element, SubElement

from src.services.tickets import TicketService


def test_list_tickets() -> None:
    svc = TicketService(MagicMock())
    response = Element("get_tickets_response", {"status": "200"})
    t = SubElement(response, "ticket", {"id": "11111111-1111-1111-1111-111111111111"})
    SubElement(t, "status").text = "open"
    svc._client.execute.return_value = response
    out = svc.list()
    assert out.total == 1
