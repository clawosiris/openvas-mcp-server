from pydantic import BaseModel, Field


class Note(BaseModel):
    id: str
    text: str = ""
    hosts: list[str] = Field(default_factory=list)
    nvt_oid: str = ""
    active: bool = True


class NoteListResponse(BaseModel):
    notes: list[Note]
    total: int
    filtered: int
