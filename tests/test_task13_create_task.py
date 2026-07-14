"""Тесты POST /tasks?task_type=task_13."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.storage.factory import get_repository
from app.task13.generator import GeneratedTask13
from app.task13.judge import verify_generated_task13

client = TestClient(app)

REQUIRED_VIEW_FIELDS = {
    "id",
    "task_type",
    "statement",
    "part_a_prompt",
    "part_b_prompt",
}


def test_create_task13_returns_task13_view():
    r = client.post("/tasks", params={"task_type": "task_13"})
    assert r.status_code == 200
    task = r.json()

    assert set(task.keys()) >= REQUIRED_VIEW_FIELDS
    assert task["task_type"] == "task_13"
    assert task["statement"].startswith("а)")
    assert "б)" in task["statement"]
    assert task["part_a_prompt"].startswith("Решите уравнение")
    assert task["part_b_prompt"].startswith("Найдите корни")
    assert task.get("interval_display")
    assert task.get("equation_latex")
    assert "answer" not in task
    assert "metadata" not in task


def test_create_task13_persists_in_repository():
    r = client.post("/tasks", params={"task_type": "task_13"})
    assert r.status_code == 200
    task_id = r.json()["id"]

    stored = get_repository().get_task(task_id)
    assert stored is not None
    assert stored["task_type"] == "task_13"
    assert stored["metadata"]["equation"]["sympy"]
    assert stored["answer"]


def test_create_task13_passes_judge():
    r = client.post("/tasks", params={"task_type": "task_13"})
    assert r.status_code == 200
    stored = get_repository().get_task(r.json()["id"])
    assert stored is not None
    assert verify_generated_task13(GeneratedTask13.from_stored(stored)) is True


def test_create_task13_get_returns_same_view():
    created = client.post("/tasks", params={"task_type": "task_13"})
    assert created.status_code == 200
    expected = created.json()

    fetched = client.get(f"/tasks/{expected['id']}")
    assert fetched.status_code == 200
    assert fetched.json() == expected


def test_create_quadratic_still_returns_task_view():
    r = client.post("/tasks", params={"task_type": "quadratic"})
    assert r.status_code == 200
    data = r.json()
    assert set(data.keys()) == {"id", "statement"}
    assert "answer" not in data
