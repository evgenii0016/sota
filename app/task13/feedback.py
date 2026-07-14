"""Пошаговые замечания по результатам verifier + justification."""

from __future__ import annotations

from app.task13.justification import JustificationResult, section_to_comment_section
from app.task13.models import Task13Comment
from app.task13.verifier import PartAVerifyResult, PartBVerifyResult


def _template_part_a_errors(part_a: PartAVerifyResult) -> list[Task13Comment]:
    comments: list[Task13Comment] = []
    if part_a.errors:
        comments.append(
            Task13Comment(
                section="серии",
                ok=False,
                text="Проверьте запись серий: параметр ∈ ℤ и формула x = … + 2πk.",
            )
        )
    if not part_a.correct:
        comments.append(
            Task13Comment(
                section="серии",
                ok=False,
                text="Множество серий не совпадает с верным ответом.",
            )
        )
    return comments


def _template_part_b_errors(part_b: PartBVerifyResult) -> list[Task13Comment]:
    comments: list[Task13Comment] = []
    if part_b.errors:
        comments.append(
            Task13Comment(
                section="ответ_б",
                ok=False,
                text=(
                    "Проверьте формат корней: точные значения через ';', "
                    "без десятичных приближений."
                ),
            )
        )
    if not part_b.correct:
        comments.append(
            Task13Comment(
                section="ответ_б",
                ok=False,
                text="Не все корни на отрезке указаны или есть лишние.",
            )
        )
    return comments


def _template_method_errors(method_errors: list[str]) -> list[Task13Comment]:
    if not method_errors:
        return []
    return [
        Task13Comment(
            section="общее",
            ok=False,
            text=error[0].upper() + error[1:] if error else "Методическая ошибка.",
        )
        for error in method_errors
    ]


def build_comments(
    *,
    part_a: PartAVerifyResult,
    part_b: PartBVerifyResult,
    justification: JustificationResult,
) -> list[Task13Comment]:
    """Сформировать comments[] без полного эталонного решения."""
    comments: list[Task13Comment] = []

    for section in justification.sections:
        comments.append(
            Task13Comment(
                section=section_to_comment_section(section.name),
                ok=section.ok,
                text=section.comment or None,
            )
        )

    comments.extend(_template_part_a_errors(part_a))
    comments.extend(_template_part_b_errors(part_b))
    comments.extend(_template_method_errors(justification.method_errors))

    if not comments:
        comments.append(
            Task13Comment(
                section="общее",
                ok=True,
                text="Решение проверено.",
            )
        )

    return _deduplicate_comments(comments)


def _deduplicate_comments(comments: list[Task13Comment]) -> list[Task13Comment]:
    seen: set[tuple[str, bool, str | None]] = set()
    unique: list[Task13Comment] = []
    for item in comments:
        key = (item.section, item.ok, item.text)
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique
