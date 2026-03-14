"""End-to-end backend tests for upload, quiz generation, and recommendations."""

from uuid import UUID


LECTURE_TEXT = """
In this lecture we focus on eigenvalues and eigenvectors for square matrices.
Eigenvalues tell us how much a matrix stretches a special direction, while eigenvectors describe those directions.
To interpret these ideas well, students often need to recall determinants and how matrix multiplication combines transformations.
We compare geometric intuition, symbolic derivations, and common mistakes students make when solving characteristic equations.
"""


def test_upload_generate_quiz_and_hide_answers(client, demo_user_id):
    headers = {"X-User-Id": demo_user_id}
    upload_response = client.post(
        "/lectures/upload",
        data={"title": "Eigenvalue Foundations", "raw_text": LECTURE_TEXT},
        headers=headers,
    )
    assert upload_response.status_code == 200
    lecture = upload_response.json()["lecture"]
    assert lecture["title"] == "Eigenvalue Foundations"
    assert any(concept["slug"] == "determinant" for concept in lecture["concepts"])

    generate_response = client.post(
        f"/lectures/{lecture['id']}/generate-quiz",
        json={"force_regenerate": False, "questions_per_concept": 2},
        headers=headers,
    )
    assert generate_response.status_code == 200
    assert generate_response.json()["question_count"] >= 2

    session_response = client.post(
        "/quiz-sessions/start",
        json={"lecture_id": lecture["id"]},
        headers=headers,
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["session_id"]

    question_response = client.get(f"/quiz-sessions/{session_id}/questions", headers=headers)
    assert question_response.status_code == 200
    first_question = question_response.json()["questions"][0]
    assert "correct_choice_id" not in first_question
    assert len(first_question["choices"]) == 4


def test_wrong_answer_refreshes_mastery_and_orders_recommendations(client, demo_user_id):
    headers = {"X-User-Id": demo_user_id}
    lecture_response = client.post(
        "/lectures/upload",
        data={"title": "Eigenvalue Gaps", "raw_text": LECTURE_TEXT},
        headers=headers,
    )
    lecture_id = lecture_response.json()["lecture"]["id"]

    client.post(
        f"/lectures/{lecture_id}/generate-quiz",
        json={"force_regenerate": False, "questions_per_concept": 1},
        headers=headers,
    )
    session_id = client.post(
        "/quiz-sessions/start",
        json={"lecture_id": lecture_id},
        headers=headers,
    ).json()["session_id"]

    questions = client.get(f"/quiz-sessions/{session_id}/questions", headers=headers).json()["questions"]
    eigenvalue_question = next(question for question in questions if question["concept_name"] == "Eigenvalues")

    submit_response = client.post(
        f"/quiz-sessions/{session_id}/submit-answer",
        json={
            "question_id": eigenvalue_question["question_id"],
            "selected_choice_id": "B",
            "response_time_ms": 2500,
        },
        headers=headers,
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["is_correct"] is False
    assert submit_response.json()["mastery"]["mastery_score"] < 0.6

    finish_response = client.post(f"/quiz-sessions/{session_id}/finish", headers=headers)
    assert finish_response.status_code == 200
    payload = finish_response.json()
    assert payload["stars_awarded"] >= 1
    assert payload["current_jar"]["earned_stars"] == payload["stars_awarded"]
    recommendation_titles = [item["title"].lower() for item in payload["recommendations"]]
    assert any("determinant" in title for title in recommendation_titles)
    determinant_index = next(i for i, title in enumerate(recommendation_titles) if "determinant" in title)
    eigenvalues_index = next(i for i, title in enumerate(recommendation_titles) if "eigenvalues" in title)
    assert determinant_index < eigenvalues_index

    mastery_response = client.get(f"/users/{demo_user_id}/concept-mastery")
    assert mastery_response.status_code == 200
    eigenvalue_mastery = next(
        item for item in mastery_response.json() if item["concept_slug"] == "eigenvalues" and item["lecture_id"] == str(UUID(lecture_id))
    )
    assert eigenvalue_mastery["is_weak"] is True
