"""Тесты проверки ответа: вердикт от verifier, LLM только для пояснения"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import verifier
from app.grader import grade_answer
from app.llm import FakeLLM
from app.main import app

_STATEMENT = (
    "Решите уравнение: x^2 - 5x + 6 = 0. "
    "В ответ запишите все корни через ';' в порядке возрастания."
)

client = TestClient(app)


def test_grade_correct_answer_without_llm_explanation():
    result = grade_answer(FakeLLM(), _STATEMENT, "2;3", "3;2")
    assert result == {"is_correct": True, "feedback": "Верно."}


def test_grade_wrong_answer_uses_verifier_not_llm():
    result = grade_answer(FakeLLM(), _STATEMENT, "2;3", "1;6")
    assert result["is_correct"] is False
    assert result["feedback"] == "Ответ выглядит правильным."


def test_grade_wrong_root_count_skips_llm(monkeypatch):
    class FailingLLM(FakeLLM):
        def complete(self, system: str, user: str) -> str:
            raise AssertionError("LLM should not be called for wrong root count")

    result = grade_answer(FailingLLM(), _STATEMENT, "2;3", "2")
    assert result["is_correct"] is False
    assert "2" in result["feedback"] and "корн" in result["feedback"].lower()


def test_grade_wrong_root_count_single_root():
    statement = (
        "Решите уравнение: x^2 - 4x + 4 = 0. "
        "В ответ запишите все корни через ';' в порядке возрастания."
    )
    result = grade_answer(FakeLLM(), statement, "2", "2;3")
    assert result["is_correct"] is False
    assert "один корень" in result["feedback"]


def test_grade_api_rejects_wrong_answer_despite_fake_llm():
    task = client.post("/tasks").json()
    r = client.post(f"/tasks/{task['id']}/grade", json={"answer": "1;6"})
    assert r.status_code == 200
    data = r.json()
    assert data["is_correct"] is False
    assert data["feedback"]


def test_grade_api_accepts_correct_answer():
    task = client.post("/tasks").json()
    correct = ";".join(verifier.solve_from_statement(task["statement"]))
    r = client.post(f"/tasks/{task['id']}/grade", json={"answer": correct})
    assert r.status_code == 200
    assert r.json() == {"is_correct": True, "feedback": "Верно."}
