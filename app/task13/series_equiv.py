"""Эквивалентность серий корней задания 13."""

from __future__ import annotations

from app.task13.models import Task13PartA
from app.task13.parser import ParsedSeries, parsed_series_to_root_series
from app.task13.trig import RootSeries, parse_series_from_metadata, series_sets_match


def series_sets_equivalent(
    student_series: list[ParsedSeries],
    reference: Task13PartA | list[dict[str, str]] | list[RootSeries],
) -> bool:
    """Сравнить множества серий (порядок и буква параметра не важны)."""
    if isinstance(reference, Task13PartA):
        reference_items = reference.series
        reference_series = parse_series_from_metadata(
            [item.model_dump() for item in reference_items]
        )
    elif reference and isinstance(reference[0], RootSeries):
        reference_series = reference  # type: ignore[assignment]
    else:
        reference_series = parse_series_from_metadata(reference)  # type: ignore[arg-type]

    if not student_series:
        return False
    if not all(item.has_integer_param for item in student_series):
        return False

    student_root_series = [parsed_series_to_root_series(item) for item in student_series]
    return series_sets_match(student_root_series, reference_series)
