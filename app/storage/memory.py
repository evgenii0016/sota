"""In-memory хранилище - режим по умолчанию без DATABASE_URL"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from app.task_types import is_extended_task_type


class MemoryRepository:
    def __init__(self) -> None:
        self._tasks: dict[str, dict[str, str]] = {}
        self._examples: dict[str, dict[str, str]] = {}
        self._grade_attempts: list[dict[str, Any]] = []
        self._events: list[dict[str, Any]] = []
        self._next_event_id = 1

    def save_task(self, statement: str, answer: str, task_type: str = "quadratic") -> str:
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = {
            "id": task_id,
            "statement": statement,
            "answer": answer,
            "task_type": task_type,
        }
        return task_id

    def get_task(self, task_id: str) -> dict[str, str] | None:
        return self._tasks.get(task_id)

    def save_grade_attempt(
        self,
        task_id: str,
        student_answer: str,
        *,
        is_correct: bool,
        feedback: str,
        llm_provider: str | None = None,
        duration_ms: int | None = None,
    ) -> str:
        attempt_id = str(uuid.uuid4())
        self._grade_attempts.append(
            {
                "id": attempt_id,
                "task_id": task_id,
                "student_answer": student_answer,
                "is_correct": is_correct,
                "feedback": feedback,
                "llm_provider": llm_provider,
                "duration_ms": duration_ms,
                "created_at": datetime.now(UTC),
            }
        )
        return attempt_id

    def find_grade_attempt(
        self,
        task_id: str,
        student_answer: str,
        *,
        llm_provider: str | None = None,
    ) -> dict[str, Any] | None:
        matches = [
            item
            for item in self._grade_attempts
            if item["task_id"] == task_id
            and item["student_answer"] == student_answer
            and item.get("llm_provider") == llm_provider
        ]
        if not matches:
            return None
        return dict(max(matches, key=lambda item: item["created_at"]))

    def list_grade_attempts(self, task_id: str) -> list[dict[str, Any]]:
        attempts = [item for item in self._grade_attempts if item["task_id"] == task_id]
        return sorted(attempts, key=lambda item: item["created_at"])

    def get_grade_attempt(self, attempt_id: str) -> dict[str, Any] | None:
        for item in self._grade_attempts:
            if item["id"] == attempt_id:
                return dict(item)
        return None

    def list_events(
        self,
        *,
        task_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        items = self._events
        if task_id is not None:
            items = [item for item in items if item.get("task_id") == task_id]
        items = sorted(items, key=lambda item: item["created_at"], reverse=True)
        return [dict(item) for item in items[:limit]]

    def list_examples(
        self,
        *,
        active_only: bool = True,
        include_extended: bool = False,
    ) -> list[dict[str, Any]]:
        items = list(self._examples.values())
        if active_only:
            items = [item for item in items if item.get("is_active", True)]
        if not include_extended:
            items = [item for item in items if not is_extended_task_type(item["task_type"])]
        return [
            {
                "id": item["id"],
                "name": item["name"],
                "task_type": item["task_type"],
                "statement": item["statement"],
                "tags": item.get("tags", []),
            }
            for item in items
        ]

    def get_example(
        self, example_id: str, *, include_extended: bool = False
    ) -> dict[str, str] | None:
        example = self._examples.get(example_id)
        if example is None:
            return None
        if not example.get("is_active", True):
            return None
        if not include_extended and is_extended_task_type(example["task_type"]):
            return None
        return example

    def register_example(
        self,
        *,
        example_id: str,
        name: str,
        statement: str,
        answer: str,
        task_type: str = "quadratic",
        tags: list[str] | None = None,
        is_active: bool = True,
    ) -> None:
        self._examples[example_id] = {
            "id": example_id,
            "name": name,
            "statement": statement,
            "answer": answer,
            "task_type": task_type,
            "tags": tags or [],
            "is_active": is_active,
        }

    def log_event(
        self,
        level: str,
        event: str,
        *,
        task_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self._events.append(
            {
                "id": self._next_event_id,
                "level": level,
                "event": event,
                "task_id": task_id,
                "payload": payload or {},
                "created_at": datetime.now(UTC),
            }
        )
        self._next_event_id += 1
