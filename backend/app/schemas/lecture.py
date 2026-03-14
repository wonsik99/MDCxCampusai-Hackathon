"""Lecture upload, detail, and quiz generation API contracts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.lecture import LectureSourceType
from app.schemas.common import AIUsageMetadata, ConceptRead, LectureSummaryBlock


class LectureListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    source_type: LectureSourceType
    summary: str | None = None
    concept_count: int = 0
    question_count: int = 0
    created_at: datetime


class LectureDetailResponse(BaseModel):
    id: UUID
    title: str
    source_type: LectureSourceType
    original_filename: str | None = None
    summary_block: LectureSummaryBlock
    concepts: list[ConceptRead]
    question_count: int
    quiz_generated: bool
    ai_metadata: AIUsageMetadata
    created_at: datetime


class LectureUploadResponse(BaseModel):
    lecture: LectureDetailResponse
    source_type: LectureSourceType
    cleaned_text_length: int


class QuizGenerationRequest(BaseModel):
    force_regenerate: bool = False
    questions_per_concept: int = Field(default=2, ge=1, le=5)


class QuizGenerationResponse(BaseModel):
    lecture_id: UUID
    question_count: int
    concept_coverage: list[str]
    generated: bool
    ai_metadata: AIUsageMetadata
