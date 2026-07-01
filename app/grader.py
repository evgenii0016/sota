"""Проверка свободного ответа ученика."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Literal

from app import verifier
from app.llm import LLM
from app.metrics import observe_verify, record_llm_call

FEEDBACK_SYSTEM = (
    "Ты - репетитор по математике. Ученик уже получил оценку «неверно». "
    "Кратко и доброжелательно объясни, в чём ошибка и как правильно записать ответ. "
    "Не выноси вердикт - только пояснение. Ответь одним абзацем текста."
)

_DEFAULT_WRONG_FEEDBACK = (
    "Ответ неверен. Проверьте вычисления и запишите все корни через ';' в порядке возрастания."
)

FeedbackSource = Literal["correct", "template_wrong_root_count", "llm", "default_fallback"]


@dataclass(frozen=True)
class GradeResult:
    is_correct: bool
    feedback: str
    verify_status: str
    feedback_source: FeedbackSource
    llm_duration_ms: int | None = None

    def as_api_dict(self) -> dict[str, str | bool]:
        return {"is_correct": self.is_correct, "feedback": self.feedback}


def _wrong_root_count_feedback(true_roots: list[str]) -> str:
    count = len(true_roots)
    if count == 1:
        return f"В уравнении один корень. Укажите только его, например: {true_roots[0]}."
    roots_word = "корня" if 2 <= count % 10 <= 4 and not 12 <= count % 100 <= 14 else "корней"
    return f"В уравнении {count} {roots_word}. Укажите все через ';' в порядке возрастания."


def _true_answer(statement: str, fallback: str) -> str:
    try:
        return ";".join(verifier.solve_from_statement(statement))
    except (ValueError, Exception):
        return fallback


def grade_answer(
    llm: LLM,
    statement: str,
    declared_answer: str,
    student_answer: str,
    *,
    llm_provider: str = "fake",
) -> GradeResult:
    """Проверить ответ ученика и вернуть вердикт с метаданными для мониторинга."""
    with observe_verify("student_answer"):
        result = verifier.verify_student_answer(statement, student_answer)

    if result.is_correct:
        return GradeResult(
            is_correct=True,
            feedback="Верно.",
            verify_status=result.status,
            feedback_source="correct",
        )

    if result.status == "wrong_root_count" and result.true_roots is not None:
        return GradeResult(
            is_correct=False,
            feedback=_wrong_root_count_feedback(result.true_roots),
            verify_status=result.status,
            feedback_source="template_wrong_root_count",
        )

    correct_answer = _true_answer(statement, declared_answer)
    prompt = (
        f"Задание: {statement}\n"
        f"Правильный ответ: {correct_answer}\n"
        f"Ответ ученика: {student_answer}\n"
        "Объясни ошибку ученика."
    )

    llm_started = time.perf_counter()
    try:
        feedback = llm.complete(FEEDBACK_SYSTEM, prompt).strip()
    except Exception:
        record_llm_call(
            provider=llm_provider,
            outcome="error",
            duration_seconds=(time.perf_counter() - llm_started),
        )
        raise

    if not feedback:
        llm_outcome = "empty"
        feedback = f"{_DEFAULT_WRONG_FEEDBACK} Правильный ответ: {correct_answer}."
        feedback_source: FeedbackSource = "default_fallback"
    else:
        llm_outcome = "success"
        feedback_source = "llm"

    llm_duration_ms = int((time.perf_counter() - llm_started) * 1000)
    record_llm_call(
        provider=llm_provider,
        outcome=llm_outcome,
        duration_seconds=llm_duration_ms / 1000,
    )

    return GradeResult(
        is_correct=False,
        feedback=feedback,
        verify_status=result.status,
        feedback_source=feedback_source,
        llm_duration_ms=llm_duration_ms,
    )
