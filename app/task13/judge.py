"""Судья генерации задания 13."""

from __future__ import annotations

import re

from app.task13.generator import GeneratedTask13
from app.task13.trig import (
    is_tabular_angle,
    parse_equation,
    parse_roots_from_storage,
    parse_series_from_metadata,
    roots_on_interval,
    roots_to_storage,
    series_sets_match,
    solve_equation_series,
)


def verify_generated_task13(task: GeneratedTask13) -> bool:
    """Пересчитать корни из equation и сверить с эталоном в metadata."""
    if not _statement_is_valid(task.statement, task.part_a_prompt, task.part_b_prompt):
        return False

    metadata = task.metadata
    equation_text = metadata.get("equation", {}).get("sympy") or task.equation
    if not equation_text:
        return False

    try:
        equation = parse_equation(equation_text)
    except (ValueError, TypeError):
        return False

    try:
        recomputed_series = solve_equation_series(equation)
    except (ValueError, TypeError):
        return False

    declared_series = parse_series_from_metadata(metadata.get("part_a", {}).get("series", []))
    if not declared_series:
        return False
    if not series_sets_match(recomputed_series, declared_series):
        return False

    if not all(is_tabular_angle(item.offset) for item in recomputed_series):
        return False
    if not all(item.get("param") for item in metadata.get("part_a", {}).get("series", [])):
        return False
    if not all(
        "∈" in (item.get("display") or "") for item in metadata.get("part_a", {}).get("series", [])
    ):
        return False

    interval = metadata.get("interval", {})
    left_text = interval.get("left") or task.interval_left
    right_text = interval.get("right") or task.interval_right
    if not left_text or not right_text:
        return False

    try:
        left = parse_roots_from_storage([left_text])[0]
        right = parse_roots_from_storage([right_text])[0]
    except (ValueError, IndexError, TypeError):
        return False

    declared_roots = metadata.get("part_b", {}).get("roots", task.part_b)
    if not declared_roots or not (2 <= len(declared_roots) <= 4):
        return False

    try:
        declared_root_values = parse_roots_from_storage(declared_roots)
    except (ValueError, TypeError):
        return False

    if not all(is_tabular_angle(root) for root in declared_root_values):
        return False

    recomputed_roots = roots_on_interval(recomputed_series, left, right)
    return roots_to_storage(recomputed_roots) == list(declared_roots)


def _statement_is_valid(statement: str, part_a_prompt: str, part_b_prompt: str) -> bool:
    if not statement or not part_a_prompt or not part_b_prompt:
        return False
    if "а)" not in statement or "б)" not in statement:
        return False
    if part_a_prompt not in statement or part_b_prompt not in statement:
        return False
    if not re.search(r"Решите уравнение", part_a_prompt):
        return False
    return bool(re.search(r"Найдите корни", part_b_prompt))
