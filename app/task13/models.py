"""Pydantic-схемы задания 13 ЕГЭ."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_DECIMAL_APPROX_RE = re.compile(r"≈|~\s*\d|(?<![\w.])(?:\d+\.\d+|\.\d+)(?![\w.])")

CommentSection = Literal["одз", "преобразование", "серии", "отбор", "ответ_б", "общее"]
TemplateFamily = Literal[
    "sin_squared_substitution",
    "cos_squared_substitution",
    "sin_cos_product",
    "factorization",
    "double_angle",
]
IntervalType = Literal["closed", "open_left", "open_right", "open"]
Task13Score = Literal[0, 1, 2]


class Task13Equation(BaseModel):
    latex: str
    sympy: str


class Task13Interval(BaseModel):
    left: str
    right: str
    type: IntervalType
    display: str | None = None


class Task13RootSeries(BaseModel):
    formula: str
    param: str
    display: str | None = None


class Task13PartA(BaseModel):
    series: list[Task13RootSeries]


class Task13PartB(BaseModel):
    roots: list[str]


class Task13Metadata(BaseModel):
    """Внутреннее представление задания 13 (эталон, не отдаётся API)."""

    equation: Task13Equation
    interval: Task13Interval
    part_a: Task13PartA
    part_b: Task13PartB
    template_family: TemplateFamily
    solution_template: str | None = None
    odz_required: bool = False


class Task13CirclePoint(BaseModel):
    angle: str


class Task13CircleArc(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_angle: str = Field(alias="from")
    to: str


class Task13CircleDiagram(BaseModel):
    points: list[Task13CirclePoint] = []
    arcs: list[Task13CircleArc] = []


class Task13View(BaseModel):
    """Условие для ученика (без эталона)."""

    id: str
    task_type: Literal["task_13"] = "task_13"
    statement: str
    part_a_prompt: str
    part_b_prompt: str
    interval_display: str | None = None
    equation_latex: str | None = None


class Task13BatchResponse(BaseModel):
    tasks: list[Task13View] = Field(..., min_length=1, max_length=10)


class Task13GradeRequest(BaseModel):
    solution_part_a: str = Field(
        ...,
        min_length=1,
        max_length=16000,
        description="Развёрнутое решение пункта а",
    )
    answer_part_b: str = Field(
        ...,
        min_length=0,
        max_length=512,
        description="Корни на отрезке через ';' (может быть пустым, если пункт б не выполнен)",
    )
    circle_diagram: Task13CircleDiagram | None = None

    @field_validator("solution_part_a", "answer_part_b", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("solution_part_a", "answer_part_b")
    @classmethod
    def reject_decimal_approximation(cls, value: str) -> str:
        if _DECIMAL_APPROX_RE.search(value):
            raise ValueError("нужно точное значение")
        return value


class Task13Comment(BaseModel):
    section: CommentSection
    ok: bool
    text: str | None = None


class Task13GradeResponse(BaseModel):
    score: Literal[0, 1, 2]
    part_a_correct: bool
    part_b_correct: bool
    justified: bool
    comments: list[Task13Comment]
    justified_part_a: bool | None = None
    justified_part_b: bool | None = None
    method_errors: list[str] = []
    attempt_id: str | None = None


class Task13DraftSolution(BaseModel):
    part_a: str = ""
    part_b: str = ""

    @field_validator("part_a", "part_b", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class Task13AssistantMessage(BaseModel):
    role: Literal["user", "assistant"]
    text: str = Field(..., min_length=1, max_length=4000)

    @field_validator("text", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class Task13AssistantRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    draft_solution: Task13DraftSolution = Field(default_factory=Task13DraftSolution)
    history: list[Task13AssistantMessage] = Field(default_factory=list, max_length=20)

    @field_validator("message", mode="before")
    @classmethod
    def strip_message(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class Task13AssistantResponse(BaseModel):
    reply: str
    uses_left: int = Field(..., ge=0)
