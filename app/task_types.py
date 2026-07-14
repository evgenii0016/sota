"""Типы заданий и доступ к расширенным примерам"""

from __future__ import annotations

from typing import Literal

from app.config import get_settings

TaskType = Literal["quadratic", "linear", "rational", "task_13"]

STANDARD_TASK_TYPES: frozenset[str] = frozenset({"quadratic"})
EXTENDED_TASK_TYPES: frozenset[str] = frozenset({"linear", "rational"})
TASK_13_TYPES: frozenset[str] = frozenset({"task_13"})
ALL_TASK_TYPES: frozenset[str] = STANDARD_TASK_TYPES | EXTENDED_TASK_TYPES | TASK_13_TYPES


def is_extended_task_type(task_type: str) -> bool:
    return task_type in EXTENDED_TASK_TYPES


def extended_access_granted(key: str | None) -> bool:
    configured = get_settings().extended_examples_key
    if not configured:
        return False
    return key is not None and key == configured
