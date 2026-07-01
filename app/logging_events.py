"""Структурные события приложения: хранилище + stdout"""

from __future__ import annotations

from typing import Any

from app.storage.factory import get_repository
from app.structured_log import log as log_stdout


def log_event(
    level: str,
    event: str,
    *,
    task_id: str | None = None,
    **payload: Any,
) -> None:
    fields: dict[str, Any] = dict(payload)
    if task_id is not None:
        fields["task_id"] = task_id
    get_repository().log_event(level, event, task_id=task_id, payload=payload or None)
    log_stdout(level, event, **fields)
