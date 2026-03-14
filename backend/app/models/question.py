"""Quiz question model with server-only answer data."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.concept import Concept
    from app.models.lecture import Lecture
    from app.models.question_attempt import QuestionAttempt


class Question(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "questions"

    lecture_id = mapped_column(ForeignKey("lectures.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    choices: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    correct_choice_id: Mapped[str] = mapped_column(String(8), nullable=False)
    wrong_answer_explanations: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    lecture: Mapped["Lecture"] = relationship(back_populates="questions")
    concept: Mapped["Concept"] = relationship(back_populates="questions")
    attempts: Mapped[list["QuestionAttempt"]] = relationship(back_populates="question")
