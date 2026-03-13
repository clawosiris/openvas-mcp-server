from __future__ import annotations

import builtins
from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from src.errors import ResourceNotFoundError
from src.utils import attr, collect, response_ok, text, validate_filter, validate_uuid

from .models import Note, NoteListResponse

if TYPE_CHECKING:
    from src.infrastructure.client import GvmClient


class NoteService:
    def __init__(self, client: GvmClient) -> None:
        self._client = client

    def list(self, filter_string: str = "") -> NoteListResponse:
        filter_string = validate_filter(filter_string)

        def operation(gmp: Any) -> Any:
            return gmp.get_notes(filter_string=filter_string or None)

        response: Element = self._client.execute(operation)
        notes = collect(response, "note", self._parse_note)
        return NoteListResponse(notes=notes, total=len(notes), filtered=len(notes))

    def get(self, note_id: str) -> Note:
        note_id = validate_uuid(note_id, "note_id")

        def operation(gmp: Any) -> Any:
            return gmp.get_note(note_id=note_id)

        response: Element = self._client.execute(operation)
        if not response_ok(response):
            raise ResourceNotFoundError("note", note_id)
        elem = response.find("note")
        if elem is None:
            raise ResourceNotFoundError("note", note_id)
        return self._parse_note(elem)

    def create(
        self,
        text_value: str,
        nvt_oid: str = "",
        hosts: builtins.list[str] | None = None,
    ) -> Note:
        def operation(gmp: Any) -> Any:
            return gmp.create_note(text=text_value, nvt_oid=nvt_oid or None, hosts=hosts or None)

        response: Element = self._client.execute(operation)
        return self.get(attr(response, "id") or text(response, "id"))

    def update(self, note_id: str, text_value: str) -> Note:
        note_id = validate_uuid(note_id, "note_id")

        def operation(gmp: Any) -> Any:
            return gmp.modify_note(note_id=note_id, text=text_value)

        self._client.execute(operation)
        return self.get(note_id)

    def delete(self, note_id: str) -> bool:
        note_id = validate_uuid(note_id, "note_id")

        def operation(gmp: Any) -> Any:
            return gmp.delete_note(note_id=note_id)

        response: Element = self._client.execute(operation)
        if attr(response, "status") == "404":
            raise ResourceNotFoundError("note", note_id)
        return response_ok(response)

    def _parse_note(self, elem: Element) -> Note:
        hosts = [h.text.strip() for h in elem.findall("hosts/host") if h.text]
        return Note(
            id=attr(elem, "id"),
            text=text(elem, "text"),
            hosts=hosts,
            nvt_oid=text(elem, "nvt/oid"),
            active=text(elem, "active", "1") in {"1", "true", "yes"},
        )
