"""Тесты парсинга и fallback для LLM-обоснованности задания 13."""

from __future__ import annotations

import json

from app.task13.justification import (
    JustificationInput,
    JustificationResult,
    _normalize_llm_payload,
    evaluate_justification,
)


class StubLLM:
    def __init__(self, response: str) -> None:
        self.response = response

    def complete(self, _system: str, _prompt: str) -> str:
        return self.response


def test_normalize_expands_pipe_section_names():
    payload = {
        "justified": True,
        "justified_part_a": True,
        "justified_part_b": True,
        "method_errors": [],
        "sections": [
            {
                "name": "одз|преобразование|серии|отбор",
                "ok": False,
                "comment": "шаблон скопирован целиком",
            }
        ],
        "odz_issue_affects_answer": False,
    }

    normalized = _normalize_llm_payload(payload)
    names = [section["name"] for section in normalized["sections"]]

    assert names == ["одз", "преобразование", "серии", "отбор"]
    assert JustificationResult.model_validate(normalized).sections[0].name == "одз"


def test_evaluate_justification_accepts_gigachat_pipe_template():
    raw = json.dumps(
        {
            "justified": True,
            "justified_part_a": True,
            "justified_part_b": False,
            "method_errors": [],
            "sections": [
                {
                    "name": "одз|преобразование|серии|отбор",
                    "ok": True,
                    "comment": "ok",
                }
            ],
            "odz_issue_affects_answer": False,
        },
        ensure_ascii=False,
    )
    data = JustificationInput(
        statement="а) ... б) ...",
        solution_part_a="Замена t = sin x, получаем x = pi/6 + 2pi k",
        answer_part_b="pi/6",
        part_a_correct=True,
        part_b_correct=True,
    )

    result = evaluate_justification(StubLLM(raw), data, llm_provider="gigachat")

    assert isinstance(result, JustificationResult)
    assert len(result.sections) == 4
    assert all(section.comment == "ok" for section in result.sections)
    assert result.justified is True


def test_evaluate_justification_falls_back_on_invalid_json():
    data = JustificationInput(
        statement="а) ... б) ...",
        solution_part_a="Замена t = sin x, получаем x = pi/6 + 2pi k, k in Z",
        answer_part_b="pi/6",
        part_a_correct=True,
        part_b_correct=True,
    )

    result = evaluate_justification(StubLLM("not json"), data, llm_provider="gigachat")

    assert isinstance(result, JustificationResult)
    assert result.justified is True


def test_evaluate_justification_uses_valid_llm_for_scoring_fields():
    raw = json.dumps(
        {
            "justified": True,
            "justified_part_a": True,
            "justified_part_b": True,
            "method_errors": [],
            "sections": [
                {"name": "преобразование", "ok": True, "comment": "LLM: всё отлично"},
            ],
            "odz_issue_affects_answer": False,
        },
        ensure_ascii=False,
    )
    data = JustificationInput(
        statement="а) ... б) ...",
        solution_part_a="-pi/2; pi/6",
        answer_part_b="-pi/2; pi/6",
        part_a_correct=False,
        part_b_correct=True,
    )

    result = evaluate_justification(StubLLM(raw), data, llm_provider="gigachat")

    assert result.justified is True
    assert result.justified_part_a is True
    assert result.justified_part_b is True
    assert any(section.comment == "LLM: всё отлично" for section in result.sections)


def test_bare_series_listing_is_not_substantive_work():
    from app.task13.justification import _has_substantive_work

    assert _has_substantive_work("x = −π/2 + 2πk, k ∈ Z; x = π/6 + 2πn, n ∈ Z.") is False
    assert _has_substantive_work("Замена t = sin x. 2t² − t − 1 = 0 → t = 1, t = −1/2.") is True


def test_evaluate_justification_falls_back_on_missing_required_fields():
    data = JustificationInput(
        statement="а) ... б) ...",
        solution_part_a="-pi/2; pi/6",
        answer_part_b="-pi/2; pi/6",
        part_a_correct=False,
        part_b_correct=False,
    )

    result = evaluate_justification(StubLLM('{"sections": []}'), data, llm_provider="gigachat")

    assert isinstance(result, JustificationResult)
    assert result.justified is False
