from typing import Literal
from uuid import uuid4
from pydantic import BaseModel, Field, ConfigDict, field_validator

Category = Literal["network", "vpn", "account", "software", "device", "other"]


class CleanModel(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")


class Report(CleanModel):
    text: str = Field(min_length=8, max_length=4000)
    location: str = Field(default="", max_length=160)
    requester: str = Field(default="Anonymous", min_length=1, max_length=80)
    request_id: str = Field(default_factory=lambda: str(uuid4()), min_length=8, max_length=120, pattern=r"^[\w.:-]+$")
    mode: Literal["demo", "live"] = "demo"
    channel: Literal["portal", "email", "webhook"] = "portal"


class Citation(CleanModel):
    id: str = Field(max_length=100)
    title: str = Field(max_length=180)
    excerpt: str = Field(max_length=6000)
    category: Category
    trusted: bool = False
    synthetic: bool = False
    score: float = 0


class Trace(CleanModel):
    name: str = Field(max_length=100)
    detail: str = Field(max_length=1500)
    kind: str = Field(max_length=30)


class TicketIn(Report):
    mode_used: str = Field(max_length=30)
    category: Category
    priority: Literal["normal", "high", "urgent"]
    summary: str = Field(min_length=1, max_length=200)
    response: str = Field(min_length=1, max_length=6000)
    steps: list[str] = Field(max_length=8)
    citations: list[Citation] = Field(max_length=5)
    flags: list[str] = Field(max_length=20)
    grounded: bool
    automation_allowed: bool
    trace: list[Trace] = Field(max_length=20)
    execution_id: str = Field(default="", max_length=100)

    @field_validator("steps")
    @classmethod
    def limit_steps(cls, value):
        if any(len(step) > 1500 for step in value):
            raise ValueError("Each step must be at most 1500 characters")
        return value


class Approval(CleanModel):
    version: int = Field(ge=1)
    response: str = Field(min_length=8, max_length=6000)


class Resolution(CleanModel):
    version: int = Field(ge=1)
    note: str = Field(min_length=3, max_length=1000)


class KnowledgeIn(CleanModel):
    title: str = Field(min_length=3, max_length=180)
    category: Category
    content: str = Field(min_length=40, max_length=16000)
    trusted: bool = False


class Query(CleanModel):
    query: str = Field(min_length=3, max_length=4000)
    category: Category | None = None


class Receipt(CleanModel):
    event_id: str = Field(min_length=1, max_length=100)
    execution_id: str = Field(default="", max_length=100)
