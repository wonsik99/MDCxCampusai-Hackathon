"""Per-user mastery snapshot for each concept."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.concept import Concept
    from app.models.user import User


class ConceptMastery(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "concept_masteries"
    __table_args__ = (UniqueConstraint("user_id", "concept_id"),)

    user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    mastery_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="concept_masteries")
    concept: Mapped["Concept"] = relationship(back_populates="masteries")
