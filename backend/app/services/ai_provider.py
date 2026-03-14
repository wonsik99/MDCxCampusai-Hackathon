"""OpenAI provider for structured educational content generation."""

from __future__ import annotations

import logging
from itertools import cycle

from openai import OpenAI

from app.core.config import Settings
from app.core.exceptions import AIProviderError
from app.schemas.ai import (
    ConceptExtractionOutput,
    LectureSummaryOutput,
    RecommendationOutput,
    WrongAnswerExplanationOutput,
    QuizGenerationOutput,
    QuizQuestionOutput,
    RecommendationMessageItem,
    WrongAnswerExplanation,
)
from app.schemas.common import ChoiceRead
from app.utils.text import extract_keyword_concepts, summarize_text_fallback

logger = logging.getLogger(__name__)


class OpenAIProvider:
    provider_name = "openai"

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
            "You are an expert educational assessment designer creating diagnostic quiz questions.\n\n"
            "TASK: Generate high-quality multiple-choice questions that test genuine understanding, "
            "not surface-level recall.\n\n"
            "RULES:\n"
            f"- Generate exactly {questions_per_concept} questions per concept.\n"
            "- Each question must belong to exactly one concept_slug from the concept list below.\n"
            "- Each question must have exactly 4 answer choices (A, B, C, D).\n"
            "- CRITICAL: Distribute the correct answer position roughly equally across A, B, C, and D. "
            "Each position must be used at least once. Do NOT cluster correct answers in A or B.\n"
            "- Distractors must be plausible misconceptions that a struggling learner might genuinely choose. "
            "Avoid obviously wrong options.\n"
            "- For each incorrect choice, provide a 1-2 sentence explanation that helps the student "
            "understand why it is wrong and points them toward the correct reasoning.\n"
            "- Vary question styles: include application questions, comparison questions, and "
            "'which of the following is true/false' questions. Avoid generic 'what is X?' patterns.\n"
            "- Ground every question in specific content from the lecture text.\n\n"
            f"CONCEPT LIST:\n{concept_list}\n\n"
            f"LECTURE TEXT:\n{compact_text}"
        )
        return self._parse_response(
            "Generate quiz questions as structured JSON. Each wrong_answer_explanations entry must have "
            "a choice_id field and an explanation field.",
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


def _trim_text_for_generation(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-(max_chars // 2) :]
    return (
        f"{head}\n\n[content truncated for quiz generation to keep the response structured and within limits]\n\n{tail}"
    )


class FallbackAIProvider:
    provider_name = "fallback"

    def __init__(self, _: Settings) -> None:
        pass

    def summarize_lecture(self, text: str) -> LectureSummaryOutput:
        concepts = extract_keyword_concepts(text, max_items=3)
        takeaways = [
            f"Focus on {concept['name']} when reviewing the lecture."
            for concept in concepts
        ]
        if not takeaways:
            takeaways = ["Review the core idea and then retry related quiz questions."]
        return LectureSummaryOutput(summary=summarize_text_fallback(text), key_takeaways=takeaways[:5])

    def extract_concepts(self, text: str) -> ConceptExtractionOutput:
        return ConceptExtractionOutput.model_validate({"concepts": extract_keyword_concepts(text, max_items=4)})

    def generate_quiz_from_lecture(
        self,
        text: str,
        concepts: list[dict[str, str]],
        questions_per_concept: int,
    ) -> QuizGenerationOutput:
        excerpt = summarize_text_fallback(text, limit=180)
        questions: list[QuizQuestionOutput] = []
        distractor_letters = ["A", "B", "C", "D"]
        for concept in concepts:
            other_names = [item["name"] for item in concepts if item["slug"] != concept["slug"]][:2]
            for index in range(questions_per_concept):
                prompt = (
                    f"Which statement best reflects the lecture's treatment of {concept['name']}?"
                    if index % 2 == 0
                    else f"What is the most useful next study move for improving on {concept['name']}?"
                )
                correct_text = (
                    concept.get("description")
                    or f"Review how {concept['name']} is used in the lecture and connect it to the worked examples."
                )
                if index % 2 == 1:
                    correct_text = (
                        f"Revisit {concept['name']} in the lecture notes, then practice one related problem from the summary."
                    )
                distractors = [
                    (
                        f"Treat {concept['name']} as identical to {other_names[0]}."
                        if other_names
                        else f"Memorize the term {concept['name']} without checking how it is used."
                    ),
                    f"Skip {concept['name']} and move straight to harder topics without reviewing the lecture.",
                    f"Ignore the lecture context and rely only on isolated definitions from outside sources.",
                ]
                choice_cycle = cycle(distractor_letters)
                choices = [
                    ChoiceRead(choice_id=next(choice_cycle), text=correct_text),
                    *[ChoiceRead(choice_id=next(choice_cycle), text=text) for text in distractors],
                ]
                wrong_explanations = [
                    WrongAnswerExplanation(
                        choice_id=choice.choice_id,
                        explanation=(
                            f"This misses how the lecture framed {concept['name']}. Use the lecture summary first: {excerpt}"
                        ),
                    )
                    for choice in choices
                    if choice.choice_id != "A"
                ]
                questions.append(
                    QuizQuestionOutput(
                        concept_slug=concept["slug"],
                        prompt=prompt,
                        choices=choices,
                        correct_choice_id="A",
                        wrong_answer_explanations=wrong_explanations,
                    )
                )
        return QuizGenerationOutput(questions=questions)

    def explain_wrong_answer(
        self,
        question: str,
        selected_answer: str,
        correct_answer: str,
        concept: str,
        lecture_summary: str,
    ) -> WrongAnswerExplanationOutput:
        explanation = (
            f"'{selected_answer}' does not match the lecture's framing of {concept}. "
            f"The stronger answer is '{correct_answer}'. {lecture_summary[:180]}"
        ).strip()
        return WrongAnswerExplanationOutput(
            explanation=explanation
        )

    def generate_recommendation(
        self,
        weak_concepts: list[dict],
        prerequisite_chain: list[list[str]],
        mastery_data: list[dict],
    ) -> RecommendationOutput:
        chain_lookup = {chain[-1]: chain for chain in prerequisite_chain if chain}
        mastery_lookup = {item["concept_slug"]: item for item in mastery_data}
        recommendations: list[RecommendationMessageItem] = []
        for weak in weak_concepts:
            chain = chain_lookup.get(weak["concept_slug"], [weak["concept_slug"]])
            prerequisite_steps = " -> ".join(chain[:-1]) if len(chain) > 1 else None
            mastery = mastery_lookup.get(weak["concept_slug"], {})
            recommendations.append(
                RecommendationMessageItem(
                    concept_slug=weak["concept_slug"],
                    title=f"Rebuild {weak['concept_name']}",
                    message=(
                        f"Study {weak['concept_name']} next. "
                        f"{f'Start with {prerequisite_steps} before returning to it. ' if prerequisite_steps else ''}"
                        f"Current mastery is {round((mastery.get('mastery_score') or 0) * 100)}%."
                    ),
                )
            )
        return RecommendationOutput(recommendations=recommendations)
