"""Тесты эквивалентности серий и корней задания 13."""

from __future__ import annotations

import pytest

from app.task13.models import Task13PartA, Task13RootSeries
from app.task13.parser import parse_series_from_solution
from app.task13.roots_equiv import roots_equivalent
from app.task13.series_equiv import series_sets_equivalent

REFERENCE_PART_A = Task13PartA(
    series=[
        Task13RootSeries(formula="-pi/2 + 2*pi*k", param="k"),
        Task13RootSeries(formula="pi/6 + 2*pi*n", param="n"),
        Task13RootSeries(formula="5*pi/6 + 2*pi*m", param="m"),
    ]
)


def test_series_equivalent_for_reference_42():
    text = "x = -π/2 + 2πk, k ∈ Z;\nx = π/6 + 2πn, n ∈ Z;\nx = 5π/6 + 2πm, m ∈ Z."
    parsed = parse_series_from_solution(text)
    assert series_sets_equivalent(parsed.series, REFERENCE_PART_A) is True


def test_series_not_equivalent_when_one_series_missing():
    text = "x = -π/2 + 2πk, k ∈ Z;\nx = π/6 + 2πn, n ∈ Z."
    parsed = parse_series_from_solution(text)
    assert series_sets_equivalent(parsed.series, REFERENCE_PART_A) is False


def test_series_not_equivalent_without_integer_parameter():
    text = "x = π/6 + 2πk"
    parsed = parse_series_from_solution(text)
    assert series_sets_equivalent(parsed.series, REFERENCE_PART_A) is False


def test_roots_equivalent_ignores_order():
    assert roots_equivalent(["pi/6", "-pi/2"], ["-pi/2", "pi/6"]) is True


def test_roots_equivalent_accepts_equal_forms():
    assert roots_equivalent(["8*pi/3"], ["2*pi + 2*pi/3"]) is True


def test_roots_reject_decimal_literals():
    with pytest.raises(ValueError, match="точное"):
        roots_equivalent(["8.377"], ["8*pi/3"])
