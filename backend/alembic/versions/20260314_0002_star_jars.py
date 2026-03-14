"""Add weekly star jar support."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260314_0002"
down_revision: Union[str, None] = "20260314_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("quiz_sessions", sa.Column("study_time_ms", sa.Integer(), nullable=True))
    op.add_column("quiz_sessions", sa.Column("accuracy_ratio", sa.Float(), nullable=True))
    op.add_column("quiz_sessions", sa.Column("stars_awarded", sa.Integer(), nullable=True))
    op.add_column("quiz_sessions", sa.Column("star_jar_week_start", sa.Date(), nullable=True))
    op.create_index(op.f("ix_quiz_sessions_star_jar_week_start"), "quiz_sessions", ["star_jar_week_start"], unique=False)

    op.create_table(
        "star_jars",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("week_start_date", sa.Date(), nullable=False),
        sa.Column("week_end_date", sa.Date(), nullable=False),
        sa.Column("capacity_stars", sa.Integer(), nullable=False),
        sa.Column("earned_stars", sa.Integer(), nullable=False),
        sa.Column("study_time_ms", sa.Integer(), nullable=False),
        sa.Column("sessions_count", sa.Integer(), nullable=False),
        sa.Column("average_accuracy", sa.Float(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_star_jars_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_star_jars")),
        sa.UniqueConstraint("user_id", "week_start_date", name="uq_star_jars_user_id_week_start_date"),
    )
    op.create_index(op.f("ix_star_jars_user_id"), "star_jars", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_star_jars_user_id"), table_name="star_jars")
    op.drop_table("star_jars")

    op.drop_index(op.f("ix_quiz_sessions_star_jar_week_start"), table_name="quiz_sessions")
    op.drop_column("quiz_sessions", "star_jar_week_start")
    op.drop_column("quiz_sessions", "stars_awarded")
    op.drop_column("quiz_sessions", "accuracy_ratio")
    op.drop_column("quiz_sessions", "study_time_ms")
