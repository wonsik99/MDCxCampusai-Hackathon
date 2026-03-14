"""Quiz session lifecycle, grading, and analytics integration."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.models import Question, QuestionAttempt, QuizSession
from app.models.quiz_session import QuizSessionStatus
from app.schemas.quiz import (
    FinishSessionResponse,
    QuizSessionQuestionRead,
    QuizSessionQuestionsResponse,
    QuizSessionRead,
    QuizSessionStartResponse,
    SubmitAnswerResponse,
)
from app.services.ai_service import AIService
from app.services.analytics_service import AnalyticsService
from app.services.lecture_service import LectureService
from app.services.recommendation_service import RecommendationService


class QuizService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.ai_service = AIService()
        self.analytics_service = AnalyticsService(session)
        self.recommendation_service = RecommendationService(
            session, analytics_service=self.analytics_service, ai_service=self.ai_service
        )
        self.lecture_service = LectureService(session, ai_service=self.ai_service)

    def start_session(self, user_id: UUID, lecture_id: UUID, question_limit: int | None) -> QuizSessionStartResponse:
        lecture = self.lecture_service.get_lecture(user_id, lecture_id)
        if not lecture.questions:
            raise ConflictError("Generate quiz questions before starting a session.")

        ordered_questions = sorted(
            lecture.questions,
            key=lambda question: (
                next(concept.display_order for concept in lecture.concepts if concept.id == question.concept_id),
                question.created_at,
            ),
        )
        if question_limit:
            ordered_questions = ordered_questions[:question_limit]

        self.analytics_service.ensure_masteries_for_lecture(user_id, lecture.concepts)
        quiz_session = QuizSession(
            user_id=user_id,
            lecture_id=lecture.id,
            status=QuizSessionStatus.IN_PROGRESS,
            question_order=[str(question.id) for question in ordered_questions],
            question_limit=question_limit,
            total_questions=len(ordered_questions),
            correct_answers=0,
            current_index=0,
            started_at=datetime.now(timezone.utc),
        )
        self.session.add(quiz_session)
        self.session.commit()
        self.session.refresh(quiz_session)
        return QuizSessionStartResponse(
            session_id=quiz_session.id,
            lecture_id=lecture.id,
            lecture_title=lecture.title,
            lecture_summary=lecture.summary or "",
            concept_ids=[concept.id for concept in sorted(lecture.concepts, key=lambda item: item.display_order)],
            session_status=quiz_session.status,
            total_questions=quiz_session.total_questions,
        )

    def get_session(self, user_id: UUID, session_id: UUID) -> QuizSession:
        session = self.session.scalars(
            select(QuizSession)
            .where(QuizSession.id == session_id, QuizSession.user_id == user_id)
            .options(joinedload(QuizSession.lecture), joinedload(QuizSession.attempts))
        ).unique().first()
        if not session:
            raise NotFoundError("Quiz session not found.")
        return session

    def get_session_read(self, user_id: UUID, session_id: UUID) -> QuizSessionRead:
        session = self.get_session(user_id, session_id)
        return QuizSessionRead(
            session_id=session.id,
            lecture_id=session.lecture_id,
            lecture_title=session.lecture.title,
            status=session.status,
            total_questions=session.total_questions,
            answered_questions=len(session.attempts),
            correct_answers=session.correct_answers,
            started_at=session.started_at,
            finished_at=session.finished_at,
        )

    def get_questions(self, user_id: UUID, session_id: UUID) -> QuizSessionQuestionsResponse:
        quiz_session = self.get_session(user_id, session_id)
        order = [UUID(question_id) for question_id in quiz_session.question_order]
        questions = self.session.scalars(
            select(Question)
            .where(Question.id.in_(order))
            .options(joinedload(Question.concept))
        ).unique().all()
        question_lookup = {question.id: question for question in questions}
        return QuizSessionQuestionsResponse(
            session_id=quiz_session.id,
            questions=[
                QuizSessionQuestionRead(
                    question_id=question_lookup[question_id].id,
                    prompt=question_lookup[question_id].prompt,
                    concept_id=question_lookup[question_id].concept_id,
                    concept_name=question_lookup[question_id].concept.name,
                    choices=question_lookup[question_id].choices,
                    sequence=index + 1,
                )
                for index, question_id in enumerate(order)
                if question_id in question_lookup
            ],
        )

    def submit_answer(
        self,
        user_id: UUID,
        session_id: UUID,
        question_id: UUID,
        selected_choice_id: str,
        response_time_ms: int,
    ) -> SubmitAnswerResponse:
        quiz_session = self.get_session(user_id, session_id)
        if quiz_session.status != QuizSessionStatus.IN_PROGRESS:
            raise ConflictError("Cannot submit an answer to a completed session.")
        if str(question_id) not in quiz_session.question_order:
            raise AppError("Question does not belong to this session.", status_code=422, error_code="invalid_question")

        already_answered = self.session.scalar(
            select(QuestionAttempt).where(
                QuestionAttempt.session_id == quiz_session.id,
                QuestionAttempt.question_id == question_id,
            )
        )
        if already_answered:
            raise ConflictError("This question has already been answered in the session.")

        question = self.session.scalar(
            select(Question)
            .where(Question.id == question_id)
            .options(joinedload(Question.concept), joinedload(Question.lecture))
        )
        if not question:
            raise NotFoundError("Question not found.")

        choices = {item["choice_id"]: item["text"] for item in question.choices}
        if selected_choice_id not in choices:
            raise AppError("Selected answer is not a valid choice.", status_code=422, error_code="invalid_choice")

        is_correct = selected_choice_id == question.correct_choice_id
        correct_choice_text = choices[question.correct_choice_id]
        explanation = (
            f"Correct. {correct_choice_text}"
            if is_correct
            else question.wrong_answer_explanations.get(selected_choice_id)
            or self.ai_service.explain_wrong_answer(
                question=question.prompt,
                selected_answer=choices[selected_choice_id],
                correct_answer=correct_choice_text,
                concept=question.concept.name,
                lecture_summary=question.lecture.summary or "",
            ).explanation
        )
        attempted_at = datetime.now(timezone.utc)
        attempt = QuestionAttempt(
            session_id=quiz_session.id,
            user_id=user_id,
            question_id=question.id,
            selected_choice_id=selected_choice_id,
            is_correct=is_correct,
            response_time_ms=response_time_ms,
            explanation=explanation,
            attempted_at=attempted_at,
        )
        self.session.add(attempt)
        mastery = self.analytics_service.update_mastery(
            user_id=user_id, concept=question.concept, is_correct=is_correct, attempted_at=attempted_at
        )
        quiz_session.correct_answers += 1 if is_correct else 0
        quiz_session.current_index += 1
        self.session.commit()

        weak_ids = {item["concept_id"] for item in self.analytics_service.detect_weak_concepts(user_id, question.lecture_id)}
        return SubmitAnswerResponse(
            session_id=quiz_session.id,
            question_id=question.id,
            is_correct=is_correct,
            correct_choice_id=question.correct_choice_id,
            correct_choice_text=correct_choice_text,
            explanation=explanation,
            mastery=self.analytics_service.build_mastery_snapshot(question.concept, mastery),
            is_weak_concept=question.concept.id in weak_ids,
        )

    def finish_session(self, user_id: UUID, session_id: UUID) -> FinishSessionResponse:
        quiz_session = self.get_session(user_id, session_id)
        if quiz_session.status != QuizSessionStatus.IN_PROGRESS:
            raise ConflictError("Quiz session has already been finished.")

        quiz_session.status = QuizSessionStatus.COMPLETED
        quiz_session.finished_at = datetime.now(timezone.utc)
        self.session.commit()
        recommendations = self.recommendation_service.refresh_recommendations(
            user_id=user_id, lecture_id=quiz_session.lecture_id, source_session_id=quiz_session.id
        )
        weak_concepts = self.analytics_service.detect_weak_concepts(user_id, quiz_session.lecture_id)
        return FinishSessionResponse(
            session_id=quiz_session.id,
            score=(quiz_session.correct_answers / quiz_session.total_questions) if quiz_session.total_questions else 0.0,
            correct_answers=quiz_session.correct_answers,
            total_questions=quiz_session.total_questions,
            concept_performance=self.analytics_service.session_performance(
                user_id, quiz_session.lecture_id, quiz_session.id
            ),
            weak_concepts=[item["concept_name"] for item in weak_concepts],
            recommendations=recommendations.recommendations,
        )
