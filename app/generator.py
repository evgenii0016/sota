"""Генерация заданий ЕГЭ по математике.

Пока поддержан один тип: квадратное уравнение с целыми корнями.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass
class GeneratedTask:
    statement: str  # условие для ученика
    answer: str  # эталонный ответ: корни через ';' по возрастанию


def _fmt(n: int) -> str:
    """Знаковое слагаемое для записи уравнения: 5 -> '+ 5', -3 -> '- 3'."""
    return f"+ {n}" if n >= 0 else f"- {abs(n)}"


def generate_quadratic(seed: int | None = None) -> GeneratedTask:
    """Сгенерировать квадратное уравнение x^2 + bx + c = 0 с целыми корнями r1, r2.

    Уравнение строится из корней: (x - r1)(x - r2) = x^2 - (r1 + r2)x + r1*r2.
    """
    rnd = random.Random(seed)
    r1 = rnd.randint(-9, 9)
    r2 = rnd.randint(-9, 9)

    b = -(r1 + r2)
    c = r1 * r2

    statement = (
        f"Решите уравнение: x^2 {_fmt(b)}x {_fmt(c)} = 0. "
        f"В ответ запишите все корни через ';' в порядке возрастания."
    )
    roots = sorted({r1, r2})
    answer = ";".join(str(r) for r in roots)
    return GeneratedTask(statement=statement, answer=answer)
