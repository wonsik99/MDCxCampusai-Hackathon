"""Unit and API coverage for weekly star jar rewards."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import select

from app.models import Concept, Lecture, Question, QuestionAttempt, QuizSession, StarJar
from app.models.lecture import LectureSourceType
from app.models.quiz_session import QuizSessionStatus
from app.services.star_jar_service import StarJarService


LECTURE_TEXT = """
Matrix multiplication applies one linear transformation after another.
Determinants describe signed volume scaling.
Eigenvalues help identify special scaling factors.
"""


def create_completed_session(
    session,
    user_id: str,
    *,
    finished_at: datetime,
    response_times_ms: list[int],
    correct_answers: int,
    title: str | None = None,
) -> QuizSession:
    user_uuid = UUID(user_id)
    lecture = Lecture(
        user_id=user_uuid,
        title=title or f"Lecture {uuid4().hex[:6]}",
        source_type=LectureSourceType.TEXT,
        raw_text="lecture",
        cleaned_text="lecture",
        summary="summary",
        ai_metadata={},
    )
    session.add(lecture)
    session.flush()

    concept = Concept(
        lecture_id=lecture.id,
        name="Concept",
        slug=f"concept-{uuid4().hex[:6]}",
        display_order=0,
        is_inferred=False,
    )
    session.add(concept)
    session.flush()

    questions: list[Question] = []
    for index, _ in enumerate(response_times_ms, start=1):
        question = Question(
            lecture_id=lecture.id,
            concept_id=concept.id,
            prompt=f"Question {index}",
            choices=[
                {"choice_id": "A", "text": "Correct"},
                {"choice_id": "B", "text": "Wrong"},
                {"choice_id": "C", "text": "Distractor"},
                {"choice_id": "D", "text": "Distractor"},
            ],
            correct_choice_id="A",
            wrong_answer_explanations={"B": "Nope", "C": "Nope", "D": "Nope"},
        )
        session.add(question)
        session.flush()
        questions.append(question)

    quiz_session = QuizSession(
        user_id=user_uuid,
        lecture_id=lecture.id,
        status=QuizSessionStatus.COMPLETED,
        question_order=[str(question.id) for question in questions],
        question_limit=None,
        total_questions=len(questions),
        correct_answers=correct_answers,
        current_index=len(questions),
        started_at=finished_at - timedelta(milliseconds=sum(response_times_ms)),
        finished_at=finished_at,
    )
    session.add(quiz_session)
    session.flush()

    for index, question in enumerate(questions):
        is_correct = index < correct_answers
        session.add(
            QuestionAttempt(
                session_id=quiz_session.id,
                user_id=user_uuid,
                question_id=question.id,
                selected_choice_id="A" if is_correct else "B",
                is_correct=is_correct,
                response_time_ms=response_times_ms[index],
                explanation="Explanation",
                attempted_at=finished_at - timedelta(seconds=len(questions) - index),
            )
        )
    session.commit()
    return quiz_session


def test_award_session_calculates_stars_from_time_and_accuracy(session, demo_user_id):
    quiz_session = create_completed_session(
        session,
        demo_user_id,
        finished_at=datetime(2026, 3, 11, 15, tzinfo=timezone.utc),
        response_times_ms=[15_000, 30_000],
        correct_answers=1,
    )

    update, current_jar = StarJarService(session).award_session(quiz_session)
    session.commit()
    refreshed = session.get(QuizSession, quiz_session.id)

    assert update.study_time_ms == 45_000
    assert update.stars_awarded == 4
    assert round(update.accuracy_ratio, 2) == 0.5
    assert refreshed.study_time_ms == 45_000
    assert refreshed.stars_awarded == 4
    assert current_jar.earned_stars == 4


def test_weekly_bucketing_uses_calendar_week(session, demo_user_id):
    quiz_session = create_completed_session(
        session,
        demo_user_id,
        finished_at=datetime(2026, 3, 11, 15, tzinfo=timezone.utc),
        response_times_ms=[20_000],
        correct_answers=1,
    )

    update, current_jar = StarJarService(session).award_session(quiz_session)
    session.commit()

    assert update.week_start_date.isoformat() == "2026-03-09"
    assert update.week_end_date.isoformat() == "2026-03-15"
    assert current_jar.week_start_date.isoformat() == "2026-03-09"


def test_weekly_jar_accuracy_is_weighted_by_total_questions(session, demo_user_id):
    create_completed_session(
        session,
        demo_user_id,
        finished_at=datetime(2026, 3, 10, 14, tzinfo=timezone.utc),
        response_times_ms=[15_000, 15_000],
        correct_answers=1,
        title="Session A",
    )
    create_completed_session(
        session,
        demo_user_id,
        finished_at=datetime(2026, 3, 12, 14, tzinfo=timezone.utc),
        response_times_ms=[15_000, 15_000, 15_000, 15_000],
        correct_answers=3,
        title="Session B",
    )

    StarJarService(session).backfill_missing_rewards(UUID(demo_user_id))
    jar = session.scalar(select(StarJar).where(StarJar.user_id == UUID(demo_user_id)))

    assert jar is not None
    assert round(jar.average_accuracy, 4) == round(4 / 6, 4)


def test_award_session_is_idempotent_for_completed_sessions(session, demo_user_id):
    quiz_session = create_completed_session(
        session,
        demo_user_id,
        finished_at=datetime(2026, 3, 11, 15, tzinfo=timezone.utc),
        response_times_ms=[15_000, 15_000],
        correct_answers=2,
    )
    service = StarJarService(session)

    first_update, _ = service.award_session(quiz_session)
    session.commit()
    second_update, _ = service.award_session(quiz_session)
    session.commit()
    jar = session.scalar(select(StarJar).where(StarJar.user_id == UUID(demo_user_id)))

    assert jar is not None
    assert first_update.stars_awarded == second_update.stars_awarded
    assert jar.earned_stars == first_update.stars_awarded
    assert jar.sessions_count == 1


def test_overflow_weeks_keep_total_stars_and_cap_fill_ratio(session, demo_user_id):
    service = StarJarService(session)
    current_week_start, _ = service.resolve_week_window(datetime.now(timezone.utc))
    for offset in range(4):
        create_completed_session(
            session,
            demo_user_id,
            finished_at=datetime.combine(current_week_start + timedelta(days=offset), datetime.min.time(), timezone.utc)
            + timedelta(hours=14),
            response_times_ms=[30_000] * 10,
            correct_answers=10,
            title=f"Overflow {offset}",
        )

    response = service.get_star_jars(UUID(demo_user_id))

    assert response.current_jar is not None
    assert response.current_jar.earned_stars == 120
    assert response.current_jar.fill_ratio == 1.0
    assert response.current_jar.is_complete is True


def test_backfill_skips_sessions_that_already_have_star_rewards(session, demo_user_id):
    create_completed_session(
        session,
        demo_user_id,
        finished_at=datetime(2026, 3, 11, 15, tzinfo=timezone.utc),
        response_times_ms=[15_000, 15_000],
        correct_answers=1,
    )
    service = StarJarService(session)

    first_processed = service.backfill_missing_rewards(UUID(demo_user_id))
    first_response = service.get_star_jars(UUID(demo_user_id))
    second_processed = service.backfill_missing_rewards(UUID(demo_user_id))
    second_response = service.get_star_jars(UUID(demo_user_id))

    assert first_processed == 1
    assert second_processed == 0
    assert first_response.current_jar is not None
    assert second_response.current_jar is not None
    assert second_response.current_jar.earned_stars == first_response.current_jar.earned_stars


def test_star_jars_endpoint_returns_empty_state(client, demo_user_id):
    response = client.get(f"/users/{demo_user_id}/star-jars")

    assert response.status_code == 200
    assert response.json() == {
        "user_id": demo_user_id,
        "current_jar": None,
        "history": [],
    }


def test_finish_session_returns_star_jar_update_and_persists_rewards(client, session, demo_user_id):
    headers = {"X-User-Id": demo_user_id}
    lecture_response = client.post(
        "/lectures/upload",
        data={"title": "Jar Lecture", "raw_text": LECTURE_TEXT},
        headers=headers,
    )
    lecture_id = lecture_response.json()["lecture"]["id"]
    client.post(
        f"/lectures/{lecture_id}/generate-quiz",
        json={"force_regenerate": False, "questions_per_concept": 1},
        headers=headers,
    )
    session_id = client.post("/quiz-sessions/start", json={"lecture_id": lecture_id}, headers=headers).json()["session_id"]
    question = client.get(f"/quiz-sessions/{session_id}/questions", headers=headers).json()["questions"][0]
    client.post(
        f"/quiz-sessions/{session_id}/submit-answer",
        json={
            "question_id": question["question_id"],
            "selected_choice_id": question["choices"][0]["choice_id"],
            "response_time_ms": 20_000,
        },
        headers=headers,
    )

    finish_response = client.post(f"/quiz-sessions/{session_id}/finish", headers=headers)

    assert finish_response.status_code == 200
    payload = finish_response.json()
    assert payload["stars_awarded"] >= 1
    assert payload["star_jar_update"]["study_time_ms"] == 20_000
    assert payload["current_jar"]["sessions_count"] == 1
    assert payload["current_jar"]["earned_stars"] == payload["stars_awarded"]

    refreshed_session = session.get(QuizSession, UUID(session_id))
    jar = session.scalar(select(StarJar).where(StarJar.user_id == UUID(demo_user_id)))
    assert refreshed_session is not None
    assert refreshed_session.stars_awarded == payload["stars_awarded"]
    assert refreshed_session.study_time_ms == 20_000
    assert jar is not None
    assert jar.earned_stars == payload["stars_awarded"]
