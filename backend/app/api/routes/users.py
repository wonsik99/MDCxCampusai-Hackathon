"""User and analytics endpoints used by the web app and future Unity client."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.core.exceptions import NotFoundError
from app.models import User
from app.schemas.user import DemoUserRead, ConceptMasteryRead, RecommendationsResponse
from app.services.analytics_service import AnalyticsService
from app.services.recommendation_service import RecommendationService


router = APIRouter()


@router.get("/demo-users", response_model=list[DemoUserRead])
def list_demo_users(session: Session = Depends(get_db)) -> list[DemoUserRead]:
    users = session.scalars(select(User).order_by(User.name)).all()
    return [DemoUserRead.model_validate(user) for user in users]


@router.get("/users/{user_id}/concept-mastery", response_model=list[ConceptMasteryRead])
def get_concept_mastery(user_id: UUID, session: Session = Depends(get_db)) -> list[ConceptMasteryRead]:
    user = session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise NotFoundError("User not found.")
    return AnalyticsService(session).get_mastery_overview(user_id)


@router.get("/users/{user_id}/recommendations", response_model=RecommendationsResponse)
def get_recommendations(user_id: UUID, session: Session = Depends(get_db)) -> RecommendationsResponse:
    user = session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise NotFoundError("User not found.")
    service = RecommendationService(session)
    return service.get_recommendations(user_id)
