"""User-scoped analytics and recommendation payloads."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DemoUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str


class ConceptMasteryRead(BaseModel):
    concept_id: UUID
    lecture_id: UUID
    lecture_title: str
    concept_name: str
    concept_slug: str
    mastery_score: float
    correct_count: int
    wrong_count: int
    prerequisite_concept_id: UUID | None = None
    is_weak: bool


class RecommendationRead(BaseModel):
    recommendation_id: UUID
    rank: int
    lecture_id: UUID | None = None
    lecture_title: str | None = None
    concept_id: UUID | None = None
    concept_name: str | None = None
    reason_code: str
    title: str
    message: str


class RecommendationsResponse(BaseModel):
    user_id: UUID
    recommendations: list[RecommendationRead]
