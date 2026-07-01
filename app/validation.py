"""Валидация и нормализация ответа ученика"""

from __future__ import annotations

import re

import sympy

_MAX_ANSWER_LENGTH = 64
_ROOT_TOKEN_RE = re.compile(r"^-?\d+(\.\d+)?(/-?\d+)?$|^-?\d*\.\d+$")


def _validate_root_token(token: str) -> str:
    if not _ROOT_TOKEN_RE.match(token):
        raise ValueError(f"Некорректное число: {token}")
    try:
        expr = sympy.sympify(token)
    except (sympy.SympifyError, TypeError, ValueError) as exc:
        raise ValueError(f"Некорректное число: {token}") from exc
    if not expr.is_number or expr.has(sympy.Symbol):
        raise ValueError(f"Некорректное число: {token}")
    return token


def validate_student_answer(answer: str) -> str:
    """Проверить формат ответа и вернуть нормализованную строку."""
    normalized = answer.strip()
    if not normalized:
        raise ValueError("Укажите хотя бы один корень")
    if len(normalized) > _MAX_ANSWER_LENGTH:
        raise ValueError(f"Ответ слишком длинный (максимум {_MAX_ANSWER_LENGTH} символов)")
    if "," in normalized:
        raise ValueError("Разделяйте корни символом ';', например: 2;3")

    parts = [part.strip() for part in normalized.split(";")]
    if any(not part for part in parts):
        raise ValueError("Пустые значения между ';' не допускаются")
    if len(parts) != len(set(parts)):
        raise ValueError("Корни не должны повторяться")

    validated = [_validate_root_token(part) for part in parts]
    return ";".join(validated)
