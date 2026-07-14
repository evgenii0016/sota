"""Детерминированный расчёт балла 0/1/2 по таблице ФИПИ."""

from __future__ import annotations

from app.task13.models import Task13Score


def score(
    *,
    part_a_correct: bool,
    part_b_correct: bool,
    justified: bool,
    method_errors: list[str],
    justified_part_a: bool | None = None,
    justified_part_b: bool | None = None,
) -> Task13Score:
    """Рассчитать итоговый балл; LLM не может изменить результат напрямую."""
    if method_errors:
        return 0

    part_a_ok = part_a_correct and (justified_part_a if justified_part_a is not None else justified)
    part_b_ok = part_b_correct and (justified_part_b if justified_part_b is not None else justified)
    if not part_a_correct:
        part_b_ok = False

    if part_a_correct and part_b_correct and justified:
        return 2
    if part_a_ok or part_b_ok:
        return 1
    return 0
