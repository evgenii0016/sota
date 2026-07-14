"""ИИ-помощник во время решения задания 13."""

from __future__ import annotations

import re
import time

from app.llm import LLM
from app.metrics import record_llm_call, record_task13_assistant
from app.task13.models import Task13AssistantRequest

ASSISTANT_EVENT = "task13_assistant"

SYSTEM_PROMPT = (
    "Ты — репетитор по тригонометрии (задание 13 ЕГЭ, профильная математика).\n"
    "Ученик решает задачу; тебе даны только условие, его вопрос, черновик решения "
    "и история диалога.\n"
    "Тебе НЕ известны правильные серии корней и ответ на отрезке.\n\n"
    "Можно:\n"
    "- объяснять теорию (формулы приведения, ОДЗ, свойства функций);\n"
    "- задавать наводящие вопросы («какие ограничения на x?»);\n"
    "- указать тип ошибки без готового исправления.\n\n"
    "Нельзя:\n"
    "- называть следующий конкретный шаг («сделайте замену t = sin x» и т.п.);\n"
    "- давать числовой ответ, серии корней или конкретные значения x;\n"
    "- рисовать или описывать окружность с отмеченными корнями.\n\n"
    "Ответь кратко (1–3 предложения), доброжелательно, на русском."
)

ASSISTANT_SYSTEM = SYSTEM_PROMPT

_STRENGTHENED_SUFFIX = (
    "\n\nКРИТИЧНО: не называй корни, серии с параметром k/n, конкретные углы "
    "(π/6, −π/2 и т.д.) и следующий шаг решения. Только теория или наводящий вопрос."
)

_DEFAULT_REPLY = (
    "Подумайте, какие преобразования уравнения уже допустимы на этом этапе "
    "и что нужно проверить, прежде чем записывать ответ."
)

_REFUSAL_REPLY = (
    "Я не могу подсказать готовый шаг или записать серии корней. "
    "Попробуйте сформулировать, на каком этапе вы застряли — "
    "и что уже проверили в своём черновике."
)

_ROOT_SERIES_RE = re.compile(
    r"x\s*=.*(?:2\s*\\?pi|2π).*[knm]\b|"
    r"[-+]?\s*(?:\\?pi|π)/?\d*\s*\+\s*2\s*(?:\\?pi|π)\s*[knm]",
    re.IGNORECASE,
)
_NEXT_STEP_RE = re.compile(
    r"(?:следующ(?:ий|его)\s+(?:шаг|этап))|"
    r"(?:сделайте|сделай|выполните|используйте|замените)\s+(?:замену|substitution)|"
    r"(?:замен(?:а|ите)\s+t\s*=)|"
    r"t\s*=\s*sin\s*x|t\s*=\s*cos\s*x",
    re.IGNORECASE,
)
_SPECIFIC_ROOT_RE = re.compile(
    r"(?:[-−]\s*)?(?:\\?pi|π)\s*/\s*(?:6|4|3|2)\b|"
    r"(?:[-−]\s*)?(?:\\?pi|π)\s*/\s*2\b|"
    r"(?:[-−]\s*)?(?:\\?pi|π)\b(?!\s*[+/])",
    re.IGNORECASE,
)
_NUMERIC_ANSWER_RE = re.compile(
    r"(?:ответ|корн(?:и|ей)|решени[ея]).{0,40}(?:[-−]?\d|π|pi/)|"
    r"(?:^|\s)(?:[-−]?\d+(?:\.\d+)?)\s*(?:;|$)",
    re.IGNORECASE,
)
_CIRCLE_ROOTS_RE = re.compile(
    r"(?:окружност|единичн(?:ой|ую)\s+окружност|отмет(?:ь|ить)\s+(?:на\s+)?окружност)",
    re.IGNORECASE,
)


