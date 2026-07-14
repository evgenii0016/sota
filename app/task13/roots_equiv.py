"""Эквивалентность корней на отрезке для задания 13."""

from __future__ import annotations

import re

import sympy as sp

from app.task13.trig import angle_to_storage, parse_roots_from_storage

_PI = sp.pi
_FLOAT_LITERAL_RE = re.compile(r"^\s*-?\d+\.\d+\s*$")


def _normalize_root_set(roots: list[str]) -> set[sp.Expr]:
    return {sp.nsimplify(sp.sympify(root, locals={"pi": _PI}), [_PI]) for root in roots}


def _reject_float_literals(roots: list[str]) -> None:
    for root in roots:
        if _FLOAT_LITERAL_RE.match(root.strip()):
            raise ValueError("нужно точное значение")


def roots_equivalent(student_roots: list[str], reference_roots: list[str]) -> bool:
    """Сравнить конечные множества корней символически."""
    if not student_roots or not reference_roots:
        return False

    _reject_float_literals(student_roots)
    _reject_float_literals(reference_roots)

    try:
        student_values = _normalize_root_set(student_roots)
        reference_values = _normalize_root_set(reference_roots)
    except (sp.SympifyError, TypeError, ValueError):
        return False

    return student_values == reference_values


def canonicalize_roots(roots: list[str]) -> list[str]:
    """Привести корни к каноническому символьному виду для хранения."""
    _reject_float_literals(roots)
    parsed = parse_roots_from_storage(roots)
    return [angle_to_storage(value) for value in parsed]
