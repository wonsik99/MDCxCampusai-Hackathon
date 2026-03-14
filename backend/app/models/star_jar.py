"""Weekly motivation jar aggregates derived from completed quiz sessions."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.user import User


class StarJar(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "star_jars"
    __table_args__ = (UniqueConstraint("user_id", "week_start_date", name="uq_star_jars_user_id_week_start_date"),)

    user_id = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    week_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    capacity_stars: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    earned_stars: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    study_time_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sessions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_accuracy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="star_jars")
