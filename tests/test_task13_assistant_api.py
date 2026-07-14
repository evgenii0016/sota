"""Интеграционные тесты POST /tasks/{id}/assistant для task_13."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import get_settings
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


def test_assistant_returns_reply_and_uses_left():
    task_id = _create_task13()
    r = client.post(
        f"/tasks/{task_id}/assistant",
        json={
            "message": "Почему нужно проверять ОДЗ?",
            "draft_solution": {"part_a": "2t² − t − 1 = 0", "part_b": ""},
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["reply"]
    assert "x =" not in data["reply"] or "2π" not in data["reply"]
    assert data["uses_left"] == get_settings().assistant_max_uses - 1


def test_assistant_decrements_uses_left():
    task_id = _create_task13()
    max_uses = get_settings().assistant_max_uses
    for expected_left in range(max_uses - 1, -1, -1):
        r = client.post(
            f"/tasks/{task_id}/assistant",
            json={
                "message": f"Вопрос {expected_left}",
                "draft_solution": {"part_a": "", "part_b": ""},
            },
        )
        assert r.status_code == 200
        assert r.json()["uses_left"] == expected_left


def test_assistant_limit_exceeded():
    task_id = _create_task13()
    max_uses = get_settings().assistant_max_uses
    for _ in range(max_uses):
        r = client.post(
            f"/tasks/{task_id}/assistant",
            json={"message": "Ещё вопрос", "draft_solution": {"part_a": "", "part_b": ""}},
        )
        assert r.status_code == 200

    r = client.post(
        f"/tasks/{task_id}/assistant",
        json={"message": "Лишний вопрос", "draft_solution": {"part_a": "", "part_b": ""}},
    )
    assert r.status_code == 429
    assert r.json()["code"] == "assistant_limit_exceeded"


def test_assistant_task_not_found():
    r = client.post(
        "/tasks/00000000-0000-0000-0000-000000000099/assistant",
        json={"message": "Вопрос", "draft_solution": {"part_a": "", "part_b": ""}},
    )
    assert r.status_code == 404
    assert r.json()["code"] == "task_not_found"


def test_assistant_unsupported_for_quadratic():
    created = client.post("/tasks", params={"task_type": "quadratic"})
    assert created.status_code == 200
    task_id = created.json()["id"]

    r = client.post(
        f"/tasks/{task_id}/assistant",
        json={"message": "Подскажите", "draft_solution": {"part_a": "", "part_b": ""}},
    )
    assert r.status_code == 422
    assert r.json()["code"] == "unsupported_task_type"


def test_assistant_rejects_empty_message():
    task_id = _create_task13()
    r = client.post(
        f"/tasks/{task_id}/assistant",
        json={"message": "   ", "draft_solution": {"part_a": "", "part_b": ""}},
    )
    assert r.status_code == 422


def test_assistant_accepts_dialog_history():
    task_id = _create_task13()
    r = client.post(
        f"/tasks/{task_id}/assistant",
        json={
            "message": "А если аргумент отрицательный?",
            "draft_solution": {"part_a": "log(...)", "part_b": ""},
            "history": [
                {"role": "user", "text": "Нужно ли проверять ОДЗ?"},
                {"role": "assistant", "text": "Какие ограничения на x вы видите?"},
            ],
        },
    )
    assert r.status_code == 200
    assert r.json()["reply"]
