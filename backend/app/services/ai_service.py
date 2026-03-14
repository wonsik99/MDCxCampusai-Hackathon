"""AI service wrapper that delegates to OpenAI. Requires a valid API key."""

from __future__ import annotations

from app.core.config import get_settings
from app.core.exceptions import AIProviderError
from app.schemas.ai import (
    ConceptExtractionOutput,
    LectureSummaryOutput,
    RecommendationOutput,
    WrongAnswerExplanationOutput,
    QuizGenerationOutput,
)
from app.schemas.common import AIUsageMetadata
from app.services.ai_provider import OpenAIProvider


class AIService:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.openai_api_key:
            raise AIProviderError("OPENAI_API_KEY is required. Set it in .env to use the application.")
        self._provider = OpenAIProvider(settings)

    @property
    def metadata(self) -> AIUsageMetadata:
        return AIUsageMetadata(provider=self._provider.provider_name, used_fallback=False)

    def summarize_lecture(self, text: str) -> LectureSummaryOutput:
        return LectureSummaryOutput.model_validate(self._provider.summarize_lecture(text))

    def extract_concepts(self, text: str) -> ConceptExtractionOutput:
        return ConceptExtractionOutput.model_validate(self._provider.extract_concepts(text))

    def generate_quiz_from_lecture(
        self,
        text: str,
        concepts: list[dict[str, str]],
        questions_per_concept: int,
    ) -> QuizGenerationOutput:
        return QuizGenerationOutput.model_validate(
            self._provider.generate_quiz_from_lecture(text, concepts, questions_per_concept)
        )

    def explain_wrong_answer(
        self,
        question: str,
        selected_answer: str,
        correct_answer: str,
        concept: str,
        lecture_summary: str,
    ) -> WrongAnswerExplanationOutput:
        return WrongAnswerExplanationOutput.model_validate(
            self._provider.explain_wrong_answer(question, selected_answer, correct_answer, concept, lecture_summary)
        )

    def generate_recommendation(
        self,
        weak_concepts: list[dict],
        prerequisite_chain: list[list[str]],
        mastery_data: list[dict],
    ) -> RecommendationOutput:
        return RecommendationOutput.model_validate(
            self._provider.generate_recommendation(weak_concepts, prerequisite_chain, mastery_data)
        )
