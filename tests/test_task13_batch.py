"""Тесты POST /tasks/task13/batch."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.storage.factory import get_repository
from app.task13.generator import GeneratedTask13, generate_task13
from app.task13.judge import verify_generated_task13

client = TestClient(app)

REQUIRED_VIEW_FIELDS = {
    "id",
    "task_type",
    "statement",
    "part_a_prompt",
    "part_b_prompt",
}


def test_task13_batch_default_count_returns_three_tasks():
    r = client.post("/tasks/task13/batch")
    assert r.status_code == 200
    data = r.json()
    assert "tasks" in data
    assert len(data["tasks"]) == 3


def test_task13_batch_custom_count():
    r = client.post("/tasks/task13/batch", params={"count": 2})
    assert r.status_code == 200
    assert len(r.json()["tasks"]) == 2


def test_task13_batch_task_view_shape():
    r = client.post("/tasks/task13/batch", params={"count": 1})
    assert r.status_code == 200
    task = r.json()["tasks"][0]

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


def test_task13_batch_tasks_have_different_equations():
    r = client.post("/tasks/task13/batch")
    assert r.status_code == 200
    equations = {task["equation_latex"] for task in r.json()["tasks"]}
    assert len(equations) == 3


def test_task13_batch_consecutive_calls_use_different_seeds(monkeypatch):
    seeds: list[int | None] = []
    timestamps = iter([1_000, 2_000])

    def capture_seed(seed=None):
        seeds.append(seed)
        return GeneratedTask13(
            statement="а) Решите уравнение x = 0.\nб) Найдите корни на отрезке [0; 0].",
            part_a_prompt="Решите уравнение x = 0.",
            part_b_prompt="Найдите корни на отрезке [0; 0].",
            equation_latex="x = 0",
            interval_display="[0; 0]",
            answer="0",
            metadata={},
            equation=f"x - {seed}",
            interval_left="0",
            interval_right="0",
            part_a=[],
            part_b=["0"],
        )

    import app.main as main_module

    monkeypatch.setattr(main_module, "generate_task13", capture_seed)
    monkeypatch.setattr(main_module, "verify_generated_task13", lambda task: True)
    monkeypatch.setattr(main_module.time, "time_ns", lambda: next(timestamps))

    r1 = client.post("/tasks/task13/batch", params={"count": 2})
    r2 = client.post("/tasks/task13/batch", params={"count": 2})
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert len(seeds) >= 4
    assert len(set(seeds)) > 1


def test_task13_batch_persists_tasks_in_repository():
    r = client.post("/tasks/task13/batch", params={"count": 1})
    assert r.status_code == 200
    task_id = r.json()["tasks"][0]["id"]

    repo = get_repository()
    stored = repo.get_task(task_id)
    assert stored is not None
    assert stored["task_type"] == "task_13"
    assert stored["metadata"]["equation"]["sympy"]
    assert stored["answer"]


def test_task13_batch_invalid_count_returns_422():
    r = client.post("/tasks/task13/batch", params={"count": 0})
    assert r.status_code == 422

    r = client.post("/tasks/task13/batch", params={"count": 11})
    assert r.status_code == 422


def test_task13_generated_tasks_pass_judge():
    for seed in range(3):
        assert verify_generated_task13(generate_task13(seed)) is True


def test_task13_batch_increments_generation_metrics():
    before = client.get("/metrics").text
    r = client.post("/tasks/task13/batch")
    assert r.status_code == 200
    after = client.get("/metrics").text
    assert "ege_grader_task13_generation_success_total" in after
    assert after.count("ege_grader_task13_generation_success_total") >= before.count(
        "ege_grader_task13_generation_success_total"
    )
