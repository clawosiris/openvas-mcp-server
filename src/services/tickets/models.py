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
