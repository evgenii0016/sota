"""Initial schema and example seed data."""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None

EXAMPLE_IDS = (
    uuid.UUID("11111111-1111-4111-8111-111111111101"),
    uuid.UUID("11111111-1111-4111-8111-111111111102"),
)


def upgrade() -> None:
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_type", sa.String(length=32), nullable=False, server_default="quadratic"),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("idx_tasks_created_at", "tasks", ["created_at"])

    op.create_table(
        "examples",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False, server_default="quadratic"),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("'{}'"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.create_table(
        "grade_attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_answer", sa.Text(), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("llm_provider", sa.String(length=32), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
    )
    op.create_index("idx_grade_attempts_task_id", "grade_attempts", ["task_id", "created_at"])

    op.create_table(
        "app_events",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("event", sa.String(length=64), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="SET NULL"),
    )
    op.create_index("idx_app_events_created_at", "app_events", ["created_at"])
    op.create_index("idx_app_events_event", "app_events", ["event"])

    examples = sa.table(
        "examples",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("task_type", sa.String()),
        sa.column("statement", sa.Text()),
        sa.column("answer", sa.Text()),
        sa.column("tags", postgresql.ARRAY(sa.String())),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        examples,
        [
            {
                "id": EXAMPLE_IDS[0],
                "name": "Два различных корня",
                "task_type": "quadratic",
                "statement": (
                    "Решите уравнение: x^2 - 5x + 6 = 0. "
                    "В ответ запишите все корни через ';' в порядке возрастания."
                ),
                "answer": "2;3",
                "tags": ["two_roots"],
                "is_active": True,
            },
            {
                "id": EXAMPLE_IDS[1],
                "name": "Двойной корень",
                "task_type": "quadratic",
                "statement": (
                    "Решите уравнение: x^2 - 4x + 4 = 0. "
                    "В ответ запишите все корни через ';' в порядке возрастания."
                ),
                "answer": "2",
                "tags": ["double_root"],
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index("idx_app_events_event", table_name="app_events")
    op.drop_index("idx_app_events_created_at", table_name="app_events")
    op.drop_table("app_events")
    op.drop_index("idx_grade_attempts_task_id", table_name="grade_attempts")
    op.drop_table("grade_attempts")
    op.drop_table("examples")
    op.drop_index("idx_tasks_created_at", table_name="tasks")
    op.drop_table("tasks")
