"""Unit-тесты генератора задания 13."""

from __future__ import annotations

import pytest

from app.task13.generator import GeneratedTask13, generate_task13
from app.task13.judge import verify_generated_task13


def test_generate_task13_returns_required_fields():
    task = generate_task13(seed=7)
    assert isinstance(task, GeneratedTask13)
    assert task.statement.startswith("а)")
    assert "б)" in task.statement
    assert task.equation
    assert task.interval_left
    assert task.interval_right
    assert task.interval_type == "closed"
    assert task.part_a
    assert 2 <= len(task.part_b) <= 4
    assert task.solution_template
    assert task.metadata["template_family"]


def test_generate_task13_passes_judge():
    task = generate_task13(seed=11)
    assert verify_generated_task13(task) is True


def test_generate_task13_different_seeds_produce_different_equations():
    first = generate_task13(seed=1)
    second = generate_task13(seed=2)
    assert first.equation != second.equation or first.interval_display != second.interval_display


def test_generate_task13_view_excludes_reference():
    task = generate_task13(seed=3)
    view = task.to_view("00000000-0000-4000-8000-000000000001")
    payload = view.model_dump()
    assert "answer" not in payload
    assert "metadata" not in payload
    assert payload["task_type"] == "task_13"


def test_generate_task13_raises_after_interval_search_failure(monkeypatch):
    from app.task13 import generator as generator_module

    def fail_pick_interval(*args, **kwargs):
        raise RuntimeError("не удалось подобрать отрезок с 2–4 корнями")

    monkeypatch.setattr(generator_module, "pick_interval", fail_pick_interval)
    with pytest.raises(RuntimeError, match="не удалось подобрать отрезок"):
        generate_task13(seed=99)
