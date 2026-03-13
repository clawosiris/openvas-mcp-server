from pydantic import BaseModel, Field


class Override(BaseModel):
    id: str
    text: str = ""
    nvt_oid: str = ""
    hosts: list[str] = Field(default_factory=list)
    severity: str = ""


class OverrideListResponse(BaseModel):
    overrides: list[Override]
    total: int
    filtered: int
