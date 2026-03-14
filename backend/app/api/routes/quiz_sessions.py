"""Unity-friendly quiz session endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.quiz import (
    FinishSessionResponse,
    QuizSessionQuestionsResponse,
    QuizSessionRead,
    QuizSessionStartRequest,
    QuizSessionStartResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.services.quiz_service import QuizService


router = APIRouter(prefix="/quiz-sessions")


@router.post("/start", response_model=QuizSessionStartResponse)
def start_quiz_session(
    payload: QuizSessionStartRequest,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizSessionStartResponse:
    return QuizService(session).start_session(current_user.id, payload.lecture_id, payload.question_limit)


@router.get("/{session_id}", response_model=QuizSessionRead)
def get_quiz_session(
    session_id: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizSessionRead:
    return QuizService(session).get_session_read(current_user.id, session_id)


@router.get("/{session_id}/questions", response_model=QuizSessionQuestionsResponse)
def get_quiz_questions(
    session_id: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizSessionQuestionsResponse:
    return QuizService(session).get_questions(current_user.id, session_id)


@router.post("/{session_id}/submit-answer", response_model=SubmitAnswerResponse)
def submit_answer(
    session_id: UUID,
    payload: SubmitAnswerRequest,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubmitAnswerResponse:
    return QuizService(session).submit_answer(
        current_user.id,
        session_id,
        payload.question_id,
        payload.selected_choice_id,
        payload.response_time_ms,
    )


@router.post("/{session_id}/finish", response_model=FinishSessionResponse)
def finish_quiz_session(
    session_id: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FinishSessionResponse:
    return QuizService(session).finish_session(current_user.id, session_id)
