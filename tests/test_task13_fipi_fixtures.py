"""Тесты задач в стиле банка ФИПИ."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.task13.grader import grade_task13
from app.task13.justification import FakeJustificationLLM
from app.task13.models import Task13GradeRequest, Task13Metadata

FIPI_DIR = Path(__file__).parent / "fixtures" / "task13" / "fipi"
FIPI_FIXTURES = sorted(FIPI_DIR.glob("*.json"))


def _cases(fixture_path: Path) -> list[tuple[str, dict]]:
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    task_id = data.get("fipi_id", fixture_path.stem)
    return [(f"{task_id}:{item['name']}", data, item) for item in data["solutions"]]


CASES: list[tuple[str, dict, dict]] = []
for path in FIPI_FIXTURES:
    CASES.extend(_cases(path))


@pytest.mark.parametrize("case_id,task_data,solution", CASES, ids=[c[0] for c in CASES])
def test_fipi_fixture_solution(case_id: str, task_data: dict, solution: dict):
    metadata = Task13Metadata.model_validate(task_data["metadata"])
    request = Task13GradeRequest(
        solution_part_a=solution["solution_part_a"],
        answer_part_b=solution["answer_part_b"],
    )
    result = grade_task13(
        FakeJustificationLLM(),
        metadata,
        task_data["statement"],
        request,
    )
    assert result.response.score == solution["expected_score"], (
        f"{case_id}: ожидался score={solution['expected_score']}, получен {result.response.score}"
    )
