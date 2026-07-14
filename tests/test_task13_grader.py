"""Тесты grade_task13 и §4.2."""

from __future__ import annotations

from app.task13.grader import grade_task13
from app.task13.justification import FakeJustificationLLM, JustificationInput, JustificationResult
from app.task13.models import Task13GradeRequest, Task13Metadata

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
    "x = 5π/6 + 2πm, m ∈ Z.\n"
    "Отбор на отрезке [−π; π/2]: k = 0, ±1."
)

ANSWER_SCORE_2 = "-pi/2; pi/6"


class AlwaysJustifiedLLM:
    """Имитирует «слишком оптимистичную» LLM — балл всё равно считает scoring."""

    def evaluate(self, data: JustificationInput) -> JustificationResult:
        return JustificationResult(
            justified=True,
            justified_part_a=True,
            justified_part_b=True,
            method_errors=[],
            sections=[],
        )


def test_golden_solution_scores_2():
    result = grade_task13(
        FakeJustificationLLM(),
        REFERENCE,
        STATEMENT,
        Task13GradeRequest(solution_part_a=SOLUTION_SCORE_2, answer_part_b=ANSWER_SCORE_2),
    )
    assert result.response.score == 2
    assert result.response.part_a_correct is True
    assert result.response.part_b_correct is True
    assert result.response.justified is True


def test_missing_root_scores_1():
    result = grade_task13(
        FakeJustificationLLM(),
        REFERENCE,
        STATEMENT,
        Task13GradeRequest(solution_part_a=SOLUTION_SCORE_2, answer_part_b="pi/6"),
    )
    assert result.response.score == 1
    assert result.response.part_a_correct is True
    assert result.response.part_b_correct is False


def test_wrong_series_scores_0():
    result = grade_task13(
        FakeJustificationLLM(),
        REFERENCE,
        STATEMENT,
        Task13GradeRequest(
            solution_part_a=("x = π/6 + 2πk, k ∈ Z;\nx = 5π/6 + 2πn, n ∈ Z."),
            answer_part_b="pi/6",
        ),
    )
    assert result.response.score == 0


def test_bare_answer_scores_0():
    result = grade_task13(
        FakeJustificationLLM(),
        REFERENCE,
        STATEMENT,
        Task13GradeRequest(
            solution_part_a="-pi/2; pi/6",
            answer_part_b="-pi/2; pi/6",
        ),
    )
    assert result.response.score == 0


def test_optimistic_llm_cannot_raise_score_when_part_a_wrong():
    result = grade_task13(
        AlwaysJustifiedLLM(),
        REFERENCE,
        STATEMENT,
        Task13GradeRequest(
            solution_part_a="x = π/6 + 2πk, k ∈ Z",
            answer_part_b="-pi/2; pi/6",
        ),
    )
    assert result.response.part_a_correct is False
    assert result.response.score == 0


def test_optimistic_external_llm_cannot_change_score():
    import json

    class OptimisticStubLLM:
        def complete(self, _system: str, _prompt: str) -> str:
            return json.dumps(
                {
                    "justified": True,
                    "justified_part_a": True,
                    "justified_part_b": True,
                    "method_errors": [],
                    "sections": [],
                    "odz_issue_affects_answer": False,
                },
                ensure_ascii=False,
            )

    result = grade_task13(
        OptimisticStubLLM(),
        REFERENCE,
        STATEMENT,
        Task13GradeRequest(
            solution_part_a="x = −π/2 + 2πk, k ∈ Z; x = π/6 + 2πn, n ∈ Z.",
            answer_part_b="-pi/2; pi/6",
        ),
        llm_provider="gigachat",
    )

    assert result.response.part_a_correct is False
    assert result.response.part_b_correct is True
    assert result.response.justified is True
    assert result.response.score == 0
