"""Тесты структурных логов и Prometheus-метрик"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app import verifier
from app.main import app

client = TestClient(app)


def test_metrics_endpoint_exposes_grade_counters():
    before = client.get("/metrics")
    assert before.status_code == 200
    before_body = before.text

    task = client.post("/tasks").json()
    correct = ";".join(verifier.solve_from_statement(task["statement"]))
    client.post(f"/tasks/{task['id']}/grade", json={"answer": correct})

    after = client.get("/metrics")
    assert after.status_code == 200
    assert "ege_grader_grades_total" in after.text
    assert after.text != before_body or 'is_correct="true"' in after.text


def test_grade_completed_event_contains_quality_fields():
    task = client.post("/tasks").json()
    client.post(f"/tasks/{task['id']}/grade", json={"answer": "1;999"})

    events = client.get("/events", params={"task_id": task["id"]}).json()
    completed = [event for event in events if event["event"] == "grade_completed"]
    assert completed
    payload = completed[0]["payload"]
    assert payload["verify_status"] == "wrong"
    assert payload["feedback_source"] == "llm"
    assert payload["cached"] is False
    assert "duration_ms" in payload


def test_validation_error_increments_metric_and_returns_422():
    task = client.post("/tasks").json()
    before = client.get("/metrics").text

    response = client.post(f"/tasks/{task['id']}/grade", json={"answer": "1,2"})
    assert response.status_code == 422
    assert response.json()["code"] == "invalid_answer_format"

    after = client.get("/metrics").text
    assert "ege_grader_validation_errors_total" in after
    assert after.count("invalid_answer_format") >= before.count("invalid_answer_format")


def test_http_response_has_request_id_header():
    response = client.get("/examples")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")


def test_structured_log_emits_event_fields(caplog):
    import logging

    caplog.set_level(logging.INFO, logger="app")
    client.get("/examples")
    records = [
        record
        for record in caplog.records
        if record.name == "app" and getattr(record, "event", None) == "http_request"
    ]
    assert records
    fields = records[-1].extra_fields
    assert fields["event"] == "http_request"
    assert fields["path"] == "/examples"
    assert "duration_ms" in fields
