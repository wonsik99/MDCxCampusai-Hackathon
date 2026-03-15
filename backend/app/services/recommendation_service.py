"""Recommendation generation built on deterministic weak-concept analytics."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from app.models import Concept, Recommendation
from app.schemas.user import RecommendationRead, RecommendationsResponse
from app.services.ai_service import AIService
from app.services.analytics_service import AnalyticsService


class RecommendationService:
    def __init__(
        self,
        session: Session,
        analytics_service: AnalyticsService | None = None,
        ai_service: AIService | None = None,
    ) -> None:
        self.session = session
        self.analytics_service = analytics_service or AnalyticsService(session)
        self.ai_service = ai_service or AIService()

    def refresh_recommendations(
        self,
        user_id,
        lecture_id=None,
        source_session_id=None,
        include_ai_copy: bool = True,
    ) -> RecommendationsResponse:
        weak_concepts = self.analytics_service.detect_weak_concepts(user_id, lecture_id)
        concepts = self.session.scalars(
            select(Concept)
            .options(joinedload(Concept.lecture), joinedload(Concept.prerequisite_concept))
            .where(Concept.id.in_([item["concept_id"] for item in weak_concepts]))
        ).unique().all()
        concepts_by_id = {concept.id: concept for concept in concepts}
        prerequisite_chains = [
            self.analytics_service.build_prerequisite_chain(concepts_by_id[item["concept_id"]])
            for item in weak_concepts
            if item["concept_id"] in concepts_by_id
        ]
        mastery_data = [
            {
                "concept_slug": item["concept_slug"],
                "mastery_score": item["mastery_score"],
                "reason_codes": item["reason_codes"],
            }
            for item in weak_concepts
        ]
        ai_copy = (
            self.ai_service.generate_recommendation(weak_concepts, prerequisite_chains, mastery_data)
            if weak_concepts and include_ai_copy
            else None
        )
        ai_messages = {item.concept_slug: item for item in (ai_copy.recommendations if ai_copy else [])}

        self.session.execute(delete(Recommendation).where(Recommendation.user_id == user_id))
        persisted: list[Recommendation] = []
        if not weak_concepts:
            persisted.append(
                Recommendation(
                    user_id=user_id,
                    lecture_id=None,
                    concept_id=None,
                    source_session_id=source_session_id,
                    rank=1,
                    reason_code="maintain_strengths",
                    title="Maintain your momentum",
                    message="No weak concepts are currently flagged. Review one challenge problem to keep these ideas active.",
                )
            )
        else:
            for index, weak_item in enumerate(weak_concepts, start=1):
                concept = concepts_by_id[weak_item["concept_id"]]
                ai_message = ai_messages.get(concept.slug)
                persisted.append(
                    Recommendation(
                        user_id=user_id,
                        lecture_id=concept.lecture_id,
                        concept_id=concept.id,
                        source_session_id=source_session_id,
                        rank=index,
                        reason_code=weak_item["reason_code"],
                        title=ai_message.title if ai_message else f"Study {concept.name} next",
                        message=(
                            ai_message.message
                            if ai_message
                            else f"Revisit {concept.name} before moving deeper because it is currently blocking later concepts."
                        ),
                    )
                )

        self.session.add_all(persisted)
        self.session.commit()
        stored = self.session.scalars(
            select(Recommendation)
            .options(joinedload(Recommendation.lecture), joinedload(Recommendation.concept))
            .where(Recommendation.user_id == user_id)
            .order_by(Recommendation.rank)
        ).unique().all()
        return RecommendationsResponse(user_id=user_id, recommendations=self._to_reads(stored))

    def get_recommendations(self, user_id, refresh_with_ai: bool = False) -> RecommendationsResponse:
        if refresh_with_ai:
            return self.refresh_recommendations(user_id, include_ai_copy=True)

        existing = self.session.scalars(
            select(Recommendation)
            .options(joinedload(Recommendation.lecture), joinedload(Recommendation.concept))
            .where(Recommendation.user_id == user_id)
            .order_by(Recommendation.rank)
        ).unique().all()
        if not existing:
            return self.refresh_recommendations(user_id)
        return RecommendationsResponse(user_id=user_id, recommendations=self._to_reads(existing))

    def _to_reads(self, recommendations: list[Recommendation]) -> list[RecommendationRead]:
        reads = []
        for item in sorted(recommendations, key=lambda rec: rec.rank):
            reads.append(
                RecommendationRead(
                    recommendation_id=item.id,
                    rank=item.rank,
                    lecture_id=item.lecture_id,
                    lecture_title=item.lecture.title if item.lecture else None,
                    concept_id=item.concept_id,
                    concept_name=item.concept.name if item.concept else None,
                    reason_code=item.reason_code,
                    title=item.title,
                    message=item.message,
                )
            )
        return reads
