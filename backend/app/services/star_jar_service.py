"""Reward and weekly jar aggregation logic for study momentum."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from math import ceil
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models import QuizSession, StarJar
from app.models.quiz_session import QuizSessionStatus
from app.schemas.quiz import StarJarUpdateRead
from app.schemas.user import StarJarRead, StarJarsResponse


@dataclass(slots=True)
class SessionReward:
    study_time_ms: int
    accuracy_ratio: float
    stars_awarded: int
    week_start_date: date
    week_end_date: date


class StarJarService:
    capacity_stars = 100
    base_interval_ms = 15_000

    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()
        self.zone = ZoneInfo(self.settings.reporting_timezone)

    def get_star_jars(self, user_id: UUID) -> StarJarsResponse:
        self.backfill_missing_rewards(user_id)
        current_week_start, _ = self.resolve_week_window(datetime.now(timezone.utc))
        jars = self.session.scalars(
            select(StarJar).where(StarJar.user_id == user_id).order_by(StarJar.week_start_date.desc())
        ).all()
        current_jar = next((jar for jar in jars if jar.week_start_date == current_week_start), None)
        return StarJarsResponse(
            user_id=user_id,
            current_jar=self.build_star_jar_read(current_jar, current_week_start) if current_jar else None,
            history=[self.build_star_jar_read(jar, current_week_start) for jar in jars],
        )

    def award_session(self, quiz_session: QuizSession) -> tuple[StarJarUpdateRead, StarJarRead]:
        reward = self._apply_session_reward(quiz_session)
        jar = self._rebuild_weekly_jar(quiz_session.user_id, reward.week_start_date)
        current_week_start, _ = self.resolve_week_window(quiz_session.finished_at or datetime.now(timezone.utc))
        return self.build_star_jar_update(reward), self.build_star_jar_read(jar, current_week_start)

    def backfill_missing_rewards(self, user_id: UUID | None = None) -> int:
        filters = [
            QuizSession.status == QuizSessionStatus.COMPLETED,
            QuizSession.finished_at.is_not(None),
            QuizSession.stars_awarded.is_(None),
        ]
        if user_id:
            filters.append(QuizSession.user_id == user_id)

        sessions = self.session.scalars(
            select(QuizSession)
            .where(*filters)
            .options(joinedload(QuizSession.attempts))
            .order_by(QuizSession.finished_at.asc(), QuizSession.created_at.asc())
        ).unique().all()
        if not sessions:
            return 0

        touched_weeks: set[tuple[UUID, date]] = set()
        for quiz_session in sessions:
            reward = self._apply_session_reward(quiz_session)
            touched_weeks.add((quiz_session.user_id, reward.week_start_date))

        for owner_id, week_start in touched_weeks:
            self._rebuild_weekly_jar(owner_id, week_start)

        self.session.commit()
        return len(sessions)

    def resolve_week_window(self, moment: datetime) -> tuple[date, date]:
        localized = moment.astimezone(self.zone)
        week_start = (localized - timedelta(days=localized.weekday())).date()
        return week_start, week_start + timedelta(days=6)

    def calculate_reward(self, study_time_ms: int, correct_answers: int, total_questions: int) -> tuple[int, float]:
        base_stars = ceil(study_time_ms / self.base_interval_ms) if study_time_ms > 0 else 0
        accuracy_ratio = (correct_answers / total_questions) if total_questions else 0.0
        accuracy_bonus = round(base_stars * accuracy_ratio * 0.5)
        return base_stars + accuracy_bonus, accuracy_ratio

    def build_star_jar_update(self, reward: SessionReward) -> StarJarUpdateRead:
        return StarJarUpdateRead(
            week_start_date=reward.week_start_date,
            week_end_date=reward.week_end_date,
            study_time_ms=reward.study_time_ms,
            accuracy_ratio=reward.accuracy_ratio,
            stars_awarded=reward.stars_awarded,
        )

    def build_star_jar_read(self, jar: StarJar, current_week_start: date) -> StarJarRead:
        fill_ratio = min((jar.earned_stars / jar.capacity_stars), 1.0) if jar.capacity_stars else 0.0
        return StarJarRead(
            jar_id=jar.id,
            week_start_date=jar.week_start_date,
            week_end_date=jar.week_end_date,
            capacity_stars=jar.capacity_stars,
            earned_stars=jar.earned_stars,
            fill_ratio=fill_ratio,
            study_time_ms=jar.study_time_ms,
            sessions_count=jar.sessions_count,
            average_accuracy=jar.average_accuracy,
            is_current=jar.week_start_date == current_week_start,
            is_complete=jar.completed_at is not None or jar.earned_stars >= jar.capacity_stars,
        )

    def _apply_session_reward(self, quiz_session: QuizSession) -> SessionReward:
        if quiz_session.status != QuizSessionStatus.COMPLETED or quiz_session.finished_at is None:
            raise ValueError("Only completed sessions can award stars.")

        if quiz_session.stars_awarded is not None and quiz_session.star_jar_week_start is not None:
            week_start = quiz_session.star_jar_week_start
            return SessionReward(
                study_time_ms=quiz_session.study_time_ms or 0,
                accuracy_ratio=quiz_session.accuracy_ratio or 0.0,
                stars_awarded=quiz_session.stars_awarded,
                week_start_date=week_start,
                week_end_date=week_start + timedelta(days=6),
            )

        study_time_ms = sum(attempt.response_time_ms for attempt in quiz_session.attempts)
        stars_awarded, accuracy_ratio = self.calculate_reward(
            study_time_ms=study_time_ms,
            correct_answers=quiz_session.correct_answers,
            total_questions=quiz_session.total_questions,
        )
        week_start, week_end = self.resolve_week_window(quiz_session.finished_at)
        quiz_session.study_time_ms = study_time_ms
        quiz_session.accuracy_ratio = accuracy_ratio
        quiz_session.stars_awarded = stars_awarded
        quiz_session.star_jar_week_start = week_start
        self.session.flush()
        return SessionReward(
            study_time_ms=study_time_ms,
            accuracy_ratio=accuracy_ratio,
            stars_awarded=stars_awarded,
            week_start_date=week_start,
            week_end_date=week_end,
        )

    def _rebuild_weekly_jar(self, user_id: UUID, week_start_date: date) -> StarJar:
        sessions = self.session.scalars(
            select(QuizSession)
            .where(
                QuizSession.user_id == user_id,
                QuizSession.status == QuizSessionStatus.COMPLETED,
                QuizSession.star_jar_week_start == week_start_date,
                QuizSession.stars_awarded.is_not(None),
            )
            .order_by(QuizSession.finished_at.asc(), QuizSession.created_at.asc())
        ).all()
        jar = self.session.scalar(
            select(StarJar).where(StarJar.user_id == user_id, StarJar.week_start_date == week_start_date)
        )
        if not jar:
            jar = StarJar(
                user_id=user_id,
                week_start_date=week_start_date,
                week_end_date=week_start_date + timedelta(days=6),
                capacity_stars=self.capacity_stars,
            )
            self.session.add(jar)

        jar.week_end_date = week_start_date + timedelta(days=6)
        jar.capacity_stars = self.capacity_stars
        jar.earned_stars = sum(current.stars_awarded or 0 for current in sessions)
        jar.study_time_ms = sum(current.study_time_ms or 0 for current in sessions)
        jar.sessions_count = len(sessions)
        total_correct = sum(current.correct_answers for current in sessions)
        total_questions = sum(current.total_questions for current in sessions)
        jar.average_accuracy = (total_correct / total_questions) if total_questions else 0.0
        jar.completed_at = self._resolve_completed_at(sessions, self.capacity_stars)
        self.session.flush()
        return jar

    def _resolve_completed_at(self, sessions: list[QuizSession], capacity_stars: int) -> datetime | None:
        cumulative = 0
        for quiz_session in sessions:
            cumulative += quiz_session.stars_awarded or 0
            if cumulative >= capacity_stars:
                return quiz_session.finished_at
        return None
