"""Deterministic mastery updates, weak concept detection, and ordering logic."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.models import Concept, ConceptMastery, Lecture, Question, QuestionAttempt
from app.schemas.quiz import ConceptMasterySnapshot, SessionConceptPerformance
from app.schemas.user import ConceptMasteryRead


class AnalyticsService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.settings = get_settings()

    def ensure_masteries_for_lecture(self, user_id: UUID, concepts: list[Concept]) -> None:
        existing = {
            mastery.concept_id
            for mastery in self.session.scalars(
                select(ConceptMastery).where(
                    ConceptMastery.user_id == user_id,
                    ConceptMastery.concept_id.in_([concept.id for concept in concepts]),
                )
            ).all()
        }
        for concept in concepts:
            if concept.id not in existing:
                self.session.add(
                    ConceptMastery(
                        user_id=user_id,
                        concept_id=concept.id,
                        mastery_score=self.settings.mastery_initial_score,
                    )
                )
        self.session.flush()

    def update_mastery(
        self,
        *,
        user_id: UUID,
        concept: Concept,
        is_correct: bool,
        attempted_at: datetime,
    ) -> ConceptMastery:
        mastery = self.session.scalar(
            select(ConceptMastery).where(
                ConceptMastery.user_id == user_id,
                ConceptMastery.concept_id == concept.id,
            )
        )
        if not mastery:
            mastery = ConceptMastery(
                user_id=user_id,
                concept_id=concept.id,
                mastery_score=self.settings.mastery_initial_score,
            )
            self.session.add(mastery)
            self.session.flush()

        outcome = 1.0 if is_correct else 0.0
        mastery.mastery_score = min(max((mastery.mastery_score * 0.7) + (outcome * 0.3), 0.0), 1.0)
        mastery.correct_count += 1 if is_correct else 0
        mastery.wrong_count += 0 if is_correct else 1
        mastery.last_attempt_at = attempted_at
        self.session.flush()
        return mastery

    def build_mastery_snapshot(self, concept: Concept, mastery: ConceptMastery) -> ConceptMasterySnapshot:
        return ConceptMasterySnapshot(
            concept_id=concept.id,
            concept_name=concept.name,
            mastery_score=mastery.mastery_score,
            correct_count=mastery.correct_count,
            wrong_count=mastery.wrong_count,
        )

    def get_recent_attempts(self, user_id: UUID, concept_id: UUID, limit: int = 3) -> list[QuestionAttempt]:
        attempts = self.session.scalars(
            select(QuestionAttempt)
            .join(Question, Question.id == QuestionAttempt.question_id)
            .where(QuestionAttempt.user_id == user_id, Question.concept_id == concept_id)
            .order_by(QuestionAttempt.attempted_at.desc())
            .limit(limit)
        ).all()
        return attempts

    def detect_weak_concepts(self, user_id: UUID, lecture_id: UUID | None = None) -> list[dict]:
        lecture_filter = [Lecture.user_id == user_id]
        if lecture_id:
            lecture_filter.append(Lecture.id == lecture_id)

        concepts = self.session.scalars(
            select(Concept)
            .join(Lecture, Lecture.id == Concept.lecture_id)
            .where(*lecture_filter)
            .options(joinedload(Concept.lecture))
            .order_by(Concept.display_order)
        ).unique().all()
        if not concepts:
            return []

        self.ensure_masteries_for_lecture(user_id, concepts)
        masteries = {
            mastery.concept_id: mastery
            for mastery in self.session.scalars(
                select(ConceptMastery).where(
                    ConceptMastery.user_id == user_id,
                    ConceptMastery.concept_id.in_([concept.id for concept in concepts]),
                )
            ).all()
        }

        weak: dict[UUID, dict] = {}
        concepts_by_id = {concept.id: concept for concept in concepts}
        for concept in concepts:
            mastery = masteries[concept.id]
            reasons = []
            if mastery.mastery_score < self.settings.mastery_weak_threshold:
                reasons.append("low_mastery")
            recent_attempts = self.get_recent_attempts(user_id, concept.id)
            if len(recent_attempts) >= 3 and sum(1 for attempt in recent_attempts if not attempt.is_correct) >= 2:
                reasons.append("recent_mistakes")
            if reasons:
                weak[concept.id] = {
                    "concept_id": concept.id,
                    "concept_name": concept.name,
                    "concept_slug": concept.slug,
                    "lecture_id": concept.lecture_id,
                    "lecture_title": concept.lecture.title,
                    "reason_code": reasons[0],
                    "reason_codes": reasons,
                    "mastery_score": mastery.mastery_score,
                }

        for weak_item in list(weak.values()):
            concept = concepts_by_id[weak_item["concept_id"]]
            prerequisite = concept.prerequisite_concept
            while prerequisite:
                prereq_mastery = masteries[prerequisite.id]
                if prereq_mastery.mastery_score < self.settings.mastery_prerequisite_threshold:
                    weak.setdefault(
                        prerequisite.id,
                        {
                            "concept_id": prerequisite.id,
                            "concept_name": prerequisite.name,
                            "concept_slug": prerequisite.slug,
                            "lecture_id": prerequisite.lecture_id,
                            "lecture_title": prerequisite.lecture.title,
                            "reason_code": "prerequisite_gap",
                            "reason_codes": ["prerequisite_gap"],
                            "mastery_score": prereq_mastery.mastery_score,
                        },
                    )
                prerequisite = prerequisite.prerequisite_concept

        ordered = self._sort_concepts_by_prerequisite([concepts_by_id[item["concept_id"]] for item in weak.values()])
        weak_lookup = {item["concept_id"]: item for item in weak.values()}
        return [weak_lookup[concept.id] for concept in ordered]

    def get_mastery_overview(self, user_id: UUID) -> list[ConceptMasteryRead]:
        concepts = self.session.scalars(
            select(Concept)
            .join(Lecture, Lecture.id == Concept.lecture_id)
            .where(Lecture.user_id == user_id)
            .options(joinedload(Concept.lecture))
            .order_by(Lecture.created_at.desc(), Concept.display_order)
        ).unique().all()
        if not concepts:
            return []
        self.ensure_masteries_for_lecture(user_id, concepts)
        masteries = {
            mastery.concept_id: mastery
            for mastery in self.session.scalars(
                select(ConceptMastery).where(
                    ConceptMastery.user_id == user_id,
                    ConceptMastery.concept_id.in_([concept.id for concept in concepts]),
                )
            ).all()
        }
        weak_ids = {item["concept_id"] for item in self.detect_weak_concepts(user_id)}
        return [
            ConceptMasteryRead(
                concept_id=concept.id,
                lecture_id=concept.lecture_id,
                lecture_title=concept.lecture.title,
                concept_name=concept.name,
                concept_slug=concept.slug,
                mastery_score=masteries[concept.id].mastery_score,
                correct_count=masteries[concept.id].correct_count,
                wrong_count=masteries[concept.id].wrong_count,
                prerequisite_concept_id=concept.prerequisite_concept_id,
                is_weak=concept.id in weak_ids,
            )
            for concept in concepts
        ]

    def session_performance(self, user_id: UUID, lecture_id: UUID, session_id: UUID) -> list[SessionConceptPerformance]:
        concepts = self.session.scalars(
            select(Concept)
            .where(Concept.lecture_id == lecture_id)
            .order_by(Concept.display_order)
        ).all()
        if not concepts:
            return []

        performance: list[SessionConceptPerformance] = []
        for concept in concepts:
            attempts = self.session.scalars(
                select(QuestionAttempt)
                .join(Question, Question.id == QuestionAttempt.question_id)
                .where(
                    QuestionAttempt.user_id == user_id,
                    QuestionAttempt.session_id == session_id,
                    Question.concept_id == concept.id,
                )
            ).all()
            mastery = self.session.scalar(
                select(ConceptMastery).where(
                    ConceptMastery.user_id == user_id,
                    ConceptMastery.concept_id == concept.id,
                )
            )
            if not mastery:
                continue
            performance.append(
                SessionConceptPerformance(
                    concept_id=concept.id,
                    concept_name=concept.name,
                    correct=sum(1 for attempt in attempts if attempt.is_correct),
                    wrong=sum(1 for attempt in attempts if not attempt.is_correct),
                    mastery_score=mastery.mastery_score,
                )
            )
        return performance

    def build_prerequisite_chain(self, concept: Concept) -> list[str]:
        chain = [concept.slug]
        current = concept.prerequisite_concept
        while current:
            chain.append(current.slug)
            current = current.prerequisite_concept
        return list(reversed(chain))

    def _sort_concepts_by_prerequisite(self, concepts: list[Concept]) -> list[Concept]:
        concept_lookup = {concept.id: concept for concept in concepts}
        ordered: list[Concept] = []
        visited: set[UUID] = set()

        def visit(concept: Concept) -> None:
            if concept.id in visited:
                return
            if concept.prerequisite_concept_id and concept.prerequisite_concept_id in concept_lookup:
                visit(concept_lookup[concept.prerequisite_concept_id])
            visited.add(concept.id)
            ordered.append(concept)

        for concept in sorted(concepts, key=lambda item: (item.lecture_id, item.display_order)):
            visit(concept)
        return ordered
