"""PostgreSQL-хранилище на SQLAlchemy"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.storage.models_db import AppEvent, Example, GradeAttempt, Task


def _parse_uuid(value: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(value)
    except ValueError:
        return None


class PostgresRepository:
    def __init__(self, database_url: str) -> None:
        self._engine: Engine = create_engine(database_url, pool_pre_ping=True)
        self._session_factory = sessionmaker(self._engine, expire_on_commit=False)

    def connect(self) -> None:
        with self._engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def close(self) -> None:
        self._engine.dispose()

    def _session(self) -> Session:
        return self._session_factory()

    def save_task(self, statement: str, answer: str, task_type: str = "quadratic") -> str:
        task = Task(statement=statement, answer=answer, task_type=task_type)
        with self._session() as session:
            session.add(task)
            session.commit()
            session.refresh(task)
            return str(task.id)

    def get_task(self, task_id: str) -> dict[str, str] | None:
        task_uuid = _parse_uuid(task_id)
        if task_uuid is None:
            return None
        with self._session() as session:
            task = session.get(Task, task_uuid)
            if task is None:
                return None
            return {
                "id": str(task.id),
                "statement": task.statement,
                "answer": task.answer,
                "task_type": task.task_type,
            }

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
        attempt = GradeAttempt(
            task_id=uuid.UUID(task_id),
            student_answer=student_answer,
            is_correct=is_correct,
            feedback=feedback,
            llm_provider=llm_provider,
            duration_ms=duration_ms,
        )
        with self._session() as session:
            session.add(attempt)
            session.commit()
            session.refresh(attempt)
            return str(attempt.id)

    def find_grade_attempt(
        self,
        task_id: str,
        student_answer: str,
        *,
        llm_provider: str | None = None,
    ) -> dict[str, Any] | None:
        task_uuid = _parse_uuid(task_id)
        if task_uuid is None:
            return None
        with self._session() as session:
            query = (
                select(GradeAttempt)
                .where(
                    GradeAttempt.task_id == task_uuid,
                    GradeAttempt.student_answer == student_answer,
                    GradeAttempt.llm_provider == llm_provider,
                )
                .order_by(GradeAttempt.created_at.desc())
                .limit(1)
            )
            attempt = session.scalars(query).first()
            if attempt is None:
                return None
            return self._grade_attempt_to_dict(attempt)

    def list_grade_attempts(self, task_id: str) -> list[dict[str, Any]]:
        task_uuid = _parse_uuid(task_id)
        if task_uuid is None:
            return []
        with self._session() as session:
            query = (
                select(GradeAttempt)
                .where(GradeAttempt.task_id == task_uuid)
                .order_by(GradeAttempt.created_at)
            )
            attempts = session.scalars(query).all()
            return [self._grade_attempt_to_dict(attempt) for attempt in attempts]

    def get_grade_attempt(self, attempt_id: str) -> dict[str, Any] | None:
        attempt_uuid = _parse_uuid(attempt_id)
        if attempt_uuid is None:
            return None
        with self._session() as session:
            attempt = session.get(GradeAttempt, attempt_uuid)
            if attempt is None:
                return None
            return self._grade_attempt_to_dict(attempt)

    def list_events(
        self,
        *,
        task_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        with self._session() as session:
            query = select(AppEvent).order_by(AppEvent.created_at.desc()).limit(limit)
            if task_id is not None:
                event_task_uuid = _parse_uuid(task_id)
                if event_task_uuid is None:
                    return []
                query = query.where(AppEvent.task_id == event_task_uuid)
            events = session.scalars(query).all()
            return [self._event_to_dict(event) for event in events]

    @staticmethod
    def _grade_attempt_to_dict(attempt: GradeAttempt) -> dict[str, Any]:
        return {
            "id": str(attempt.id),
            "task_id": str(attempt.task_id),
            "student_answer": attempt.student_answer,
            "is_correct": attempt.is_correct,
            "feedback": attempt.feedback,
            "llm_provider": attempt.llm_provider,
            "duration_ms": attempt.duration_ms,
            "created_at": attempt.created_at,
        }

    @staticmethod
    def _event_to_dict(event: AppEvent) -> dict[str, Any]:
        return {
            "id": event.id,
            "level": event.level,
            "event": event.event,
            "task_id": str(event.task_id) if event.task_id else None,
            "payload": dict(event.payload),
            "created_at": event.created_at,
        }

    def list_examples(self, *, active_only: bool = True) -> list[dict[str, Any]]:
        with self._session() as session:
            query = select(Example)
            if active_only:
                query = query.where(Example.is_active.is_(True))
            query = query.order_by(Example.created_at)
            examples = session.scalars(query).all()
            return [
                {
                    "id": str(example.id),
                    "name": example.name,
                    "task_type": example.task_type,
                    "statement": example.statement,
                    "tags": list(example.tags),
                }
                for example in examples
            ]

    def get_example(self, example_id: str) -> dict[str, str] | None:
        example_uuid = _parse_uuid(example_id)
        if example_uuid is None:
            return None
        with self._session() as session:
            example = session.get(Example, example_uuid)
            if example is None or not example.is_active:
                return None
            return {
                "id": str(example.id),
                "name": example.name,
                "statement": example.statement,
                "answer": example.answer,
                "task_type": example.task_type,
            }

    def log_event(
        self,
        level: str,
        event: str,
        *,
        task_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        event_row = AppEvent(
            level=level,
            event=event,
            task_id=uuid.UUID(task_id) if task_id else None,
            payload=payload or {},
        )
        with self._session() as session:
            session.add(event_row)
            session.commit()
