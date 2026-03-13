"""Port list service implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from src.errors import ResourceNotFoundError
from src.utils import attr, collect, response_ok, text, to_int, validate_filter, validate_uuid

from .models import PortList, PortListListResponse

if TYPE_CHECKING:
    from src.infrastructure.client import GvmClient


class PortListService:
    """Service for managing port lists."""

    def __init__(self, client: GvmClient) -> None:
        self._client = client

    def get(self, port_list_id: str) -> PortList:
        port_list_id = validate_uuid(port_list_id, "port_list_id")

        def operation(gmp: Any) -> Any:
            return gmp.get_port_list(port_list_id=port_list_id)

        response: Element = self._client.execute(operation)
        if not response_ok(response):
            raise ResourceNotFoundError("port_list", port_list_id)

        port_list_elem = response.find("port_list")
        if port_list_elem is None:
            raise ResourceNotFoundError("port_list", port_list_id)

        return self._parse_port_list(port_list_elem)

    def list(self, filter_string: str = "") -> PortListListResponse:
        filter_string = validate_filter(filter_string)

        def operation(gmp: Any) -> Any:
            return gmp.get_port_lists(filter_string=filter_string or None)

        response: Element = self._client.execute(operation)
        port_lists = collect(response, "port_list", self._parse_port_list)

        return PortListListResponse(
            port_lists=port_lists,
            total=len(port_lists),
            filtered=len(port_lists),
        )

    def _parse_port_list(self, elem: Element) -> PortList:
        port_count = to_int(text(elem, "port_count"), 0)
        if port_count == 0:
            port_count = to_int(attr(elem, "port_count"), 0)

        return PortList(
            id=attr(elem, "id"),
            name=text(elem, "name"),
            port_count=port_count,
            comment=text(elem, "comment"),
        )
