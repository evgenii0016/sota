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


def grade_answer(llm: LLM, statement: str, declared_answer: str, student_answer: str) -> dict:
    """Проверить ответ ученика и вернуть {is_correct, feedback}."""
    result = verifier.verify_student_answer(statement, student_answer)
    if result.is_correct:
        return {"is_correct": True, "feedback": "Верно."}

    if result.status == "wrong_root_count" and result.true_roots is not None:
        return {
            "is_correct": False,
            "feedback": _wrong_root_count_feedback(result.true_roots),
        }

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
