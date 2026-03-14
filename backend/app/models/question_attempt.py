"""Individual student answer attempt records for mastery analytics."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.question import Question
    from app.models.quiz_session import QuizSession
    from app.models.user import User


class QuestionAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "question_attempts"

    session_id = mapped_column(ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_choice_id: Mapped[str] = mapped_column(String(8), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    session: Mapped["QuizSession"] = relationship(back_populates="attempts")
    user: Mapped["User"] = relationship(back_populates="attempts")
    question: Mapped["Question"] = relationship(back_populates="attempts")
