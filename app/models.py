"""Pydantic-схемы API"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.task13.models import Task13Comment
from app.validation import validate_student_answer


class TaskView(BaseModel):
    id: str
    statement: str
    # эталонный ответ ученику НЕ отдаём


class GradeRequest(BaseModel):
    answer: str = Field(
        ...,
        min_length=1,
        description="Корни уравнения через ';', например: 2;3",
        examples=["2;3"],
    )

    @field_validator("answer", mode="before")
    @classmethod
    def strip_answer(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("answer")
    @classmethod
    def check_answer_format(cls, value: str) -> str:
        return validate_student_answer(value)


class GradeResponse(BaseModel):
    is_correct: bool
    feedback: str


class ExampleView(BaseModel):
    id: str
    name: str
    task_type: str
    statement: str
    tags: list[str] = []


class GradeAttemptView(BaseModel):
    id: str
    task_id: str
    student_answer: str
    is_correct: bool
    feedback: str
    llm_provider: str | None = None
    duration_ms: int | None = None
    created_at: datetime | None = None
    score: Literal[0, 1, 2] | None = None
    solution_part_a: str | None = None
    answer_part_b: str | None = None
    comments: list[Task13Comment] | None = None
    part_a_correct: bool | None = None
    part_b_correct: bool | None = None
    justified: bool | None = None
    justified_part_a: bool | None = None
    justified_part_b: bool | None = None
    method_errors: list[str] | None = None


class AppEventView(BaseModel):
    id: int
    level: str
    event: str
    task_id: str | None = None
    payload: dict[str, Any] = {}
    created_at: datetime | None = None
