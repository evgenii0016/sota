"""Add task_13 metadata and grade attempt fields"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "003_task_13"
down_revision = "002_extended_examples"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "tasks",
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )

    op.add_column("grade_attempts", sa.Column("score", sa.Integer(), nullable=True))
    op.add_column("grade_attempts", sa.Column("solution_part_a", sa.Text(), nullable=True))
    op.add_column("grade_attempts", sa.Column("answer_part_b", sa.Text(), nullable=True))
    op.add_column(
        "grade_attempts",
        sa.Column("comments", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )
    op.create_check_constraint(
        "ck_grade_attempts_score",
        "grade_attempts",
        "score IS NULL OR score IN (0, 1, 2)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_grade_attempts_score", "grade_attempts", type_="check")
    op.drop_column("grade_attempts", "comments")
    op.drop_column("grade_attempts", "answer_part_b")
    op.drop_column("grade_attempts", "solution_part_a")
    op.drop_column("grade_attempts", "score")
    op.drop_column("tasks", "metadata")
