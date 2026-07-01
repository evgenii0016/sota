"""Тесты независимого верификатора."""

from __future__ import annotations

import pytest

from app import generator, verifier

_STATEMENT = (
    "Решите уравнение: x^2 - 5x + 6 = 0. "
    "В ответ запишите все корни через ';' в порядке возрастания."
)
_DOUBLE_ROOT_STATEMENT = (
    "Решите уравнение: x^2 - 4x + 4 = 0. "
    "В ответ запишите все корни через ';' в порядке возрастания."
)
_NO_REAL_ROOTS_STATEMENT = (
    "Решите уравнение: x^2 + 1 = 0. В ответ запишите все корни через ';' в порядке возрастания."
)


def test_solve_from_statement():
    assert verifier.solve_from_statement(_STATEMENT) == ["2", "3"]


def test_verify_accepts_correct_answer():
    assert verifier.verify_task(_STATEMENT, "2;3") is True


def test_verify_accepts_answer_with_whitespace_and_wrong_order():
    assert verifier.verify_task(_STATEMENT, "3 ; 2") is True


def test_verify_rejects_wrong_answer():
    assert verifier.verify_task(_STATEMENT, "1;6") is False


def test_verify_double_root():
    assert verifier.solve_from_statement(_DOUBLE_ROOT_STATEMENT) == ["2"]
    assert verifier.verify_task(_DOUBLE_ROOT_STATEMENT, "2") is True


def test_verify_no_real_roots():
    with pytest.raises(ValueError, match="действительных"):
        verifier.solve_from_statement(_NO_REAL_ROOTS_STATEMENT)
    assert verifier.verify_task(_NO_REAL_ROOTS_STATEMENT, "") is False


def test_verify_student_answer_wrong_root_count():
    result = verifier.verify_student_answer(_STATEMENT, "2")
    assert result.is_correct is False
    assert result.status == "wrong_root_count"
    assert result.true_roots == ["2", "3"]


def test_verify_student_answer_correct():
    result = verifier.verify_student_answer(_STATEMENT, "3;2")
    assert result.is_correct is True
    assert result.status == "correct"


def test_verify_rational_equation():
    statement = (
        "Решите уравнение: (x + 16)/(x + 2) = 3. "
        "В ответ запишите все корни через ';' в порядке возрастания."
    )
    assert verifier.solve_from_statement(statement) == ["5"]
    assert verifier.verify_task(statement, "5") is True


def test_verify_linear_equation():
    statement = (
        "Решите уравнение: 2x - 6 = 0. В ответ запишите все корни через ';' в порядке возрастания."
    )
    assert verifier.solve_from_statement(statement) == ["3"]
    assert verifier.verify_task(statement, "3") is True


def test_verify_rejects_invalid_answer_format():
    assert verifier.verify_task(_STATEMENT, "abc") is False
    assert verifier.verify_task(_STATEMENT, "") is False


def test_generator_tasks_pass_verifier():
    for seed in range(25):
        for generate in (
            generator.generate_quadratic,
            generator.generate_linear,
            generator.generate_rational,
        ):
            task = generate(seed=seed)
            assert verifier.verify_task(task.statement, task.answer) is True
