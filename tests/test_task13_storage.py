"""Тесты сохранения и чтения task_13 в хранилище."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.storage.factory import get_repository
from app.storage.memory import MemoryRepository
from app.task13.models import Task13Metadata

SAMPLE_METADATA = Task13Metadata(
    equation={
        "latex": r"2\sin^2 x - \sin x - 1 = 0",
        "sympy": "2*sin(x)**2 - sin(x) - 1",
    },
    interval={
        "left": "-pi",
        "right": "pi/2",
        "type": "closed",
        "display": "[−π; π/2]",
    },
    part_a={
        "series": [
            {"formula": "-pi/2 + 2*pi*k", "param": "k", "display": "x = −π/2 + 2πk, k ∈ ℤ"},
            {"formula": "pi/6 + 2*pi*n", "param": "n", "display": "x = π/6 + 2πn, n ∈ ℤ"},
        ]
    },
    part_b={"roots": ["-pi/2", "pi/6"]},
    template_family="sin_squared_substitution",
)

SAMPLE_STATEMENT = (
    "а) Решите уравнение 2sin²x − sin x − 1 = 0.\n"
    "б) Найдите корни этого уравнения, принадлежащие отрезку [−π; π/2]."
)
SAMPLE_ANSWER = "-pi/2; pi/6"
SAMPLE_SOLUTION_A = (
    "Замена t = sin x. 2t² − t − 1 = 0 → t = 1, t = −1/2.\n"
    "x = −π/2 + 2πk, k ∈ Z;\nx = π/6 + 2πn, n ∈ Z."
)
SAMPLE_COMMENTS = [
    {"section": "преобразование", "ok": True, "text": "Замена выполнена корректно."},
    {"section": "серии", "ok": True, "text": "Серии записаны с параметром ∈ ℤ."},
]


def test_memory_assistant_use_reservation_is_atomic():
    repo = MemoryRepository()
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda _: repo.reserve_assistant_use("task", 5), range(10)))

    assert sorted(value for value in results if value is not None) == [0, 1, 2, 3, 4]
    assert results.count(None) == 5
    assert repo.count_assistant_uses("task") == 5


def test_save_and_get_task_13_with_metadata():
    repo = get_repository()
    metadata = SAMPLE_METADATA.model_dump()

    task_id = repo.save_task(
        SAMPLE_STATEMENT,
        SAMPLE_ANSWER,
        task_type="task_13",
        metadata=metadata,
    )

    task = repo.get_task(task_id)
    assert task is not None
    assert task["task_type"] == "task_13"
    assert task["statement"] == SAMPLE_STATEMENT
    assert task["answer"] == SAMPLE_ANSWER
    assert task["metadata"]["equation"]["sympy"] == "2*sin(x)**2 - sin(x) - 1"
    assert task["metadata"]["part_b"]["roots"] == ["-pi/2", "pi/6"]
    assert task["metadata"]["template_family"] == "sin_squared_substitution"


def test_save_and_get_task_13_grade_attempt():
    repo = get_repository()
    task_id = repo.save_task(
        SAMPLE_STATEMENT,
        SAMPLE_ANSWER,
        task_type="task_13",
        metadata=SAMPLE_METADATA.model_dump(),
    )

    attempt_id = repo.save_grade_attempt(
        task_id,
        SAMPLE_ANSWER,
        is_correct=True,
        feedback="Верно.",
        score=2,
        solution_part_a=SAMPLE_SOLUTION_A,
        answer_part_b="-pi/2; pi/6",
        comments=SAMPLE_COMMENTS,
        part_a_correct=True,
        part_b_correct=True,
        justified=True,
        justified_part_a=True,
        justified_part_b=True,
        method_errors=[],
        llm_provider="fake",
        duration_ms=42,
    )

    attempt = repo.get_grade_attempt(attempt_id)
    assert attempt is not None
    assert attempt["task_id"] == task_id
    assert attempt["score"] == 2
    assert attempt["solution_part_a"] == SAMPLE_SOLUTION_A
    assert attempt["answer_part_b"] == "-pi/2; pi/6"
    assert attempt["comments"] == SAMPLE_COMMENTS
    assert attempt["part_a_correct"] is True
    assert attempt["part_b_correct"] is True
    assert attempt["justified"] is True
    assert attempt["is_correct"] is True
    assert attempt["feedback"] == "Верно."


def test_list_task_13_grade_attempts():
    repo = get_repository()
    task_id = repo.save_task(
        SAMPLE_STATEMENT,
        SAMPLE_ANSWER,
        task_type="task_13",
        metadata=SAMPLE_METADATA.model_dump(),
    )
    repo.save_grade_attempt(
        task_id,
        "-pi/2; pi/6",
        is_correct=True,
        feedback="2 балла",
        score=2,
        solution_part_a=SAMPLE_SOLUTION_A,
        answer_part_b="-pi/2; pi/6",
        comments=SAMPLE_COMMENTS,
    )
    repo.save_grade_attempt(
        task_id,
        "pi/6",
        is_correct=False,
        feedback="0 баллов",
        score=0,
        solution_part_a="Неполное решение.",
        answer_part_b="pi/6",
        comments=[{"section": "ответ_б", "ok": False, "text": "Пропущен корень."}],
    )

    attempts = repo.list_grade_attempts(task_id)
    assert len(attempts) == 2
    assert attempts[0]["score"] == 2
    assert attempts[1]["score"] == 0
    assert attempts[0]["solution_part_a"] == SAMPLE_SOLUTION_A
    assert attempts[1]["answer_part_b"] == "pi/6"


def test_quadratic_task_metadata_defaults_to_empty():
    repo = get_repository()
    task_id = repo.save_task("Решите: x^2 - 1 = 0", "1;-1")

    task = repo.get_task(task_id)
    assert task is not None
    assert task["task_type"] == "quadratic"
    assert task["metadata"] == {}


def test_quadratic_grade_attempt_task_13_fields_are_none():
    repo = get_repository()
    task_id = repo.save_task("Решите: x^2 - 1 = 0", "1;-1")
    attempt_id = repo.save_grade_attempt(
        task_id,
        "1;-1",
        is_correct=True,
        feedback="Верно.",
    )

    attempt = repo.get_grade_attempt(attempt_id)
    assert attempt is not None
    assert attempt["score"] is None
    assert attempt["solution_part_a"] is None
    assert attempt["answer_part_b"] is None
    assert attempt["comments"] is None
