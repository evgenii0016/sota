"""Тесты расчёта балла задания 13."""

from __future__ import annotations

import pytest

from app.task13.scoring import score


@pytest.mark.parametrize(
    ("part_a", "part_b", "justified", "justified_a", "justified_b", "errors", "expected"),
    [
        (True, True, True, True, True, [], 2),
        (True, False, True, True, False, [], 1),
        (True, False, True, True, True, [], 1),
        (False, True, True, False, True, [], 0),
        (False, True, False, False, False, [], 0),
        (True, True, False, False, False, [], 0),
        (True, True, True, True, True, ["деление на sin x"], 0),
        (False, False, True, True, True, [], 0),
    ],
)
def test_score_table(
    part_a: bool,
    part_b: bool,
    justified: bool,
    justified_a: bool,
    justified_b: bool,
    errors: list[str],
    expected: int,
):
    assert (
        score(
            part_a_correct=part_a,
            part_b_correct=part_b,
            justified=justified,
            method_errors=errors,
            justified_part_a=justified_a,
            justified_part_b=justified_b,
        )
        == expected
    )
