"""Тесты выбора LLM-провайдера"""

from __future__ import annotations

import pytest

from app.llm import FakeLLM, GigaChatLLM, get_llm


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
