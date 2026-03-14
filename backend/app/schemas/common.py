"""Common schema primitives and error envelopes."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict | None = None


class AIUsageMetadata(BaseModel):
    provider: str
    used_fallback: bool = False


class ChoiceRead(BaseModel):
    choice_id: str
    text: str


class ConceptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str | None = None
    prerequisite_concept_id: UUID | None = None
    is_inferred: bool
    display_order: int


class LectureSummaryBlock(BaseModel):
    summary: str
    key_takeaways: list[str] = Field(default_factory=list)


class TimestampedRead(BaseModel):
    created_at: datetime
    updated_at: datetime
