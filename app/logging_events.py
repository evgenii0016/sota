"""Структурные события приложения в хранилище"""

from __future__ import annotations

from typing import Any

from app.storage.factory import get_repository


def log_event(
    level: str,
    event: str,
    *,
    task_id: str | None = None,
    **payload: Any,
) -> None:
    get_repository().log_event(level, event, task_id=task_id, payload=payload or None)
