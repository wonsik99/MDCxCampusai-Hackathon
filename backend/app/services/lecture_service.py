"""Lecture ingestion, AI enrichment, and quiz generation workflows."""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.models import Concept, Lecture, Question, QuizSession, User
from app.models.lecture import LectureSourceType
from app.schemas.ai import ConceptExtractionItem
from app.schemas.common import LectureSummaryBlock
from app.schemas.lecture import LectureDetailResponse, LectureListItem, QuizGenerationResponse
from app.schemas.common import AIUsageMetadata
from app.services.ai_service import AIService
from app.utils.pdf import extract_text_from_pdf
from app.utils.prerequisite import enrich_with_prerequisites
from app.utils.text import clean_lecture_text


class LectureService:
    def __init__(self, session: Session, ai_service: AIService | None = None) -> None:
        self.session = session
        self.ai_service = ai_service or AIService()

    def create_lecture(
        self,
        *,
        user: User,
        title: str | None,
        raw_text: str | None,
        filename: str | None,
        file_bytes: bytes | None,
    ) -> Lecture:
        if bool(raw_text and raw_text.strip()) == bool(file_bytes):
            raise AppError(
                "Provide exactly one lecture input: either raw_text or a PDF file.",
                status_code=422,
                error_code="invalid_upload_payload",
            )

        if file_bytes:
            raw_content = extract_text_from_pdf(file_bytes)
            source_type = LectureSourceType.PDF
            lecture_title = title or filename or "Uploaded PDF"
        else:
            raw_content = raw_text or ""
            source_type = LectureSourceType.TEXT
            lecture_title = title or "Lecture Notes"

        cleaned_text = clean_lecture_text(raw_content)
        if len(cleaned_text) < 40:
            raise AppError("Lecture content is too short to analyze.", status_code=422, error_code="lecture_too_short")

        summary = self.ai_service.summarize_lecture(cleaned_text)
        extracted = self.ai_service.extract_concepts(cleaned_text)

        lecture = Lecture(
            user_id=user.id,
            title=lecture_title,
            source_type=source_type,
            original_filename=filename,
            raw_text=raw_content,
            cleaned_text=cleaned_text,
            summary=summary.summary,
            ai_metadata={
                "provider": self.ai_service.metadata.provider,
                "used_fallback": self.ai_service.metadata.used_fallback,
                "key_takeaways": summary.key_takeaways,
            },
        )
        self.session.add(lecture)
        self.session.flush()
        self._replace_concepts(lecture, extracted.concepts)
        self.session.commit()
        self.session.refresh(lecture)
        return lecture

    def list_lectures(self, user_id: UUID) -> list[LectureListItem]:
        lectures = self.session.scalars(
            select(Lecture)
            .where(Lecture.user_id == user_id)
            .options(joinedload(Lecture.concepts), joinedload(Lecture.questions))
            .order_by(Lecture.created_at.desc())
        ).unique().all()
        return [
            LectureListItem(
                id=lecture.id,
                title=lecture.title,
                source_type=lecture.source_type,
                summary=lecture.summary,
                concept_count=len(lecture.concepts),
                question_count=len(lecture.questions),
                created_at=lecture.created_at,
            )
            for lecture in lectures
        ]

    def get_lecture(self, user_id: UUID, lecture_id: UUID) -> Lecture:
        lecture = self.session.scalars(
            select(Lecture)
            .where(Lecture.id == lecture_id, Lecture.user_id == user_id)
            .options(joinedload(Lecture.concepts), joinedload(Lecture.questions))
        ).unique().first()
        if not lecture:
            raise NotFoundError("Lecture not found.")
        return lecture

    def generate_quiz(
        self,
        *,
        user_id: UUID,
        lecture_id: UUID,
        force_regenerate: bool,
        questions_per_concept: int,
    ) -> QuizGenerationResponse:
        lecture = self.get_lecture(user_id, lecture_id)

        if lecture.questions and not force_regenerate:
            covered_concepts = {question.concept_id for question in lecture.questions}
            return QuizGenerationResponse(
                lecture_id=lecture.id,
                question_count=len(lecture.questions),
                concept_coverage=[concept.slug for concept in lecture.concepts if concept.id in covered_concepts],
                generated=False,
                ai_metadata=self.ai_service.metadata,
            )

        if lecture.questions and force_regenerate:
            existing_sessions = self.session.scalar(
                select(QuizSession).where(QuizSession.lecture_id == lecture.id).limit(1)
            )
            if existing_sessions:
                raise ConflictError("Quiz questions cannot be regenerated after sessions already exist.")
            self.session.execute(delete(Question).where(Question.lecture_id == lecture.id))
            self.session.flush()

        concept_payload = [
            {"name": concept.name, "slug": concept.slug, "description": concept.description or concept.name}
            for concept in sorted(lecture.concepts, key=lambda item: item.display_order)
        ]
        generated = self.ai_service.generate_quiz_from_lecture(
            lecture.cleaned_text, concept_payload, questions_per_concept
        )

        concepts_by_slug = {concept.slug: concept for concept in lecture.concepts}
        concept_counts: dict[str, int] = defaultdict(int)
        for question_payload in generated.questions:
            concept = concepts_by_slug.get(question_payload.concept_slug)
            if not concept:
                raise AppError(
                    f"Generated question referenced unknown concept '{question_payload.concept_slug}'.",
                    status_code=502,
                    error_code="invalid_ai_output",
                )
            explanation_keys = set(question_payload.wrong_answer_explanations)
            valid_wrong_choices = {choice.choice_id for choice in question_payload.choices if choice.choice_id != question_payload.correct_choice_id}
            if explanation_keys != valid_wrong_choices:
                raise AppError(
                    "Generated wrong-answer explanations did not match the incorrect choices.",
                    status_code=502,
                    error_code="invalid_ai_output",
                )
            self.session.add(
                Question(
                    lecture_id=lecture.id,
                    concept_id=concept.id,
                    prompt=question_payload.prompt,
                    choices=[choice.model_dump() for choice in question_payload.choices],
                    correct_choice_id=question_payload.correct_choice_id,
                    wrong_answer_explanations=question_payload.wrong_answer_explanations,
                )
            )
            concept_counts[concept.slug] += 1

        lecture.ai_metadata = {**lecture.ai_metadata, **self.ai_service.metadata.model_dump()}
        self.session.commit()
        self.session.expire_all()
        refreshed = self.get_lecture(user_id, lecture_id)
        return QuizGenerationResponse(
            lecture_id=refreshed.id,
            question_count=len(refreshed.questions),
            concept_coverage=[slug for slug, count in concept_counts.items() if count > 0],
            generated=True,
            ai_metadata=self.ai_service.metadata,
        )

    def to_detail_response(self, lecture: Lecture) -> LectureDetailResponse:
        return LectureDetailResponse(
            id=lecture.id,
            title=lecture.title,
            source_type=lecture.source_type,
            original_filename=lecture.original_filename,
            summary_block=LectureSummaryBlock(
                summary=lecture.summary or "",
                key_takeaways=lecture.ai_metadata.get("key_takeaways", []),
            ),
            concepts=[
                {
                    "id": concept.id,
                    "name": concept.name,
                    "slug": concept.slug,
                    "description": concept.description,
                    "prerequisite_concept_id": concept.prerequisite_concept_id,
                    "is_inferred": concept.is_inferred,
                    "display_order": concept.display_order,
                }
                for concept in sorted(lecture.concepts, key=lambda item: item.display_order)
            ],
            question_count=len(lecture.questions),
            quiz_generated=bool(lecture.questions),
            ai_metadata=AIUsageMetadata.model_validate(lecture.ai_metadata),
            created_at=lecture.created_at,
        )

    def _replace_concepts(self, lecture: Lecture, concepts: list[ConceptExtractionItem]) -> None:
        enriched = enrich_with_prerequisites(concepts)
        created: dict[str, Concept] = {}
        for index, concept_seed in enumerate(enriched):
            concept = Concept(
                lecture_id=lecture.id,
                name=concept_seed.name,
                slug=concept_seed.slug,
                description=concept_seed.description,
                is_inferred=concept_seed.is_inferred,
                display_order=index,
            )
            self.session.add(concept)
            self.session.flush()
            created[concept.slug] = concept

        for concept_seed in enriched:
            if concept_seed.prerequisite_slug and concept_seed.slug in created:
                created[concept_seed.slug].prerequisite_concept_id = created[concept_seed.prerequisite_slug].id
