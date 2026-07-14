"""Unit-тесты помощника задания 13."""

from __future__ import annotations

from app.task13.assistant import (
    SYSTEM_PROMPT,
    FakeAssistantLLM,
    _build_prompt,
    _sanitize_reply,
    ask_assistant,
)
from app.task13.models import Task13AssistantMessage, Task13AssistantRequest, Task13DraftSolution


def test_build_prompt_excludes_reference_answer():
    request = Task13AssistantRequest(
        message="Почему ОДЗ?",
        draft_solution=Task13DraftSolution(part_a="черновик", part_b=""),
    )
    prompt = _build_prompt("а) ... б) ...", request)
    assert "черновик" in prompt
    assert "-pi/2" not in prompt
    assert "metadata" not in prompt


def test_build_prompt_includes_dialog_history():
    request = Task13AssistantRequest(
        message="А если аргумент отрицательный?",
        draft_solution=Task13DraftSolution(part_a="log(...)", part_b=""),
        history=[
            Task13AssistantMessage(role="user", text="Нужно ли проверять ОДЗ?"),
            Task13AssistantMessage(role="assistant", text="Какие ограничения на x вы видите?"),
        ],
    )
    prompt = _build_prompt("а) ... б) ...", request)
    assert "История диалога" in prompt
    assert "Нужно ли проверять ОДЗ?" in prompt
    assert "Какие ограничения на x вы видите?" in prompt


def test_sanitize_reply_blocks_root_series():
    reply, blocked = _sanitize_reply("Запишите x = −π/2 + 2πk, k ∈ Z.")
    assert blocked
    assert "2πk" not in reply
    assert "не могу" in reply.lower()


def test_sanitize_reply_blocks_next_step_hint():
    reply, blocked = _sanitize_reply("Сделайте замену t = sin x.")
    assert blocked
    assert "t = sin" not in reply


def test_sanitize_reply_blocks_specific_root():
    reply, blocked = _sanitize_reply("Один из корней — π/6.")
    assert blocked
    assert "π/6" not in reply


def test_sanitize_reply_blocks_next_step_phrase():
    reply, blocked = _sanitize_reply("Следующий шаг — разложить уравнение на множители.")
    assert blocked
    assert "следующ" not in reply.lower()


def test_fake_assistant_refuses_direct_answer_request():
    reply = ask_assistant(
        FakeAssistantLLM(),
        statement="а) ... б) ...",
        request=Task13AssistantRequest(
            message="Дай ответ на пункт б",
            draft_solution=Task13DraftSolution(),
        ),
    )
    assert "не могу" in reply.lower() or "самостоятель" in reply.lower()
    assert "π" not in reply
    assert "pi" not in reply.lower()
    assert not any(char.isdigit() for char in reply)


def test_fake_assistant_answers_log_odz_question_with_theory_only():
    reply = ask_assistant(
        FakeAssistantLLM(),
        statement="а) ... б) ...",
        request=Task13AssistantRequest(
            message="Объясни ОДЗ для логарифма",
            draft_solution=Task13DraftSolution(),
        ),
    )
    assert "логар" in reply.lower()
    assert "полож" in reply.lower()
    assert "π" not in reply
    assert "x =" not in reply


def test_fake_assistant_answers_odz_question():
    reply = ask_assistant(
        FakeAssistantLLM(),
        statement="а) ... б) ...",
        request=Task13AssistantRequest(
            message="Нужно ли проверять ОДЗ?",
            draft_solution=Task13DraftSolution(),
        ),
    )
    assert "определ" in reply.lower() or "x" in reply.lower()


def test_system_prompt_forbids_next_step_and_roots():
    assert "следующ" in SYSTEM_PROMPT.lower() or "замен" in SYSTEM_PROMPT.lower()
    assert "серии корней" in SYSTEM_PROMPT.lower()
