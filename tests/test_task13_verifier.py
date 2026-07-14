"""Тесты символьного верификатора задания 13 (§4.2)."""

from __future__ import annotations

from app.task13.models import Task13Metadata, Task13PartA, Task13RootSeries
from app.task13.verifier import verify_part_a, verify_part_b

REFERENCE = Task13Metadata(
    equation={"latex": r"2\sin^2 x - \sin x - 1 = 0", "sympy": "2*sin(x)**2 - sin(x) - 1"},
    interval={"left": "-pi", "right": "pi/2", "type": "closed", "display": "[−π; π/2]"},
    part_a={
        "series": [
            {"formula": "-pi/2 + 2*pi*k", "param": "k"},
            {"formula": "pi/6 + 2*pi*n", "param": "n"},
            {"formula": "5*pi/6 + 2*pi*m", "param": "m"},
        ]
    },
    part_b={"roots": ["-pi/2", "pi/6"]},
    template_family="sin_squared_substitution",
)

STATEMENT = (
    "а) Решите уравнение 2sin²x − sin x − 1 = 0.\n"
    "б) Найдите корни этого уравнения, принадлежащие отрезку [−π; π/2]."
)

SOLUTION_SCORE_2 = (
    "Замена t = sin x. 2t² − t − 1 = 0 → t = 1, t = −1/2.\n"
    "x = −π/2 + 2πk, k ∈ Z;\n"
    "x = π/6 + 2πn, n ∈ Z;\n"
    "x = 5π/6 + 2πm, m ∈ Z."
)

SOLUTION_SCORE_1_MISSING_ROOT = SOLUTION_SCORE_2
ANSWER_SCORE_1_MISSING_ROOT = "pi/6"

SOLUTION_SCORE_1_PART_B_EMPTY = SOLUTION_SCORE_2

SOLUTION_SCORE_0_WRONG_SERIES = (
    "Замена t = sin x. 2t² − t − 1 = 0 → t = 1/2.\nx = π/6 + 2πk, k ∈ Z;\nx = 5π/6 + 2πn, n ∈ Z."
)

SOLUTION_SCORE_0_DIVIDE_SIN = (
    "Делим на sin x, получаем 2sin x - 1 - 1/sin x = 0.\nx = π/6 + 2πk, k ∈ Z."
)

SOLUTION_SCORE_0_BARE = "-pi/2; pi/6"


def test_example_42_score_2_part_a_and_b():
    part_a = verify_part_a(STATEMENT, SOLUTION_SCORE_2, REFERENCE.part_a)
    part_b = verify_part_b(REFERENCE.part_b.roots, "-pi/2; pi/6", REFERENCE.interval)
    assert part_a.correct is True
    assert part_b.correct is True


def test_example_42_score_1_missing_root_in_b():
    part_a = verify_part_a(STATEMENT, SOLUTION_SCORE_1_MISSING_ROOT, REFERENCE.part_a)
    part_b = verify_part_b(
        REFERENCE.part_b.roots,
        ANSWER_SCORE_1_MISSING_ROOT,
        REFERENCE.interval,
    )
    assert part_a.correct is True
    assert part_b.correct is False


def test_example_42_score_1_part_a_only():
    part_a = verify_part_a(STATEMENT, SOLUTION_SCORE_1_PART_B_EMPTY, REFERENCE.part_a)
    assert part_a.correct is True


def test_example_42_score_0_wrong_series():
    part_a = verify_part_a(STATEMENT, SOLUTION_SCORE_0_WRONG_SERIES, REFERENCE.part_a)
    assert part_a.correct is False


def test_example_42_score_0_divide_sin_lost_series():
    part_a = verify_part_a(STATEMENT, SOLUTION_SCORE_0_DIVIDE_SIN, REFERENCE.part_a)
    assert part_a.correct is False


def test_example_42_score_0_bare_answer_without_series():
    part_a = verify_part_a(STATEMENT, SOLUTION_SCORE_0_BARE, REFERENCE.part_a)
    assert part_a.correct is False


def test_part_a_accepts_task13_part_a_model():
    reference = Task13PartA(series=[Task13RootSeries(formula="-pi/2 + 2*pi*k", param="k")])
    result = verify_part_a(
        STATEMENT,
        "x = -pi/2 + 2*pi*k, k ∈ Z",
        reference,
    )
    assert result.correct is True
