"""Регрессия по автосгенерированным «испорченным» решениям."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.task13.grader import grade_task13
from app.task13.justification import FakeJustificationLLM
from app.task13.models import Task13GradeRequest, Task13Metadata

GENERATED_DIR = Path(__file__).parent / "fixtures" / "task13" / "generated"
GENERATED_FIXTURES = sorted(GENERATED_DIR.glob("*.json"))


@pytest.mark.parametrize("fixture_path", GENERATED_FIXTURES, ids=lambda p: p.stem)
@pytest.mark.skipif(not GENERATED_FIXTURES, reason="нет generated fixtures")
def test_generated_fixture_score_stable(fixture_path: Path):
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    metadata = Task13Metadata.model_validate(data["metadata"])
    result = grade_task13(
        FakeJustificationLLM(),
        metadata,
        data["statement"],
        Task13GradeRequest(
            solution_part_a=data["solution_part_a"],
            answer_part_b=data["answer_part_b"],
        ),
    )
    assert result.response.score == data["expected_score"], (
        f"{data['name']}: ожидался score={data['expected_score']}, получен {result.response.score}"
    )
