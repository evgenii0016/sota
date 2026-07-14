"""Интеграционные тесты GET /tasks/{id} для task_13 и legacy-типов."""

from __future__ import annotations

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


def _create_task13() -> str:
    repo = get_repository()
    return repo.save_task(
        STATEMENT,
        "-pi/2; pi/6",
        task_type="task_13",
        metadata=REFERENCE.model_dump(),
    )


def test_get_task13_returns_task13_view():
    task_id = _create_task13()
    r = client.get(f"/tasks/{task_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == task_id
    assert data["task_type"] == "task_13"
    assert data["statement"] == STATEMENT
    assert data["part_a_prompt"].startswith("Решите уравнение")
    assert data["part_b_prompt"].startswith("Найдите корни")
    assert data["interval_display"] == "[−π; π/2]"
    assert data["equation_latex"] == r"2\sin^2 x - \sin x - 1 = 0"
    assert "answer" not in data
    assert "metadata" not in data


def test_get_task13_from_batch():
    created = client.post("/tasks/task13/batch", params={"count": 1})
    assert created.status_code == 200
    expected = created.json()["tasks"][0]

    r = client.get(f"/tasks/{expected['id']}")
    assert r.status_code == 200
    assert r.json() == expected


def test_get_quadratic_returns_task_view():
    created = client.post("/tasks", params={"task_type": "quadratic"})
    assert created.status_code == 200
    task = created.json()

    r = client.get(f"/tasks/{task['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data == {"id": task["id"], "statement": task["statement"]}
    assert "task_type" not in data


def test_get_task_not_found():
    r = client.get("/tasks/00000000-0000-0000-0000-000000000099")
    assert r.status_code == 404
    assert r.json()["code"] == "task_not_found"
