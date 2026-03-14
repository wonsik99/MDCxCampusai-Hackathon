"""User-scoped analytics, recommendation, and motivation payloads."""

from datetime import date
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


class StarJarRead(BaseModel):
    jar_id: UUID
    week_start_date: date
    week_end_date: date
    capacity_stars: int
    earned_stars: int
    fill_ratio: float
    study_time_ms: int
    sessions_count: int
    average_accuracy: float
    is_current: bool
    is_complete: bool


class RecommendationsResponse(BaseModel):
    user_id: UUID
    recommendations: list[RecommendationRead]


class StarJarsResponse(BaseModel):
    user_id: UUID
    current_jar: StarJarRead | None = None
    history: list[StarJarRead]
