"""Тесты парсера ответов задания 13."""

from __future__ import annotations

import pytest

from app.task13.parser import (
    DecimalApproximationError,
    parse_roots_from_answer,
    parse_series_from_solution,
)


def test_parse_series_accepts_pi_and_latex_variants():
    text = "x = -\\pi/2 + 2\\pi k, k \\in Z\nx = pi/6 + 2*pi*n, n ∈ ℤ\nx = 5π/6 + 2πm, m — целое"
    result = parse_series_from_solution(text)
    assert len(result.series) == 3
    assert result.errors == []
    assert all(item.has_integer_param for item in result.series)


def test_parse_series_rejects_decimal_approximation():
    with pytest.raises(DecimalApproximationError, match="точное"):
        parse_series_from_solution("x = pi/6 + 2*pi*k, k ∈ Z; примерно 8.377")


@pytest.mark.parametrize("value", ["0.5", "1.25", ".5", "8.377"])
def test_parse_series_rejects_any_decimal_approximation(value: str):
    with pytest.raises(DecimalApproximationError, match="точное"):
        parse_series_from_solution(f"x = {value} + 2*pi*k, k ∈ Z")


def test_parse_series_marks_missing_integer_parameter():
    result = parse_series_from_solution("x = pi/6 + 2*pi*k")
    assert len(result.series) == 1
    assert result.series[0].has_integer_param is False
    assert any("∈ Z" in error for error in result.errors)


def test_parse_roots_from_semicolon_list():
    result = parse_roots_from_answer("-pi/2; pi/6")
    assert result.roots == ["-pi/2", "pi/6"]
    assert result.errors == []


def test_parse_roots_from_set_notation():
    result = parse_roots_from_answer("{-π/2, pi/6}")
    assert result.roots == ["-pi/2", "pi/6"]


def test_parse_roots_from_mathlive_latex_fractions():
    result = parse_roots_from_answer(r"-\frac{\pi}{2}; \frac{\pi}{6}")
    assert result.roots == ["-pi/2", "pi/6"]
    assert result.errors == []


def test_parse_series_from_mathlive_latex_fractions():
    result = parse_series_from_solution(
        r"x = -\frac{\pi}{2} + 2\pi k, k \in \mathbb{Z}",
    )
    assert len(result.series) == 1
    assert result.errors == []
    assert result.series[0].has_integer_param is True


def test_parse_roots_rejects_decimal():
    with pytest.raises(DecimalApproximationError):
        parse_roots_from_answer("8.377")


@pytest.mark.parametrize("value", ["0.5", "1.25", ".5"])
def test_parse_roots_rejects_any_decimal_approximation(value: str):
    with pytest.raises(DecimalApproximationError, match="точное"):
        parse_roots_from_answer(value)
