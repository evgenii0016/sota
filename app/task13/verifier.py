"""Символьная проверка ответов ученика по заданию 13 (SymPy, без LLM)."""

from __future__ import annotations

from dataclasses import dataclass

from app.task13.models import Task13Interval, Task13Metadata, Task13PartA
from app.task13.parser import (
    DecimalApproximationError,
    parse_roots_from_answer,
    parse_series_from_solution,
)
from app.task13.roots_equiv import roots_equivalent
from app.task13.series_equiv import series_sets_equivalent


@dataclass(frozen=True)
class PartAVerifyResult:
    correct: bool
    parsed_series: list | None
    errors: list[str]


@dataclass(frozen=True)
class PartBVerifyResult:
    correct: bool
    parsed_roots: list[str] | None
    errors: list[str]


def verify_part_a(
    statement: str,
    student_solution: str,
    reference: Task13PartA | Task13Metadata | dict,
) -> PartAVerifyResult:
    """Проверить пункт а: множество серий совпадает с эталоном."""
    del statement  # условие может понадобиться позже для контекстной проверки

    if isinstance(reference, Task13Metadata):
        reference_part_a = reference.part_a
    elif isinstance(reference, dict):
        reference_part_a = Task13PartA.model_validate(reference.get("part_a", reference))
    else:
        reference_part_a = reference

    try:
        parsed = parse_series_from_solution(student_solution)
    except DecimalApproximationError as exc:
        return PartAVerifyResult(correct=False, parsed_series=None, errors=[str(exc)])

    errors = list(parsed.errors)
    if not parsed.series:
        return PartAVerifyResult(correct=False, parsed_series=[], errors=errors)

    correct = series_sets_equivalent(parsed.series, reference_part_a)
    if not correct and not errors:
        errors.append("множество серий не совпадает с эталоном")

    return PartAVerifyResult(
        correct=correct,
        parsed_series=[item.raw for item in parsed.series],
        errors=errors,
    )


def verify_part_b(
    reference_roots: list[str],
    student_answer: str,
    interval: Task13Interval | dict | None = None,
) -> PartBVerifyResult:
    """Проверить пункт б: множество корней на отрезке совпадает с эталоном."""
    del interval  # MVP: сверка с эталоном; интервал для будущих проверок

    try:
        parsed = parse_roots_from_answer(student_answer)
    except DecimalApproximationError as exc:
        return PartBVerifyResult(correct=False, parsed_roots=None, errors=[str(exc)])

    errors = list(parsed.errors)
    if not parsed.roots:
        return PartBVerifyResult(correct=False, parsed_roots=[], errors=errors)

    correct = roots_equivalent(parsed.roots, reference_roots)
    if not correct and not errors:
        errors.append("множество корней не совпадает с эталоном")

    return PartBVerifyResult(
        correct=correct,
        parsed_roots=parsed.roots,
        errors=errors,
    )
