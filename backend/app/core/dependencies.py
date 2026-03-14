"""Request-scoped FastAPI dependencies."""

from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.db.session import get_db_session
from app.models import User


def get_db(session: Session = Depends(get_db_session)) -> Session:
    return session


def get_current_user(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    session: Session = Depends(get_db),
) -> User:
    if not x_user_id:
        raise UnauthorizedError("X-User-Id header is required for lecture and quiz routes.")
    try:
        user_id = UUID(x_user_id)
    except ValueError as exc:
        raise UnauthorizedError("X-User-Id must be a valid UUID.") from exc

    user = session.scalar(select(User).where(User.id == user_id))
    if not user:
        raise UnauthorizedError("Demo user was not found.")
    return user
