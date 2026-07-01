"""Проверка свободного ответа ученика."""

from __future__ import annotations

from app import verifier
from app.llm import LLM

FEEDBACK_SYSTEM = (
    "Ты - репетитор по математике. Ученик уже получил оценку «неверно». "
    "Кратко и доброжелательно объясни, в чём ошибка и как правильно записать ответ. "
    "Не выноси вердикт - только пояснение. Ответь одним абзацем текста."
)

_DEFAULT_WRONG_FEEDBACK = (
    "Ответ неверен. Проверьте вычисления и запишите все корни через ';' в порядке возрастания."
)


def _true_answer(statement: str, fallback: str) -> str:
    try:
        return ";".join(verifier.solve_from_statement(statement))
    except (ValueError, Exception):
        return fallback


def grade_answer(llm: LLM, statement: str, declared_answer: str, student_answer: str) -> dict:
    """Проверить ответ ученика и вернуть {is_correct, feedback}."""
    is_correct = verifier.verify_task(statement, student_answer)
    if is_correct:
        return {"is_correct": True, "feedback": "Верно."}

    correct_answer = _true_answer(statement, declared_answer)
    prompt = (
        f"Задание: {statement}\n"
        f"Правильный ответ: {correct_answer}\n"
        f"Ответ ученика: {student_answer}\n"
        "Объясни ошибку ученика."
    )
    feedback = llm.complete(FEEDBACK_SYSTEM, prompt).strip()
    if not feedback:
        feedback = f"{_DEFAULT_WRONG_FEEDBACK} Правильный ответ: {correct_answer}."

    return {"is_correct": False, "feedback": feedback}
