# SPDX-License-Identifier: AGPL-3.0-or-later
# SPDX-FileCopyrightText: 2026 Greenbone AG

from pydantic import BaseModel


class Ticket(BaseModel):
    id: str
    result_id: str = ""
    status: str = ""
    comment: str = ""


class TicketListResponse(BaseModel):
    tickets: list[Ticket]
    total: int
    filtered: int
