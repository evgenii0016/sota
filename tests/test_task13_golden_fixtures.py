"""Параметризованные тесты золотого набора §4.2."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.task13.grader import grade_task13
from app.task13.justification import FakeJustificationLLM
from app.task13.models import Task13GradeRequest, Task13Metadata

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "task13"
GOLDEN_FIXTURES = sorted(
    path for path in FIXTURES_DIR.glob("*.json") if not path.name.startswith("_")
)


def _load_fixture(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_request(data: dict) -> Task13GradeRequest:
    return Task13GradeRequest(
        solution_part_a=data["solution_part_a"],
        answer_part_b=data.get("answer_part_b", ""),
    )


@pytest.mark.parametrize("fixture_path", GOLDEN_FIXTURES, ids=lambda p: p.stem)
def test_golden_fixture_score(fixture_path: Path):
    data = _load_fixture(fixture_path)
    metadata = Task13Metadata.model_validate(data["metadata"])
    result = grade_task13(
        FakeJustificationLLM(),
        metadata,
        data["statement"],
        _build_request(data),
    )
    assert result.response.score == data["expected_score"], (
        f"{data['name']}: ожидался score={data['expected_score']}, получен {result.response.score}"
    )
