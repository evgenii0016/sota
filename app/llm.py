"""Абстракция LLM-провайдера + детерминированная заглушка.

Реальный провайдер (OpenAI / Anthropic / Gemini / любой) подключается по интерфейсу
`LLM`. По умолчанию используется `FakeLLM`, чтобы сервис и тесты работали офлайн,
без сетевых вызовов и API-ключей.
Подключен GigaChat API.
"""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from dataclasses import dataclass
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


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


@dataclass(frozen=True)
class GigaChatPolicy:
    """Таймаут, повторы и клиентский rate limit для GigaChat"""

    timeout: float = 60.0
    max_retries: int = 3
    retry_backoff_factor: float = 0.5
    rate_limit_requests: int = 0
    rate_limit_period_sec: float = 60.0

    @classmethod
    def from_env(cls) -> GigaChatPolicy:
        return cls(
            timeout=_env_float("GIGACHAT_TIMEOUT", 60.0),
            max_retries=_env_int("GIGACHAT_MAX_RETRIES", 3),
            retry_backoff_factor=_env_float("GIGACHAT_RETRY_BACKOFF_FACTOR", 0.5),
            rate_limit_requests=_env_int("GIGACHAT_RATE_LIMIT_REQUESTS", 0),
            rate_limit_period_sec=_env_float("GIGACHAT_RATE_LIMIT_PERIOD_SEC", 60.0),
        )


class RateLimiter:
    """Скользящее окно: не более N запросов за период. При превышении - ожидание"""

    def __init__(self, max_requests: int, period_sec: float) -> None:
        if max_requests <= 0:
            raise ValueError("max_requests must be positive")
        if period_sec <= 0:
            raise ValueError("period_sec must be positive")
        self._max_requests = max_requests
        self._period_sec = period_sec
        self._timestamps: deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self._lock:
                now = time.monotonic()
                while self._timestamps and self._timestamps[0] <= now - self._period_sec:
                    self._timestamps.popleft()
                if len(self._timestamps) < self._max_requests:
                    self._timestamps.append(now)
                    return
                wait_until = self._timestamps[0] + self._period_sec
            time.sleep(max(wait_until - time.monotonic(), 0.01))


class GigaChatLLM:
    """Провайдер GigaChat API с политикой timeout/retry/rate limit"""

    def __init__(self, policy: GigaChatPolicy | None = None) -> None:
        self._policy = policy or GigaChatPolicy.from_env()
        self._rate_limiter: RateLimiter | None = None
        if self._policy.rate_limit_requests > 0:
            self._rate_limiter = RateLimiter(
                self._policy.rate_limit_requests,
                self._policy.rate_limit_period_sec,
            )

    def complete(self, system: str, prompt: str) -> str:
        from gigachat import GigaChat
        from gigachat.models import Chat, Messages, MessagesRole

        if self._rate_limiter is not None:
            self._rate_limiter.acquire()

        chat = Chat(
            messages=[
                Messages(role=MessagesRole.SYSTEM, content=system),
                Messages(role=MessagesRole.USER, content=prompt),
            ],
        )
        with GigaChat(
            timeout=self._policy.timeout,
            max_retries=self._policy.max_retries,
            retry_backoff_factor=self._policy.retry_backoff_factor,
        ) as client:
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
