"""Абстракция LLM-провайдера + детерминированная заглушка.

Реальный провайдер (OpenAI / Anthropic / Gemini / любой) подключается по интерфейсу
`LLM`. По умолчанию используется `FakeLLM`, чтобы сервис и тесты работали офлайн,
без сетевых вызовов и API-ключей.
Подключен GigaChat API.
"""

from __future__ import annotations

import os
from typing import Protocol

from dotenv import load_dotenv


class LLM(Protocol):
    """Минимальный контракт LLM-провайдера."""

    def complete(self, system: str, prompt: str) -> str: ...


class FakeLLM:
    """Заглушка для офлайн-разработки.

    ВАЖНО: эта «модель» не умеет считать математику. Она имитирует уверенный, но
    ненадёжный ответ настоящей LLM - всегда говорит, что ответ верный. Это
    специально: так видно, что вердикт LLM нельзя использовать как источник истины.
    """

    def complete(self, system: str, prompt: str) -> str:
        # Ненадёжная «уверенность» - вердикт grader берёт из verifier, не из LLM
        return "Ответ выглядит правильным."


class GigaChatLLM:
    """Провайдер GigaChat API"""

    def complete(self, system: str, prompt: str) -> str:
        from gigachat import GigaChat
        from gigachat.models import Chat, Messages, MessagesRole

        chat = Chat(
            messages=[
                Messages(role=MessagesRole.SYSTEM, content=system),
                Messages(role=MessagesRole.USER, content=prompt),
            ],
        )
        with GigaChat() as client:
            response = client.chat(chat)

        if not response.choices:
            raise RuntimeError("GigaChat вернул пустой список choices")

        content = response.choices[0].message.content.strip()
        if not content:
            raise RuntimeError("GigaChat вернул пустой ответ")
        return content


def get_llm() -> LLM:
    """Вернуть LLM-провайдер по переменной окружения LLM_PROVIDER"""
    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "fake").strip().lower()
    if provider == "gigachat":
        return GigaChatLLM()
    if provider != "fake":
        raise ValueError(f"Неизвестный LLM_PROVIDER: {provider!r}. Допустимо: fake, gigachat")
    return FakeLLM()
