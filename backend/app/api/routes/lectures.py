"""Lecture ingestion and quiz generation endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.lecture import (
    LectureDetailResponse,
    LectureListItem,
    LectureUploadResponse,
    QuizGenerationRequest,
    QuizGenerationResponse,
)
from app.services.lecture_service import LectureService


router = APIRouter(prefix="/lectures")


@router.post("/upload", response_model=LectureUploadResponse)
async def upload_lecture(
    title: str | None = Form(default=None),
    raw_text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LectureUploadResponse:
    settings = get_settings()
    file_bytes = None
    filename = None
    if file is not None:
        filename = file.filename
        if not filename or not filename.lower().endswith(".pdf") or file.content_type not in {
            "application/pdf",
            "application/x-pdf",
            "binary/octet-stream",
        }:
            raise ValueError("Only PDF uploads are supported for file-based ingestion.")
        file_bytes = await file.read()
        if len(file_bytes) > settings.max_upload_size_mb * 1024 * 1024:
            raise ValueError(f"PDF uploads must be smaller than {settings.max_upload_size_mb} MB.")

    service = LectureService(session)
    lecture = service.create_lecture(
        user=current_user,
        title=title,
        raw_text=raw_text,
        filename=filename,
        file_bytes=file_bytes,
    )
    detail = service.to_detail_response(service.get_lecture(current_user.id, lecture.id))
    return LectureUploadResponse(
        lecture=detail,
        source_type=lecture.source_type,
        cleaned_text_length=len(lecture.cleaned_text),
    )


@router.get("", response_model=list[LectureListItem])
def list_lectures(
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[LectureListItem]:
    return LectureService(session).list_lectures(current_user.id)


@router.get("/{lecture_id}", response_model=LectureDetailResponse)
def get_lecture_detail(
    lecture_id: UUID,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LectureDetailResponse:
    service = LectureService(session)
    return service.to_detail_response(service.get_lecture(current_user.id, lecture_id))


@router.post("/{lecture_id}/generate-quiz", response_model=QuizGenerationResponse)
def generate_quiz(
    lecture_id: UUID,
    payload: QuizGenerationRequest,
    session: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QuizGenerationResponse:
    return LectureService(session).generate_quiz(
        user_id=current_user.id,
        lecture_id=lecture_id,
        force_regenerate=payload.force_regenerate,
        questions_per_concept=payload.questions_per_concept,
    )
