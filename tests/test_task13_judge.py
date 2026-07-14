"""Unit-тесты судьи генерации задания 13."""

from __future__ import annotations

import copy

from app.task13.generator import generate_task13
from app.task13.judge import verify_generated_task13


def test_judge_accepts_valid_generated_task():
    task = generate_task13(seed=21)
    assert verify_generated_task13(task) is True


def test_judge_rejects_corrupted_part_b_roots():
    task = generate_task13(seed=22)
    corrupted = copy.deepcopy(task)
    corrupted.metadata["part_b"]["roots"] = ["pi/99"]
    corrupted.part_b = ["pi/99"]
    assert verify_generated_task13(corrupted) is False


def test_judge_rejects_corrupted_equation():
    task = generate_task13(seed=23)
    corrupted = copy.deepcopy(task)
    corrupted.metadata["equation"]["sympy"] = "sin(x) - 2"
    corrupted.equation = "sin(x) - 2"
    assert verify_generated_task13(corrupted) is False


def test_judge_rejects_invalid_statement():
    task = generate_task13(seed=24)
    corrupted = copy.deepcopy(task)
    corrupted.statement = "Решите уравнение"
    assert verify_generated_task13(corrupted) is False


def test_judge_rejects_missing_integer_parameter_marker():
    task = generate_task13(seed=25)
    corrupted = copy.deepcopy(task)
    series = corrupted.metadata["part_a"]["series"]
    series[0]["display"] = "x = pi/2 + 2pi k"
    assert verify_generated_task13(corrupted) is False
