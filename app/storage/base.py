"""Абстракция хранилища заданий и связанных данных"""

from __future__ import annotations

from typing import Any, Protocol


class TaskRepository(Protocol):
    def save_task(
        self,
        statement: str,
        answer: str,
        task_type: str = "quadratic",
        *,
        metadata: dict[str, Any] | None = None,
    ) -> str: ...

    def get_task(self, task_id: str) -> dict[str, Any] | None: ...

    def count_assistant_uses(self, task_id: str) -> int: ...

    def reserve_assistant_use(self, task_id: str, max_uses: int) -> int | None: ...

    def save_grade_attempt(
        self,
        task_id: str,
        student_answer: str,
        *,
        is_correct: bool,
        feedback: str,
        llm_provider: str | None = None,
        duration_ms: int | None = None,
        score: int | None = None,
        solution_part_a: str | None = None,
        answer_part_b: str | None = None,
        comments: list[dict[str, Any]] | None = None,
        part_a_correct: bool | None = None,
        part_b_correct: bool | None = None,
        justified: bool | None = None,
        justified_part_a: bool | None = None,
        justified_part_b: bool | None = None,
        method_errors: list[str] | None = None,
    ) -> str: ...

    def find_grade_attempt(
        self,
        task_id: str,
        student_answer: str,
        *,
        llm_provider: str | None = None,
    ) -> dict[str, Any] | None: ...

    def list_grade_attempts(self, task_id: str) -> list[dict[str, Any]]: ...

    def get_grade_attempt(self, attempt_id: str) -> dict[str, Any] | None: ...

    def list_events(
        self,
        *,
        task_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]: ...

    def list_examples(
        self,
        *,
        active_only: bool = True,
        include_extended: bool = False,
    ) -> list[dict[str, Any]]: ...

    def get_example(
        self, example_id: str, *, include_extended: bool = False
    ) -> dict[str, str] | None: ...

    def log_event(
        self,
        level: str,
        event: str,
        *,
        task_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None: ...
