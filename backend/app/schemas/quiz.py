"""Quiz session request and response payloads."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.quiz_session import QuizSessionStatus
from app.schemas.common import ChoiceRead


class QuizSessionStartRequest(BaseModel):
    lecture_id: UUID
    question_limit: int | None = Field(default=None, ge=1, le=50)


class QuizSessionStartResponse(BaseModel):
    session_id: UUID
    lecture_id: UUID
    lecture_title: str
    lecture_summary: str
    concept_ids: list[UUID]
    session_status: QuizSessionStatus
    total_questions: int


class QuizSessionQuestionRead(BaseModel):
    question_id: UUID
    prompt: str
    concept_id: UUID
    concept_name: str
    choices: list[ChoiceRead]
    sequence: int


class QuizSessionQuestionsResponse(BaseModel):
    session_id: UUID
    questions: list[QuizSessionQuestionRead]


class QuizSessionRead(BaseModel):
    session_id: UUID
    lecture_id: UUID
    lecture_title: str
    status: QuizSessionStatus
    total_questions: int
    answered_questions: int
    correct_answers: int
    started_at: datetime
    finished_at: datetime | None = None


class SubmitAnswerRequest(BaseModel):
    question_id: UUID
    selected_choice_id: str = Field(min_length=1, max_length=8)
    response_time_ms: int = Field(ge=0, le=600000)


class ConceptMasterySnapshot(BaseModel):
    concept_id: UUID
    concept_name: str
    mastery_score: float
    correct_count: int
    wrong_count: int


class SubmitAnswerResponse(BaseModel):
    session_id: UUID
    question_id: UUID
    is_correct: bool
    correct_choice_id: str
    correct_choice_text: str
    explanation: str
    mastery: ConceptMasterySnapshot
    is_weak_concept: bool


class SessionConceptPerformance(BaseModel):
    concept_id: UUID
    concept_name: str
    correct: int
    wrong: int
    mastery_score: float


class StarJarUpdateRead(BaseModel):
    week_start_date: date
    week_end_date: date
    study_time_ms: int
    accuracy_ratio: float
    stars_awarded: int


class FinishSessionResponse(BaseModel):
    session_id: UUID
    score: float
    correct_answers: int
    total_questions: int
    concept_performance: list[SessionConceptPerformance]
    weak_concepts: list[str]
    stars_awarded: int
    star_jar_update: "StarJarUpdateRead"
    current_jar: "StarJarRead"
    recommendations: list["RecommendationRead"]


from app.schemas.user import RecommendationRead, StarJarRead  # noqa: E402

FinishSessionResponse.model_rebuild()
