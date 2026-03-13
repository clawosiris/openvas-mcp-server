from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.services.notes import NoteService

if TYPE_CHECKING:
    from mcp.server.fastmcp import FastMCP


def register_note_tools(server: FastMCP, service: NoteService) -> None:
    @server.tool(name="openvas_list_notes")
    def list_notes(filter: str = "") -> dict[str, Any]:
        return service.list(filter).model_dump()

    @server.tool(name="openvas_get_note")
    def get_note(note_id: str) -> dict[str, Any]:
        return service.get(note_id).model_dump()

    @server.tool(name="openvas_create_note")
    def create_note(text: str, nvt_oid: str = "") -> dict[str, Any]:
        return service.create(text_value=text, nvt_oid=nvt_oid).model_dump()

    @server.tool(name="openvas_update_note")
    def update_note(note_id: str, text: str) -> dict[str, Any]:
        return service.update(note_id, text).model_dump()

    @server.tool(name="openvas_delete_note")
    def delete_note(note_id: str) -> dict[str, Any]:
        return {"success": service.delete(note_id), "note_id": note_id}
