"""Структурные JSON-логи в stdout для агрегаторов"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_configured = False


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        event = getattr(record, "event", None)
        if event is not None:
            payload["event"] = event
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            payload.update(extra)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: str = "INFO") -> None:
    global _configured
    if _configured:
        return

    root = logging.getLogger("app")
    root.setLevel(level.upper())
    root.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)
    _configured = True


def log(
    level: str,
    event: str,
    *,
    message: str | None = None,
    **fields: Any,
) -> None:
    """Записать структурное событие в stdout."""
    logger = logging.getLogger("app")
    if not _configured:
        configure_logging()

    log_level = getattr(logging, level.upper(), logging.INFO)
    extra_fields = {"event": event, **fields}
    logger.log(
        log_level,
        message or event,
        extra={"event": event, "extra_fields": extra_fields},
    )
