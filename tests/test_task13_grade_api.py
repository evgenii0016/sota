"""Интеграционные тесты POST /tasks/{id}/grade для task_13."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage.factory import get_repository
from app.task13.models import Task13Metadata

client = TestClient(app)

REFERENCE = Task13Metadata(
    equation={"latex": r"2\sin^2 x - \sin x - 1 = 0", "sympy": "2*sin(x)**2 - sin(x) - 1"},
    interval={"left": "-pi", "right": "pi/2", "type": "closed", "display": "[−π; π/2]"},
    part_a={
        "series": [
            {"formula": "-pi/2 + 2*pi*k", "param": "k"},
            {"formula": "pi/6 + 2*pi*n", "param": "n"},
            {"formula": "5*pi/6 + 2*pi*m", "param": "m"},
        ]
    },
    part_b={"roots": ["-pi/2", "pi/6"]},
    template_family="sin_squared_substitution",
)

STATEMENT = (
    "а) Решите уравнение 2sin²x − sin x − 1 = 0.\n"
    "б) Найдите корни этого уравнения, принадлежащие отрезку [−π; π/2]."
)

SOLUTION = (
    "Замена t = sin x. 2t² − t − 1 = 0 → t = 1, t = −1/2.\n"
    "x = −π/2 + 2πk, k ∈ Z;\n"
    "x = π/6 + 2πn, n ∈ Z;\n"
    "x = 5π/6 + 2πm, m ∈ Z.\n"
    "Отбор на отрезке [−π; π/2]."
)


def _create_task13() -> str:
    repo = get_repository()
    return repo.save_task(
        STATEMENT,
        "-pi/2; pi/6",
        task_type="task_13",
        metadata=REFERENCE.model_dump(),
    )


def test_grade_task13_returns_score_and_comments():
    task_id = _create_task13()
    r = client.post(
        f"/tasks/{task_id}/grade",
        json={
            "solution_part_a": SOLUTION,
            "answer_part_b": "-pi/2; pi/6",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["score"] == 2
    assert data["part_a_correct"] is True
    assert data["part_b_correct"] is True
    assert data["justified"] is True
    assert isinstance(data["comments"], list)
    assert data["attempt_id"]


@pytest.mark.parametrize("decimal", ["8.377", "0.5", "1.25"])
def test_grade_task13_rejects_decimal_in_part_b(decimal: str):
    task_id = _create_task13()
    r = client.post(
        f"/tasks/{task_id}/grade",
        json={
            "solution_part_a": SOLUTION,
            "answer_part_b": decimal,
        },
    )
    assert r.status_code == 422


@pytest.mark.parametrize("decimal", ["8.377", "0.5", "1.25"])
def test_grade_task13_rejects_decimal_in_part_a(decimal: str):
    task_id = _create_task13()
    r = client.post(
        f"/tasks/{task_id}/grade",
        json={
            "solution_part_a": f"{SOLUTION}\nx = {decimal}",
            "answer_part_b": "-pi/2; pi/6",
        },
    )
    assert r.status_code == 422
    assert r.json()["code"] == "validation_error"
    assert r.json()["field"] == "solution_part_a"


def test_grade_task13_accepts_empty_part_b_for_part_a_score():
    task_id = _create_task13()
    r = client.post(
        f"/tasks/{task_id}/grade",
        json={
            "solution_part_a": SOLUTION,
            "answer_part_b": "",
        },
    )
    assert r.status_code == 200
    assert r.json()["score"] == 1


def test_grade_quadratic_still_works():
    created = client.post("/tasks", params={"task_type": "quadratic"})
    assert created.status_code == 200
    task_id = created.json()["id"]
    r = client.post(
        f"/tasks/{task_id}/grade",
        json={"answer": "1;2"},
    )
    assert r.status_code == 200
    assert "is_correct" in r.json()
    assert "feedback" in r.json()


def test_grade_task13_not_found():
    r = client.post(
        "/tasks/00000000-0000-0000-0000-000000000099/grade",
        json={"solution_part_a": "x = pi/6 + 2pi k", "answer_part_b": "pi/6"},
    )
    assert r.status_code == 404
