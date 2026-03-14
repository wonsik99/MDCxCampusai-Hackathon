"""Structured model outputs required from OpenAI or fallback providers."""

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ChoiceRead, LectureSummaryBlock


class LectureSummaryOutput(LectureSummaryBlock):
    pass


class ConceptExtractionItem(BaseModel):
    name: str
    slug: str
    description: str | None = None


class ConceptExtractionOutput(BaseModel):
    concepts: list[ConceptExtractionItem] = Field(default_factory=list)

    @field_validator("concepts")
    @classmethod
    def ensure_non_empty(cls, value: list[ConceptExtractionItem]) -> list[ConceptExtractionItem]:
        if not value:
            raise ValueError("At least one concept must be returned.")
        return value


class WrongAnswerExplanation(BaseModel):
    choice_id: str
    explanation: str


class QuizQuestionOutput(BaseModel):
    concept_slug: str
    prompt: str
    choices: list[ChoiceRead]
    correct_choice_id: str
    wrong_answer_explanations: list[WrongAnswerExplanation]

    @field_validator("choices")
    @classmethod
    def ensure_four_choices(cls, value: list[ChoiceRead]) -> list[ChoiceRead]:
        if len(value) != 4:
            raise ValueError("Each question must include exactly four choices.")
        return value

    def wrong_answer_explanations_as_dict(self) -> dict[str, str]:
        return {item.choice_id: item.explanation for item in self.wrong_answer_explanations}


class QuizGenerationOutput(BaseModel):
    questions: list[QuizQuestionOutput] = Field(default_factory=list)

    @field_validator("questions")
    @classmethod
    def ensure_questions(cls, value: list[QuizQuestionOutput]) -> list[QuizQuestionOutput]:
        if not value:
            raise ValueError("At least one quiz question must be returned.")
        return value


class WrongAnswerExplanationOutput(BaseModel):
    explanation: str


class RecommendationMessageItem(BaseModel):
    concept_slug: str
    title: str
    message: str


class RecommendationOutput(BaseModel):
    recommendations: list[RecommendationMessageItem] = Field(default_factory=list)
