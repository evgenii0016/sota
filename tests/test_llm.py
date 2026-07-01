"""Тесты выбора LLM-провайдера и политики GigaChat"""

from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.llm import (
    FakeLLM,
    GigaChatLLM,
    GigaChatPolicy,
    RateLimiter,
    get_llm,
)


def test_get_llm_defaults_to_fake(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "fake")
    assert isinstance(get_llm(), FakeLLM)


def test_get_llm_gigachat(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gigachat")
    assert isinstance(get_llm(), GigaChatLLM)


def test_get_llm_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unknown")
    with pytest.raises(ValueError, match="Неизвестный LLM_PROVIDER"):
        get_llm()


def test_gigachat_policy_from_env(monkeypatch):
    monkeypatch.setenv("GIGACHAT_TIMEOUT", "45")
    monkeypatch.setenv("GIGACHAT_MAX_RETRIES", "5")
    monkeypatch.setenv("GIGACHAT_RETRY_BACKOFF_FACTOR", "1.5")
    monkeypatch.setenv("GIGACHAT_RATE_LIMIT_REQUESTS", "10")
    monkeypatch.setenv("GIGACHAT_RATE_LIMIT_PERIOD_SEC", "30")

    policy = GigaChatPolicy.from_env()

    assert policy.timeout == 45.0
    assert policy.max_retries == 5
    assert policy.retry_backoff_factor == 1.5
    assert policy.rate_limit_requests == 10
    assert policy.rate_limit_period_sec == 30.0


def test_rate_limiter_blocks_when_window_is_full():
    limiter = RateLimiter(max_requests=2, period_sec=0.2)
    limiter.acquire()
    limiter.acquire()

    started = time.monotonic()
    limiter.acquire()
    elapsed = time.monotonic() - started

    assert elapsed >= 0.15


def test_rate_limiter_allows_burst_up_to_limit():
    limiter = RateLimiter(max_requests=2, period_sec=1.0)

    started = time.monotonic()
    limiter.acquire()
    limiter.acquire()
    elapsed = time.monotonic() - started

    assert elapsed < 0.1


@patch("gigachat.GigaChat")
def test_gigachat_llm_applies_policy_and_rate_limit(mock_gigachat_cls):
    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.chat.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="  пояснение  "))],
    )
    mock_gigachat_cls.return_value = mock_client

    policy = GigaChatPolicy(
        timeout=42.0,
        max_retries=4,
        retry_backoff_factor=2.0,
        rate_limit_requests=0,
    )
    llm = GigaChatLLM(policy=policy)

    assert llm.complete("system", "prompt") == "пояснение"
    mock_gigachat_cls.assert_called_once_with(
        timeout=42.0,
        max_retries=4,
        retry_backoff_factor=2.0,
    )
    mock_client.chat.assert_called_once()
