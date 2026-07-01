"""Тесты API примеров и in-memory хранилища"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.storage.factory import get_repository

client = TestClient(app)


def test_list_examples_returns_seed_data():
    r = client.get("/examples")
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 2
    assert all("statement" in item and "answer" not in item for item in data)


def test_create_task_from_example():
    examples = client.get("/examples").json()
    example_id = examples[0]["id"]
    r = client.post(f"/tasks/from-example/{example_id}")
    assert r.status_code == 200
    task = r.json()
    assert task["id"] and task["statement"] == examples[0]["statement"]


def test_create_task_from_unknown_example_returns_404():
    r = client.post("/tasks/from-example/does-not-exist")
    assert r.status_code == 404


def test_memory_repository_persists_grade_attempts():
    repo = get_repository()
    task_id = repo.save_task("statement", "1;2")
    attempt_id = repo.save_grade_attempt(
        task_id,
        "1;2",
        is_correct=True,
        feedback="Верно.",
        llm_provider="fake",
        duration_ms=10,
    )
    assert attempt_id
    repo.log_event("INFO", "test_event", task_id=task_id, payload={"ok": True})


def test_list_task_attempts_after_grade():
    task = client.post("/tasks").json()
    client.post(f"/tasks/{task['id']}/grade", json={"answer": "1;2"})
    r = client.get(f"/tasks/{task['id']}/attempts")
    assert r.status_code == 200
    attempts = r.json()
    assert len(attempts) == 1
    assert attempts[0]["task_id"] == task["id"]
    assert "student_answer" in attempts[0]
    assert "is_correct" in attempts[0]


def test_get_attempt_by_id():
    task = client.post("/tasks").json()
    client.post(f"/tasks/{task['id']}/grade", json={"answer": "wrong"})
    attempt_id = client.get(f"/tasks/{task['id']}/attempts").json()[0]["id"]
    r = client.get(f"/attempts/{attempt_id}")
    assert r.status_code == 200
    assert r.json()["id"] == attempt_id


def test_get_unknown_attempt_returns_404():
    r = client.get("/attempts/does-not-exist")
    assert r.status_code == 404


def test_list_task_attempts_unknown_task_returns_404():
    r = client.get("/tasks/does-not-exist/attempts")
    assert r.status_code == 404


def test_list_events_returns_grade_completed():
    task = client.post("/tasks").json()
    client.post(f"/tasks/{task['id']}/grade", json={"answer": "1"})
    r = client.get("/events", params={"task_id": task["id"]})
    assert r.status_code == 200
    events = r.json()
    assert any(item["event"] == "grade_completed" for item in events)


def test_grade_deduplicates_same_answer_without_second_llm_call(monkeypatch):
    from app import grader

    call_count = 0
    original_grade_answer = grader.grade_answer

    def counting_grade_answer(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return original_grade_answer(*args, **kwargs)

    monkeypatch.setattr("app.main.grade_answer", counting_grade_answer)

    task = client.post("/tasks").json()
    first = client.post(f"/tasks/{task['id']}/grade", json={"answer": "wrong-answer"})
    second = client.post(f"/tasks/{task['id']}/grade", json={"answer": "wrong-answer"})

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert call_count == 1

    attempts = client.get(f"/tasks/{task['id']}/attempts").json()
    assert len(attempts) == 2
    assert attempts[0]["feedback"] == attempts[1]["feedback"]
    assert attempts[1]["duration_ms"] == 0


def test_grade_different_answers_call_llm_twice(monkeypatch):
    from app import grader

    call_count = 0
    original_grade_answer = grader.grade_answer

    def counting_grade_answer(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return original_grade_answer(*args, **kwargs)

    monkeypatch.setattr("app.main.grade_answer", counting_grade_answer)

    task = client.post("/tasks").json()
    client.post(f"/tasks/{task['id']}/grade", json={"answer": "wrong-1"})
    client.post(f"/tasks/{task['id']}/grade", json={"answer": "wrong-2"})

    assert call_count == 2
