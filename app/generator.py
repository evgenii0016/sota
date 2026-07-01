"""Генерация заданий ЕГЭ по математике.

Поддерживаются квадратные, линейные и рациональные уравнения с целыми корнями.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from app.task_types import TaskType

_ANSWER_HINT = "В ответ запишите все корни через ';' в порядке возрастания."


@dataclass
class GeneratedTask:
    statement: str  # условие для ученика
    answer: str  # эталонный ответ: корни через ';' по возрастанию
    task_type: TaskType = "quadratic"


def _fmt(n: int) -> str:
    """Знаковое слагаемое для записи уравнения: 5 -> '+ 5', -3 -> '- 3'."""
    return f"+ {n}" if n >= 0 else f"- {abs(n)}"


def _fmt_x_shift(n: int) -> str:
    """Сдвиг в скобках: 2 -> '+ 2', -3 -> '- 3'."""
    return _fmt(n)


def _fmt_x_coef(a: int) -> str:
    if a == 1:
        return "x"
    if a == -1:
        return "-x"
    return f"{a}x"


def generate_quadratic(seed: int | None = None) -> GeneratedTask:
    """Сгенерировать квадратное уравнение x^2 + bx + c = 0 с целыми корнями r1, r2.

    Уравнение строится из корней: (x - r1)(x - r2) = x^2 - (r1 + r2)x + r1*r2.
    """
    rnd = random.Random(seed)
    r1 = rnd.randint(-9, 9)
    r2 = rnd.randint(-9, 9)

    b = -(r1 + r2)
    c = r1 * r2

    statement = f"Решите уравнение: x^2 {_fmt(b)}x {_fmt(c)} = 0. {_ANSWER_HINT}"
    roots = sorted({r1, r2})
    answer = ";".join(str(r) for r in roots)
    return GeneratedTask(statement=statement, answer=answer, task_type="quadratic")


def generate_linear(seed: int | None = None) -> GeneratedTask:
    """Сгенерировать линейное уравнение ax + b = 0 с целым корнем r."""
    rnd = random.Random(seed)
    root = rnd.randint(-12, 12)
    coefficient = rnd.choice([value for value in range(-9, 10) if value != 0])
    constant = -coefficient * root

    statement = f"Решите уравнение: {_fmt_x_coef(coefficient)} {_fmt(constant)} = 0. {_ANSWER_HINT}"
    return GeneratedTask(statement=statement, answer=str(root), task_type="linear")


def generate_rational(seed: int | None = None) -> GeneratedTask:
    """Сгенерировать рациональное уравнение (x + a)/(x + b) = c с целым корнем."""
    rnd = random.Random(seed)
    for _ in range(50):
        root = rnd.randint(-9, 9)
        shift = rnd.randint(-9, 9)
        if shift == -root:
            continue
        ratio = rnd.choice([value for value in range(-4, 5) if value not in (0, 1)])
        numerator_shift = (ratio - 1) * root + ratio * shift
        statement = (
            f"Решите уравнение: (x {_fmt_x_shift(numerator_shift)})/(x {_fmt_x_shift(shift)}) "
            f"= {ratio}. {_ANSWER_HINT}"
        )
        answer = str(root)
        return GeneratedTask(statement=statement, answer=answer, task_type="rational")
    raise RuntimeError("не удалось подобрать рациональное уравнение")


_GENERATORS = {
    "quadratic": generate_quadratic,
    "linear": generate_linear,
    "rational": generate_rational,
}


def generate_task(task_type: TaskType, seed: int | None = None) -> GeneratedTask:
    try:
        generator = _GENERATORS[task_type]
    except KeyError as exc:
        raise ValueError(f"неизвестный тип задания: {task_type!r}") from exc
    return generator(seed=seed)
