"""OpenAI and fallback providers for structured educational content generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
import logging

from openai import OpenAI

from app.core.config import Settings
from app.core.exceptions import AIProviderError
from app.schemas.ai import (
    ConceptExtractionOutput,
    LectureSummaryOutput,
    RecommendationOutput,
    WrongAnswerExplanationOutput,
    QuizGenerationOutput,
)
from app.utils.text import extract_keyword_concepts, summarize_text_fallback

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    provider_name: str
    used_fallback: bool

    @abstractmethod
    def summarize_lecture(self, text: str) -> LectureSummaryOutput:
        raise NotImplementedError

    @abstractmethod
    def extract_concepts(self, text: str) -> ConceptExtractionOutput:
        raise NotImplementedError

    @abstractmethod
    def generate_quiz_from_lecture(
        self,
        text: str,
        concepts: list[dict[str, str]],
        questions_per_concept: int,
    ) -> QuizGenerationOutput:
        raise NotImplementedError

    @abstractmethod
    def explain_wrong_answer(
        self,
        question: str,
        selected_answer: str,
        correct_answer: str,
        concept: str,
        lecture_summary: str,
    ) -> WrongAnswerExplanationOutput:
        raise NotImplementedError

    @abstractmethod
    def generate_recommendation(
        self,
        weak_concepts: list[dict],
        prerequisite_chain: list[list[str]],
        mastery_data: list[dict],
    ) -> RecommendationOutput:
        raise NotImplementedError


class OpenAIProvider(BaseAIProvider):
    provider_name = "openai"
    used_fallback = False

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise AIProviderError("OpenAI API key is missing.")
        self.model = settings.openai_model
        self.client = OpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds)

    def summarize_lecture(self, text: str) -> LectureSummaryOutput:
        prompt = (
            "Summarize the lecture for a struggling student. Return a concise summary and 3-5 key takeaways. "
            "Focus on concepts that should become quiz targets."
        )
        return self._parse_response(prompt, text, LectureSummaryOutput)

    def extract_concepts(self, text: str) -> ConceptExtractionOutput:
        prompt = (
            "Extract the core quiz-worthy concepts from the lecture. "
            "Return 3-6 concepts with a stable slug and short student-facing description."
        )
        return self._parse_response(prompt, text, ConceptExtractionOutput)

    def generate_quiz_from_lecture(
        self,
        text: str,
        concepts: list[dict[str, str]],
        questions_per_concept: int,
    ) -> QuizGenerationOutput:
        compact_text = _trim_text_for_generation(text, max_chars=18000)
        concept_list = "\n".join(f"- {concept['name']} ({concept['slug']}): {concept['description']}" for concept in concepts)
        prompt = (
            "You are generating multiple-choice study questions from lecture notes.\n"
            "Rules:\n"
            f"- Generate exactly {questions_per_concept} questions per concept.\n"
            "- Each question must belong to exactly one concept_slug from the provided concept list.\n"
            "- Each question must have exactly 4 answer choices.\n"
            "- Include wrong-answer explanations for the 3 incorrect choices only.\n"
            "- Make distractors plausible for struggling learners.\n\n"
            f"Concept list:\n{concept_list}\n\n"
            f"Lecture text:\n{compact_text}"
        )
        return self._parse_response(
            "Generate quiz questions as structured JSON.",
            prompt,
            QuizGenerationOutput,
            max_output_tokens=5000,
            truncation="auto",
        )

    def explain_wrong_answer(
        self,
        question: str,
        selected_answer: str,
        correct_answer: str,
        concept: str,
        lecture_summary: str,
    ) -> WrongAnswerExplanationOutput:
        prompt = (
            "Explain why the selected answer is wrong and why the correct answer is better. "
            "Keep it to 2-3 sentences for a student who is still building the concept.\n"
            f"Concept: {concept}\nLecture summary: {lecture_summary}\nQuestion: {question}\n"
            f"Selected answer: {selected_answer}\nCorrect answer: {correct_answer}"
        )
        return self._parse_response("Return a single explanation field.", prompt, WrongAnswerExplanationOutput)

    def generate_recommendation(
        self,
        weak_concepts: list[dict],
        prerequisite_chain: list[list[str]],
        mastery_data: list[dict],
    ) -> RecommendationOutput:
        prompt = (
            "Write actionable, prerequisite-aware study recommendations for a struggling student. "
            "Keep recommendations ordered as provided and specific about what to review next.\n"
            f"Weak concepts: {weak_concepts}\nPrerequisite chains: {prerequisite_chain}\nMastery: {mastery_data}"
        )
        return self._parse_response("Return one recommendation entry per weak concept in order.", prompt, RecommendationOutput)

    def _parse_response(self, system_prompt: str, user_prompt: str, schema: type, **kwargs) -> object:
        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                text_format=schema,
                **kwargs,
            )
            parsed = getattr(response, "output_parsed", None)
            if parsed is None:
                raise AIProviderError("OpenAI returned an empty structured response.")
            return schema.model_validate(parsed.model_dump() if hasattr(parsed, "model_dump") else parsed)
        except AIProviderError:
            raise
        except Exception as exc:  # pragma: no cover - network/runtime dependent
            logger.exception("OpenAI structured output generation failed for schema %s", schema.__name__)
            raise AIProviderError(
                "Failed to generate structured OpenAI output.",
                extra={"provider_message": f"{exc.__class__.__name__}: {exc}"},
            ) from exc


class FallbackAIProvider(BaseAIProvider):
    provider_name = "fallback"
    used_fallback = True

    def summarize_lecture(self, text: str) -> LectureSummaryOutput:
        summary = summarize_text_fallback(text)
        takeaways = [segment.strip() for segment in summary.split(". ") if segment.strip()][:3]
        if not takeaways:
            takeaways = ["Review the lecture in smaller chunks and focus on the main definitions."]
        return LectureSummaryOutput(summary=summary, key_takeaways=takeaways)

    def extract_concepts(self, text: str) -> ConceptExtractionOutput:
        return ConceptExtractionOutput(concepts=extract_keyword_concepts(text))

    def generate_quiz_from_lecture(
        self,
        text: str,
        concepts: list[dict[str, str]],
        questions_per_concept: int,
    ) -> QuizGenerationOutput:
        questions = []
        choice_ids = ["A", "B", "C", "D"]
        concept_names = [concept["name"] for concept in concepts]
        for concept in concepts:
            for index in range(questions_per_concept):
                correct_text = concept["description"] or f"The lecture's main idea about {concept['name']}."
                distractors = [
                    f"A detail about {name} without the main definition."
                    for name in concept_names
                    if name != concept["name"]
                ][:3]
                while len(distractors) < 3:
                    distractors.append(f"A partially related fact that does not define {concept['name']}.")
                choices = [correct_text, *distractors[:3]]
                question_choices = [{"choice_id": choice_ids[i], "text": choices[i]} for i in range(4)]
                questions.append(
                    {
                        "concept_slug": concept["slug"],
                        "prompt": f"Question {index + 1}: Which option best describes {concept['name']} in this lecture?",
                        "choices": question_choices,
                        "correct_choice_id": "A",
                        "wrong_answer_explanations": {
                            "B": f"This option mentions a nearby idea, but it misses the core meaning of {concept['name']}.",
                            "C": f"This distractor sounds plausible, but the lecture uses {concept['name']} differently.",
                            "D": f"This answer is too vague to explain {concept['name']} correctly.",
                        },
                    }
                )
        return QuizGenerationOutput.model_validate({"questions": questions})

    def explain_wrong_answer(
        self,
        question: str,
        selected_answer: str,
        correct_answer: str,
        concept: str,
        lecture_summary: str,
    ) -> WrongAnswerExplanationOutput:
        return WrongAnswerExplanationOutput(
            explanation=(
                f"For {concept}, the stronger answer is '{correct_answer}' because it matches the lecture summary: "
                f"{lecture_summary[:160]}. Your selected answer, '{selected_answer}', leaves out the central idea."
            )
        )

    def generate_recommendation(
        self,
        weak_concepts: list[dict],
        prerequisite_chain: list[list[str]],
        mastery_data: list[dict],
    ) -> RecommendationOutput:
        chain_lookup = {chain[-1]: chain for chain in prerequisite_chain if chain}
        mastery_lookup = {item["concept_slug"]: item for item in mastery_data}
        recommendations = []
        for concept in weak_concepts:
            slug = concept["concept_slug"]
            chain = " -> ".join(chain_lookup.get(slug, [slug]))
            mastery = mastery_lookup.get(slug, {})
            score = mastery.get("mastery_score", 0.0)
            recommendations.append(
                {
                    "concept_slug": slug,
                    "title": f"Rebuild {concept['concept_name']}",
                    "message": (
                        f"Study this concept next because it sits in the chain {chain}. "
                        f"Current mastery is {score:.0%}; revisit definitions and one worked example before retrying."
                    ),
                }
            )
        return RecommendationOutput.model_validate({"recommendations": recommendations})


def _trim_text_for_generation(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-(max_chars // 2) :]
    return (
        f"{head}\n\n[content truncated for quiz generation to keep the response structured and within limits]\n\n{tail}"
    )
