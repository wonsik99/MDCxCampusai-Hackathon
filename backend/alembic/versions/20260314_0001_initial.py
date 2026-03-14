"""Initial StruggleSense schema."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260314_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


lecture_source_type = sa.Enum("PDF", "TEXT", name="lecturesourcetype")
quiz_session_status = sa.Enum("IN_PROGRESS", "COMPLETED", name="quizsessionstatus")


def upgrade() -> None:
    bind = op.get_bind()
    lecture_source_type.create(bind, checkfirst=True)
    quiz_session_status.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "lectures",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", lecture_source_type, nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("cleaned_text", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("ai_metadata", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_lectures_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lectures")),
    )
    op.create_index(op.f("ix_lectures_user_id"), "lectures", ["user_id"], unique=False)

    op.create_table(
        "concepts",
        sa.Column("lecture_id", sa.Uuid(), nullable=False),
        sa.Column("prerequisite_concept_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_inferred", sa.Boolean(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lecture_id"], ["lectures.id"], name=op.f("fk_concepts_lecture_id_lectures"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["prerequisite_concept_id"],
            ["concepts.id"],
            name=op.f("fk_concepts_prerequisite_concept_id_concepts"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_concepts")),
    )
    op.create_index(op.f("ix_concepts_lecture_id"), "concepts", ["lecture_id"], unique=False)
    op.create_index(op.f("ix_concepts_prerequisite_concept_id"), "concepts", ["prerequisite_concept_id"], unique=False)
    op.create_index(op.f("ix_concepts_slug"), "concepts", ["slug"], unique=False)

    op.create_table(
        "quiz_sessions",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("lecture_id", sa.Uuid(), nullable=False),
        sa.Column("status", quiz_session_status, nullable=False),
        sa.Column("question_order", sa.JSON(), nullable=False),
        sa.Column("question_limit", sa.Integer(), nullable=True),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("correct_answers", sa.Integer(), nullable=False),
        sa.Column("current_index", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["lecture_id"], ["lectures.id"], name=op.f("fk_quiz_sessions_lecture_id_lectures"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_quiz_sessions_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quiz_sessions")),
    )
    op.create_index(op.f("ix_quiz_sessions_lecture_id"), "quiz_sessions", ["lecture_id"], unique=False)
    op.create_index(op.f("ix_quiz_sessions_user_id"), "quiz_sessions", ["user_id"], unique=False)

    op.create_table(
        "questions",
        sa.Column("lecture_id", sa.Uuid(), nullable=False),
        sa.Column("concept_id", sa.Uuid(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("choices", sa.JSON(), nullable=False),
        sa.Column("correct_choice_id", sa.String(length=8), nullable=False),
        sa.Column("wrong_answer_explanations", sa.JSON(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.id"], name=op.f("fk_questions_concept_id_concepts"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["lecture_id"], ["lectures.id"], name=op.f("fk_questions_lecture_id_lectures"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_questions")),
    )
    op.create_index(op.f("ix_questions_concept_id"), "questions", ["concept_id"], unique=False)
    op.create_index(op.f("ix_questions_lecture_id"), "questions", ["lecture_id"], unique=False)

    op.create_table(
        "concept_masteries",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("concept_id", sa.Uuid(), nullable=False),
        sa.Column("mastery_score", sa.Float(), nullable=False),
        sa.Column("correct_count", sa.Integer(), nullable=False),
        sa.Column("wrong_count", sa.Integer(), nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.id"], name=op.f("fk_concept_masteries_concept_id_concepts"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_concept_masteries_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_concept_masteries")),
        sa.UniqueConstraint("user_id", "concept_id", name=op.f("uq_concept_masteries_user_id")),
    )
    op.create_index(op.f("ix_concept_masteries_concept_id"), "concept_masteries", ["concept_id"], unique=False)
    op.create_index(op.f("ix_concept_masteries_user_id"), "concept_masteries", ["user_id"], unique=False)

    op.create_table(
        "question_attempts",
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("selected_choice_id", sa.String(length=8), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("response_time_ms", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("attempted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], name=op.f("fk_question_attempts_question_id_questions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["quiz_sessions.id"], name=op.f("fk_question_attempts_session_id_quiz_sessions"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_question_attempts_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_question_attempts")),
    )
    op.create_index(op.f("ix_question_attempts_question_id"), "question_attempts", ["question_id"], unique=False)
    op.create_index(op.f("ix_question_attempts_session_id"), "question_attempts", ["session_id"], unique=False)
    op.create_index(op.f("ix_question_attempts_user_id"), "question_attempts", ["user_id"], unique=False)

    op.create_table(
        "recommendations",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("lecture_id", sa.Uuid(), nullable=True),
        sa.Column("concept_id", sa.Uuid(), nullable=True),
        sa.Column("source_session_id", sa.Uuid(), nullable=True),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("reason_code", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.id"], name=op.f("fk_recommendations_concept_id_concepts"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["lecture_id"], ["lectures.id"], name=op.f("fk_recommendations_lecture_id_lectures"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_session_id"], ["quiz_sessions.id"], name=op.f("fk_recommendations_source_session_id_quiz_sessions"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_recommendations_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_recommendations")),
    )
    op.create_index(op.f("ix_recommendations_concept_id"), "recommendations", ["concept_id"], unique=False)
    op.create_index(op.f("ix_recommendations_lecture_id"), "recommendations", ["lecture_id"], unique=False)
    op.create_index(op.f("ix_recommendations_source_session_id"), "recommendations", ["source_session_id"], unique=False)
    op.create_index(op.f("ix_recommendations_user_id"), "recommendations", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_recommendations_user_id"), table_name="recommendations")
    op.drop_index(op.f("ix_recommendations_source_session_id"), table_name="recommendations")
    op.drop_index(op.f("ix_recommendations_lecture_id"), table_name="recommendations")
    op.drop_index(op.f("ix_recommendations_concept_id"), table_name="recommendations")
    op.drop_table("recommendations")

    op.drop_index(op.f("ix_question_attempts_user_id"), table_name="question_attempts")
    op.drop_index(op.f("ix_question_attempts_session_id"), table_name="question_attempts")
    op.drop_index(op.f("ix_question_attempts_question_id"), table_name="question_attempts")
    op.drop_table("question_attempts")

    op.drop_index(op.f("ix_concept_masteries_user_id"), table_name="concept_masteries")
    op.drop_index(op.f("ix_concept_masteries_concept_id"), table_name="concept_masteries")
    op.drop_table("concept_masteries")

    op.drop_index(op.f("ix_questions_lecture_id"), table_name="questions")
    op.drop_index(op.f("ix_questions_concept_id"), table_name="questions")
    op.drop_table("questions")

    op.drop_index(op.f("ix_quiz_sessions_user_id"), table_name="quiz_sessions")
    op.drop_index(op.f("ix_quiz_sessions_lecture_id"), table_name="quiz_sessions")
    op.drop_table("quiz_sessions")

    op.drop_index(op.f("ix_concepts_slug"), table_name="concepts")
    op.drop_index(op.f("ix_concepts_prerequisite_concept_id"), table_name="concepts")
    op.drop_index(op.f("ix_concepts_lecture_id"), table_name="concepts")
    op.drop_table("concepts")

    op.drop_index(op.f("ix_lectures_user_id"), table_name="lectures")
    op.drop_table("lectures")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    quiz_session_status.drop(bind, checkfirst=True)
    lecture_source_type.drop(bind, checkfirst=True)
