"""User model for demo student ownership and analytics scoping."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.concept_mastery import ConceptMastery
    from app.models.lecture import Lecture
    from app.models.question_attempt import QuestionAttempt
    from app.models.quiz_session import QuizSession
    from app.models.recommendation import Recommendation
    from app.models.star_jar import StarJar


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)

    lectures: Mapped[list["Lecture"]] = relationship(back_populates="user")
    quiz_sessions: Mapped[list["QuizSession"]] = relationship(back_populates="user")
    attempts: Mapped[list["QuestionAttempt"]] = relationship(back_populates="user")
    concept_masteries: Mapped[list["ConceptMastery"]] = relationship(back_populates="user")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="user")
    star_jars: Mapped[list["StarJar"]] = relationship(back_populates="user", cascade="all, delete-orphan")
