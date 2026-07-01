"""Тонкая обёртка над storage для обратной совместимости"""

from __future__ import annotations

from app.storage.factory import get_repository


def save_task(statement: str, answer: str, task_type: str = "quadratic") -> str:
    return get_repository().save_task(statement, answer, task_type)


def get_task(task_id: str) -> dict | None:
    return get_repository().get_task(task_id)
