from pydantic import BaseModel


class Policy(BaseModel):
    id: str
    name: str


class PolicyListResponse(BaseModel):
    policies: list[Policy]
    total: int


class ComplianceStatus(BaseModel):
    target_id: str
    compliant: bool
    passed: int = 0
    failed: int = 0
