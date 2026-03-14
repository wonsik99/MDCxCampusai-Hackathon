"""Concept model with optional prerequisite links inside a lecture graph."""

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.concept_mastery import ConceptMastery
    from app.models.lecture import Lecture
    from app.models.question import Question
    from app.models.recommendation import Recommendation


class Concept(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "concepts"

    lecture_id = mapped_column(ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    prerequisite_concept_id = mapped_column(ForeignKey("concepts.id", ondelete="SET NULL"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    slug: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_inferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    lecture: Mapped["Lecture"] = relationship(back_populates="concepts")
    prerequisite_concept: Mapped["Concept | None"] = relationship(remote_side="Concept.id")
    questions: Mapped[list["Question"]] = relationship(back_populates="concept")
    masteries: Mapped[list["ConceptMastery"]] = relationship(back_populates="concept")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="concept")
