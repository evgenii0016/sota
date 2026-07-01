"""Тесты валидации ответа и формата ошибок API"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.models import GradeRequest
from app.validation import validate_student_answer

client = TestClient(app)

_UNKNOWN_TASK_ID = "00000000-0000-4000-8000-000000000099"


@pytest.mark.parametrize(
    ("answer", "expected"),
    [
        ("2;3", "2;3"),
        (" 3 ; 2 ", "3;2"),
        ("-1;0;5", "-1;0;5"),
        ("1/2", "1/2"),
        ("0.5", "0.5"),
    ],
)
def test_validate_student_answer_accepts_valid_formats(answer: str, expected: str):
    assert validate_student_answer(answer) == expected


@pytest.mark.parametrize(
    "answer",
    ["", "   ", "2,3", "abc", "2;x", "2;;3", "2;2", "2;3;"],
)
def test_validate_student_answer_rejects_invalid_formats(answer: str):
    with pytest.raises(ValueError):
        validate_student_answer(answer)


def test_grade_request_rejects_empty_answer():
    with pytest.raises(ValidationError):
        GradeRequest(answer="")


def test_grade_api_rejects_empty_answer_with_422():
    task = client.post("/tasks").json()
    r = client.post(f"/tasks/{task['id']}/grade", json={"answer": ""})
    assert r.status_code == 422
    data = r.json()
    assert data["code"] == "invalid_answer_format"
    assert data["field"] == "answer"


def test_grade_api_rejects_comma_separator():
    task = client.post("/tasks").json()
    r = client.post(f"/tasks/{task['id']}/grade", json={"answer": "2,3"})
    assert r.status_code == 422
    assert r.json()["code"] == "invalid_answer_format"
    assert ";" in r.json()["message"]


def test_grade_api_rejects_non_numeric_answer():
    task = client.post("/tasks").json()
    r = client.post(f"/tasks/{task['id']}/grade", json={"answer": "abc"})
    assert r.status_code == 422
    assert r.json()["code"] == "invalid_answer_format"


def test_grade_unknown_task_returns_404_with_code():
    r = client.post(f"/tasks/{_UNKNOWN_TASK_ID}/grade", json={"answer": "1;2"})
    assert r.status_code == 404
    assert r.json() == {
        "code": "task_not_found",
        "message": "Задание не найдено",
        "field": None,
    }


def test_grade_invalid_task_id_returns_422():
    r = client.post("/tasks/not-a-uuid/grade", json={"answer": "1;2"})
    assert r.status_code == 422
    assert r.json()["code"] == "invalid_id"


def test_events_limit_out_of_range_returns_422():
    r = client.get("/events", params={"limit": 0})
    assert r.status_code == 422
    assert r.json()["code"] == "invalid_query_param"
