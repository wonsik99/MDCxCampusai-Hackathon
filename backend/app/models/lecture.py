"""Lecture source material model with AI-generated metadata."""

from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.concept import Concept
    from app.models.question import Question
    from app.models.quiz_session import QuizSession
    from app.models.recommendation import Recommendation
    from app.models.user import User


class LectureSourceType(str, Enum):
    PDF = "pdf"
    TEXT = "text"


class Lecture(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "lectures"

    user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[LectureSourceType] = mapped_column(SAEnum(LectureSourceType), nullable=False)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_text: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    user: Mapped["User"] = relationship(back_populates="lectures")
    concepts: Mapped[list["Concept"]] = relationship(back_populates="lecture", cascade="all, delete-orphan")
    questions: Mapped[list["Question"]] = relationship(back_populates="lecture", cascade="all, delete-orphan")
    quiz_sessions: Mapped[list["QuizSession"]] = relationship(back_populates="lecture")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="lecture")
