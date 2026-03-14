"""Quiz session state and ordered question payload for future Unity clients."""

from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum as SAEnum, Float, ForeignKey, Integer, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.lecture import Lecture
    from app.models.question_attempt import QuestionAttempt
    from app.models.recommendation import Recommendation
    from app.models.user import User


class QuizSessionStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class QuizSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "quiz_sessions"

    user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lecture_id = mapped_column(ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[QuizSessionStatus] = mapped_column(SAEnum(QuizSessionStatus), default=QuizSessionStatus.IN_PROGRESS)
    question_order: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    question_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_answers: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    current_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    study_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accuracy_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    stars_awarded: Mapped[int | None] = mapped_column(Integer, nullable=True)
    star_jar_week_start: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    user: Mapped["User"] = relationship(back_populates="quiz_sessions")
    lecture: Mapped["Lecture"] = relationship(back_populates="quiz_sessions")
    attempts: Mapped[list["QuestionAttempt"]] = relationship(back_populates="session", cascade="all, delete-orphan")
    generated_recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="source_session")
