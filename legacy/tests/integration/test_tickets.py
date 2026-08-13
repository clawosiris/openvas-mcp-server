# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from __future__ import annotations

import pytest

from src.services.tickets import TicketService

pytestmark = pytest.mark.integration


def test_list_tickets(ticket_service: TicketService) -> None:
    """List tickets (mock server may return empty list)."""
    result = ticket_service.list()
    # Just verify the call succeeds and returns a valid response
    assert result is not None
    assert hasattr(result, "tickets")


def test_create_ticket(ticket_service: TicketService, result_id: str) -> None:
    """Create a ticket (requires a result from a scan)."""
    ticket = ticket_service.create(result_id=result_id, comment="integration test ticket")

    try:
        assert ticket.id
        assert ticket.comment == "integration test ticket"
    finally:
        ticket_service.delete(ticket.id)
