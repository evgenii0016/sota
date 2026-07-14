"""Генератор задания 13 ЕГЭ."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any

from app.task13.models import Task13Metadata, Task13View
from app.task13.templates import TemplateResult, build_template
from app.task13.trig import (
    RootSeries,
    expr_to_latex,
    expr_to_sympy_text,
    interval_to_storage,
    is_tabular_angle,
    pick_interval,
    readable_equation_text,
    roots_to_storage,
    solve_equation_series,
)


@dataclass
class GeneratedTask13:
    statement: str
    part_a_prompt: str
    part_b_prompt: str
    equation_latex: str
    interval_display: str
    answer: str
    metadata: dict[str, Any]
    equation: str
    interval_left: str
    interval_right: str
    interval_type: str = "closed"
    part_a: list[dict[str, str]] = field(default_factory=list)
    part_b: list[str] = field(default_factory=list)
    solution_template: str = ""

    def to_view(self, task_id: str) -> Task13View:
        return Task13View(
            id=task_id,
            statement=self.statement,
            part_a_prompt=self.part_a_prompt,
            part_b_prompt=self.part_b_prompt,
            interval_display=self.interval_display,
            equation_latex=self.equation_latex,
        )

    @classmethod
    def from_stored(cls, stored: dict[str, Any]) -> GeneratedTask13:
        """Восстановить задание из репозитория (для судьи и тестов)."""
        metadata = stored["metadata"]
        statement = stored["statement"]
        part_a_prompt, part_b_prompt = _parse_statement_prompts(statement)
        interval = metadata["interval"]
        return cls(
            statement=statement,
            part_a_prompt=part_a_prompt,
            part_b_prompt=part_b_prompt,
            equation_latex=metadata["equation"]["latex"],
            interval_display=interval.get("display") or "",
            answer=stored["answer"],
            metadata=metadata,
            equation=metadata["equation"]["sympy"],
            interval_left=interval["left"],
            interval_right=interval["right"],
            interval_type=interval.get("type", "closed"),
            part_a=list(metadata["part_a"]["series"]),
            part_b=list(metadata["part_b"]["roots"]),
            solution_template=metadata.get("solution_template") or "",
        )


def _parse_statement_prompts(statement: str) -> tuple[str, str]:
    prefix_a = "а) "
    delimiter_b = "\nб) "
    if not statement.startswith(prefix_a) or delimiter_b not in statement:
        raise ValueError(f"некорректный statement: {statement!r}")
    part_a_prompt, part_b_prompt = statement.removeprefix(prefix_a).split(delimiter_b, 1)
    return part_a_prompt, part_b_prompt


def _validate_series_tabular(series_list: list[RootSeries]) -> bool:
    return all(is_tabular_angle(item.offset) for item in series_list)


def _build_from_parts(
    template: TemplateResult,
    series_list: list[RootSeries],
    left,
    right,
    roots,
) -> GeneratedTask13:
    left_text, right_text, interval_display = interval_to_storage(left, right)
    part_a = [item.to_dict() for item in series_list]
    part_b = roots_to_storage(roots)
    equation_text = readable_equation_text(template.equation)
    part_a_prompt = f"Решите уравнение {equation_text.replace(' = 0', '')} = 0."
    part_b_prompt = f"Найдите корни этого уравнения, принадлежащие отрезку {interval_display}."
    statement = f"а) {part_a_prompt}\nб) {part_b_prompt}"
    equation_latex = expr_to_latex(template.equation)
    equation_sympy = expr_to_sympy_text(template.equation)

    metadata = Task13Metadata(
        equation={"latex": equation_latex, "sympy": equation_sympy},
        interval={
            "left": left_text,
            "right": right_text,
            "type": "closed",
            "display": interval_display,
        },
        part_a={"series": part_a},
        part_b={"roots": part_b},
        template_family=template.template_family,
        solution_template=template.solution_template,
    )

    return GeneratedTask13(
        statement=statement,
        part_a_prompt=part_a_prompt,
        part_b_prompt=part_b_prompt,
        equation_latex=equation_latex,
        interval_display=interval_display,
        answer=";".join(part_b),
        metadata=metadata.model_dump(),
        equation=equation_sympy,
        interval_left=left_text,
        interval_right=right_text,
        part_a=part_a,
        part_b=part_b,
        solution_template=template.solution_template,
    )


def generate_task13(seed: int | None = None) -> GeneratedTask13:
    """Сгенерировать задание 13: уравнение, серии корней и отрезок для пункта б."""
    rnd = random.Random(seed)
    template = build_template(rnd.randint(0, 10_000_000))
    series_list = solve_equation_series(template.equation)
    if not _validate_series_tabular(series_list):
        raise RuntimeError("сгенерированы нетабличные корни")

    left, right, roots = pick_interval(series_list, rnd=rnd.randint(0, 10_000_000))
    if not all(is_tabular_angle(root) for root in roots):
        raise RuntimeError("на отрезке получились нетабличные корни")

    return _build_from_parts(template, series_list, left, right, roots)
