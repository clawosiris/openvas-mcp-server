from __future__ import annotations

from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from src.errors import ResourceNotFoundError
from src.utils import attr, collect, response_ok, text, validate_filter, validate_uuid

from .models import Ticket, TicketListResponse

if TYPE_CHECKING:
    from src.infrastructure.client import GvmClient


class TicketService:
    def __init__(self, client: GvmClient) -> None:
        self._client = client

    def list(self, filter_string: str = "") -> TicketListResponse:
        filter_string = validate_filter(filter_string)

        def operation(gmp: Any) -> Any:
            return gmp.get_tickets(filter_string=filter_string or None)

        response: Element = self._client.execute(operation)
        items = collect(response, "ticket", self._parse_ticket)
        return TicketListResponse(tickets=items, total=len(items), filtered=len(items))

    def get(self, ticket_id: str) -> Ticket:
        ticket_id = validate_uuid(ticket_id, "ticket_id")

        def operation(gmp: Any) -> Any:
            return gmp.get_ticket(ticket_id=ticket_id)

        response: Element = self._client.execute(operation)
        if not response_ok(response):
            raise ResourceNotFoundError("ticket", ticket_id)
        elem = response.find("ticket")
        if elem is None:
            raise ResourceNotFoundError("ticket", ticket_id)
        return self._parse_ticket(elem)

    def create(self, result_id: str, comment: str = "") -> Ticket:
        result_id = validate_uuid(result_id, "result_id")

        def operation(gmp: Any) -> Any:
            return gmp.create_ticket(result_id=result_id, comment=comment or None)

        response: Element = self._client.execute(operation)
        return self.get(attr(response, "id") or text(response, "id"))

    def update(self, ticket_id: str, status: str, comment: str = "") -> Ticket:
        ticket_id = validate_uuid(ticket_id, "ticket_id")

        def operation(gmp: Any) -> Any:
            return gmp.modify_ticket(ticket_id=ticket_id, status=status, comment=comment or None)

        self._client.execute(operation)
        return self.get(ticket_id)

    def delete(self, ticket_id: str) -> bool:
        ticket_id = validate_uuid(ticket_id, "ticket_id")

        def operation(gmp: Any) -> Any:
            return gmp.delete_ticket(ticket_id=ticket_id)

        response: Element = self._client.execute(operation)
        if attr(response, "status") == "404":
            raise ResourceNotFoundError("ticket", ticket_id)
        return response_ok(response)

    def _parse_ticket(self, elem: Element) -> Ticket:
        result_elem = elem.find("result")
        return Ticket(
            id=attr(elem, "id"),
            result_id=attr(result_elem, "id") if result_elem is not None else "",
            status=text(elem, "status"),
            comment=text(elem, "comment"),
        )