def _build_prompt(statement: str, request: Task13AssistantRequest) -> str:
    draft = request.draft_solution
    parts = [f"Условие:\n{statement}\n"]

    if request.history:
        parts.append("История диалога:")
        for item in request.history:
            speaker = "Ученик" if item.role == "user" else "Помощник"
            parts.append(f"{speaker}: {item.text}")
        parts.append("")

    parts.extend(
        [
            f"Черновик пункта а:\n{draft.part_a or '(пусто)'}\n",
            f"Черновик пункта б:\n{draft.part_b or '(пусто)'}\n",
            f"Вопрос ученика:\n{request.message}",
        ]
    )
    return "\n".join(parts)


def _sanitize_reply(reply: str) -> tuple[str, bool]:
    text = reply.strip()
    if not text:
        return _DEFAULT_REPLY, False

    blocked = any(
        pattern.search(text)
        for pattern in (
            _ROOT_SERIES_RE,
            _NEXT_STEP_RE,
            _SPECIFIC_ROOT_RE,
            _NUMERIC_ANSWER_RE,
            _CIRCLE_ROOTS_RE,
        )
    )
    if blocked:
        return _REFUSAL_REPLY, True
    return text, False


class FakeAssistantLLM:
    """Детерминированная заглушка помощника для тестов."""

    def ask(self, statement: str, request: Task13AssistantRequest) -> str:
        message = request.message.lower()
        if any(
            word in message for word in ("дай ответ", "напиши ответ", "какой ответ", "скажи ответ")
        ):
            return (
                "Я не могу назвать готовый ответ — это часть вашей самостоятельной работы. "
                "Опишите, какие преобразования вы уже сделали и где возникло затруднение."
            )
        if "логар" in message and ("одз" in message or "област" in message):
            return (
                "Для логарифма аргумент должен быть строго положительным. "
                "Какие значения x вы бы исключили из рассмотрения?"
            )
        if "одз" in message or "област" in message:
            return (
                "Подумайте: при каких значениях x выражения в уравнении перестают быть определены?"
            )
        if "отбор" in message or "отрез" in message:
            return "Как вы обычно проверяете, какие значения параметра попадают в заданный отрезок?"
        if "сер" in message:
            return "Как вы записываете общий вид корней с целочисленным параметром?"
        return _DEFAULT_REPLY


def _complete_assistant(
    llm: LLM,
    *,
    statement: str,
    request: Task13AssistantRequest,
    retry: bool = False,
) -> tuple[str, bool]:
    system = SYSTEM_PROMPT + (_STRENGTHENED_SUFFIX if retry else "")
    raw = llm.complete(system, _build_prompt(statement, request))
    reply, blocked = _sanitize_reply(raw)
    if blocked:
        return reply, True
    if not reply:
        return _DEFAULT_REPLY, False
    return reply, False


def ask_assistant(
    llm: LLM | FakeAssistantLLM,
    *,
    statement: str,
    request: Task13AssistantRequest,
    llm_provider: str = "fake",
) -> str:
    """Получить ответ помощника без передачи эталона."""
    if isinstance(llm, FakeAssistantLLM) or hasattr(llm, "ask"):
        raw = llm.ask(statement, request)  # type: ignore[union-attr]
        reply, _ = _sanitize_reply(raw)
        record_task13_assistant(outcome="success")
        return reply

    started = time.perf_counter()
    try:
        reply, blocked = _complete_assistant(
            llm,
            statement=statement,
            request=request,
        )
        outcome = "success"
        if blocked:
            reply, still_blocked = _complete_assistant(
                llm,
                statement=statement,
                request=request,
                retry=True,
            )
            outcome = "filtered" if still_blocked else "success"
            if still_blocked:
                reply = _REFUSAL_REPLY
    except Exception:
        record_llm_call(
            provider=llm_provider,
            outcome="error",
            duration_seconds=time.perf_counter() - started,
        )
        record_task13_assistant(outcome="error")
        raise

    record_llm_call(
        provider=llm_provider,
        outcome=outcome,
        duration_seconds=time.perf_counter() - started,
    )
    record_task13_assistant(outcome=outcome)
    return reply
