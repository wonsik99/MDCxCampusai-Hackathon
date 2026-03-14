"""Ordered study recommendations derived from deterministic analytics."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.concept import Concept
    from app.models.lecture import Lecture
    from app.models.quiz_session import QuizSession
    from app.models.user import User


class Recommendation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "recommendations"

    user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    lecture_id = mapped_column(ForeignKey("lectures.id", ondelete="SET NULL"), nullable=True, index=True)
    concept_id = mapped_column(ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True, index=True)
    source_session_id = mapped_column(ForeignKey("quiz_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    reason_code: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    user: Mapped["User"] = relationship(back_populates="recommendations")
    lecture: Mapped["Lecture"] = relationship(back_populates="recommendations")
    concept: Mapped["Concept | None"] = relationship(back_populates="recommendations")
    source_session: Mapped["QuizSession | None"] = relationship(back_populates="generated_recommendations")
