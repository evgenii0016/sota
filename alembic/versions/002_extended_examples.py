"""Add linear and rational demo examples"""

from __future__ import annotations

import uuid

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "002_extended_examples"
down_revision = "001_initial"
branch_labels = None
depends_on = None

EXTENDED_EXAMPLE_IDS = (
    uuid.UUID("11111111-1111-4111-8111-111111111103"),
    uuid.UUID("11111111-1111-4111-8111-111111111104"),
)


def upgrade() -> None:
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
                "id": EXTENDED_EXAMPLE_IDS[0],
                "name": "Линейное уравнение",
                "task_type": "linear",
                "statement": (
                    "Решите уравнение: 2x - 6 = 0. "
                    "В ответ запишите все корни через ';' в порядке возрастания."
                ),
                "answer": "3",
                "tags": ["linear"],
                "is_active": True,
            },
            {
                "id": EXTENDED_EXAMPLE_IDS[1],
                "name": "Рациональное уравнение",
                "task_type": "rational",
                "statement": (
                    "Решите уравнение: (x + 16)/(x + 2) = 3. "
                    "В ответ запишите все корни через ';' в порядке возрастания."
                ),
                "answer": "5",
                "tags": ["rational"],
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    connection = op.get_bind()
    for example_id in EXTENDED_EXAMPLE_IDS:
        connection.execute(
            sa.text("DELETE FROM examples WHERE id = :id"),
            {"id": example_id},
        )
