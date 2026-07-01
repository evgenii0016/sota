"""Тесты генератора.

Независимо от того, как генератор строит уравнение, эталонный ответ обязан реально
решать уравнение из условия. Этот тест разбирает условие отдельно (через sympy) и
сверяет с задекларированным ответом.
"""

from __future__ import annotations

import re

import sympy

from app import generator

_X = sympy.symbols("x")


def _real_roots_from_statement(statement: str) -> list[int]:
    """Независимый разбор условия: достаём уравнение и решаем его через sympy."""
    m = re.search(r"Решите уравнение:\s*(.+?)\.\s*В ответ", statement)
    assert m, f"не удалось найти уравнение в условии: {statement!r}"
    eq = m.group(1).replace("^", "**")
    eq = re.sub(r"(\d)\s*x", r"\1*x", eq)  # '5x' -> '5*x'
    lhs, rhs = eq.split("=")
    sol = sympy.solve(sympy.Eq(sympy.sympify(lhs), sympy.sympify(rhs)), _X)
    return sorted(int(s) for s in sol if s.is_real)


def test_declared_answer_actually_solves_equation():
    for seed in range(25):
        task = generator.generate_quadratic(seed=seed)
        real_roots = _real_roots_from_statement(task.statement)
        declared = sorted(int(p) for p in task.answer.split(";") if p.strip())
        assert declared == real_roots, (
            f"seed={seed}: условие {task.statement!r} -> "
            f"задекларирован ответ {declared}, реальные корни {real_roots}"
        )


def test_linear_generator_matches_sympy():
    for seed in range(25):
        task = generator.generate_linear(seed=seed)
        real_roots = _real_roots_from_statement(task.statement)
        declared = sorted(int(p) for p in task.answer.split(";") if p.strip())
        assert declared == real_roots


def test_rational_generator_matches_sympy():
    for seed in range(25):
        task = generator.generate_rational(seed=seed)
        real_roots = _real_roots_from_statement(task.statement)
        declared = sorted(int(p) for p in task.answer.split(";") if p.strip())
        assert declared == real_roots
