"""AI service wrapper that switches between OpenAI and local fallback behavior."""

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
from app.services.ai_provider import BaseAIProvider, FallbackAIProvider, OpenAIProvider


class AIService:
    def __init__(self) -> None:
        settings = get_settings()
        self.fallback_provider = FallbackAIProvider()
        self.primary_provider: BaseAIProvider = (
            OpenAIProvider(settings) if settings.openai_api_key else self.fallback_provider
        )
        self._last_provider_name = self.primary_provider.provider_name
        self._last_used_fallback = self.primary_provider.used_fallback

    @property
    def metadata(self) -> AIUsageMetadata:
        return AIUsageMetadata(provider=self._last_provider_name, used_fallback=self._last_used_fallback)

    def summarize_lecture(self, text: str) -> LectureSummaryOutput:
        return LectureSummaryOutput.model_validate(self._run_with_fallback("summarize_lecture", text))

    def extract_concepts(self, text: str) -> ConceptExtractionOutput:
        return ConceptExtractionOutput.model_validate(self._run_with_fallback("extract_concepts", text))

    def generate_quiz_from_lecture(
        self,
        text: str,
        concepts: list[dict[str, str]],
        questions_per_concept: int,
    ) -> QuizGenerationOutput:
        return QuizGenerationOutput.model_validate(
            self._run_with_fallback("generate_quiz_from_lecture", text, concepts, questions_per_concept)
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
            self._run_with_fallback(
                "explain_wrong_answer",
                question,
                selected_answer,
                correct_answer,
                concept,
                lecture_summary,
            )
        )

    def generate_recommendation(
        self,
        weak_concepts: list[dict],
        prerequisite_chain: list[list[str]],
        mastery_data: list[dict],
    ) -> RecommendationOutput:
        return RecommendationOutput.model_validate(
            self._run_with_fallback(
                "generate_recommendation",
                weak_concepts,
                prerequisite_chain,
                mastery_data,
            )
        )

    def _run_with_fallback(self, method_name: str, *args):
        method = getattr(self.primary_provider, method_name)
        try:
            result = method(*args)
            self._last_provider_name = self.primary_provider.provider_name
            self._last_used_fallback = self.primary_provider.used_fallback
            return result
        except AIProviderError:
            if self.primary_provider is self.fallback_provider:
                raise
            fallback_method = getattr(self.fallback_provider, method_name)
            result = fallback_method(*args)
            self._last_provider_name = self.fallback_provider.provider_name
            self._last_used_fallback = True
            return result
