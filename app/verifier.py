"""Независимая проверка корректности задания и ответа средствами sympy.

Истинные корни вычисляются символически из условия — и с ними сверяются
сгенерированный ключ и ответ ученика.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

import sympy

_X = sympy.symbols("x")


def _extract_equation(statement: str) -> str:
    """Достать уравнение из текста условия и привести к sympy-синтаксису"""
    m = re.search(r":\s*(.+?=\s*0)", statement)
    if not m:
        raise ValueError(f"не удалось найти уравнение в условии: {statement!r}")
    eq = m.group(1).replace("^", "**")
    return re.sub(r"(\d)\s*x", r"\1*x", eq)


def _format_root(value: sympy.Expr) -> str:
    if not value.is_real:
        raise ValueError("уравнение имеет недействительные корни")
    if value.is_integer:
        return str(int(value))
    return str(sympy.nsimplify(value))


def _parse_answer(answer: str) -> list[str] | None:
    """Разобрать ответ 'r1;r2' в отсортированный список корней"""
    parts = [p.strip() for p in answer.split(";") if p.strip()]
    if not parts:
        return None
    try:
        normalized = _sort_roots(parts)
    except (sympy.SympifyError, TypeError, ValueError):
        return None
    return normalized


def _sort_roots(roots: list[str]) -> list[str]:
    return sorted(roots, key=lambda s: float(sympy.sympify(s)))


def solve_from_statement(statement: str) -> list[str]:
    """Вернуть реальные корни уравнения, разобранного из текста условия"""
    eq = _extract_equation(statement)
    lhs, rhs = eq.split("=")
    solutions = sympy.solve(sympy.Eq(sympy.sympify(lhs), sympy.sympify(rhs)), _X)
    real_solutions = [s for s in solutions if s.is_real]
    if not real_solutions:
        raise ValueError("уравнение не имеет действительных корней")
    roots = _sort_roots({_format_root(s) for s in real_solutions})
    return roots


@dataclass(frozen=True)
class VerifyResult:
    is_correct: bool
    status: Literal["correct", "wrong", "wrong_root_count"]
    true_roots: list[str] | None = None
    parsed_roots: list[str] | None = None


def verify_student_answer(statement: str, student_answer: str) -> VerifyResult:
    """Сверить ответ ученика с корнями, вычисленными из условия"""
    try:
        true_roots = solve_from_statement(statement)
    except (ValueError, sympy.SympifyError):
        return VerifyResult(is_correct=False, status="wrong")

    parsed_roots = _parse_answer(student_answer)
    if parsed_roots is None:
        return VerifyResult(is_correct=False, status="wrong")

    if len(parsed_roots) != len(true_roots):
        return VerifyResult(
            is_correct=False,
            status="wrong_root_count",
            true_roots=true_roots,
            parsed_roots=parsed_roots,
        )

    if parsed_roots == true_roots:
        return VerifyResult(
            is_correct=True,
            status="correct",
            true_roots=true_roots,
            parsed_roots=parsed_roots,
        )

    return VerifyResult(
        is_correct=False,
        status="wrong",
        true_roots=true_roots,
        parsed_roots=parsed_roots,
    )


def verify_task(statement: str, declared_answer: str) -> bool:
    """True, если declared_answer совпадает с реально вычисленными корнями"""
    try:
        true_roots = solve_from_statement(statement)
    except (ValueError, sympy.SympifyError):
        return False
    declared_roots = _parse_answer(declared_answer)
    if declared_roots is None:
        return False
    return declared_roots == true_roots
