"""Тесты линейных/рациональных заданий и ключа расширенных примеров."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings_cache
from app.main import app

client = TestClient(app)

EXTENDED_HEADER = {"X-Extended-Examples-Key": "test-extended-key"}
LINEAR_EXAMPLE_ID = "11111111-1111-4111-8111-111111111103"
RATIONAL_EXAMPLE_ID = "11111111-1111-4111-8111-111111111104"


@pytest.fixture(autouse=True)
def extended_examples_key(monkeypatch):
    monkeypatch.setenv("EXTENDED_EXAMPLES_KEY", "test-extended-key")
    reset_settings_cache()
    yield
    reset_settings_cache()


def test_list_examples_without_key_returns_only_standard():
    r = client.get("/examples")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 2
    assert {item["task_type"] for item in data} == {"quadratic"}


def test_list_examples_with_key_includes_extended():
    r = client.get("/examples", headers=EXTENDED_HEADER)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 4
    assert {item["task_type"] for item in data} == {"quadratic", "linear", "rational"}


def test_create_linear_task_without_key_returns_403():
    r = client.post("/tasks", params={"task_type": "linear"})
    assert r.status_code == 403
    assert r.json()["code"] == "extended_access_required"


def test_create_linear_task_with_key():
    r = client.post("/tasks", params={"task_type": "linear"}, headers=EXTENDED_HEADER)
    assert r.status_code == 200
    assert r.json()["statement"].startswith("Решите уравнение:")


def test_create_rational_task_with_key():
    r = client.post("/tasks", params={"task_type": "rational"}, headers=EXTENDED_HEADER)
    assert r.status_code == 200
    assert "/" in r.json()["statement"]


def test_create_task_from_extended_example_without_key_returns_404():
    r = client.post(f"/tasks/from-example/{LINEAR_EXAMPLE_ID}")
    assert r.status_code == 404
    assert r.json()["code"] == "example_not_found"


def test_create_task_from_extended_example_with_key():
    r = client.post(f"/tasks/from-example/{LINEAR_EXAMPLE_ID}", headers=EXTENDED_HEADER)
    assert r.status_code == 200
    assert "2x - 6 = 0" in r.json()["statement"]


def test_create_task_from_rational_example_with_key():
    r = client.post(f"/tasks/from-example/{RATIONAL_EXAMPLE_ID}", headers=EXTENDED_HEADER)
    assert r.status_code == 200
    assert "(x + 16)/(x + 2) = 3" in r.json()["statement"]


def test_invalid_task_type_returns_422():
    r = client.post("/tasks", params={"task_type": "integral"})
    assert r.status_code == 422
    assert r.json()["code"] == "invalid_task_type"
