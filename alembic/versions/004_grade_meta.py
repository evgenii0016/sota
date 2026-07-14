"""Add grade_meta JSONB for task_13 grade details"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "004_grade_meta"
down_revision = "003_task_13"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "grade_attempts",
        sa.Column("grade_meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("grade_attempts", "grade_meta")
