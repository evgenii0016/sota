"""FastAPI-сервис: генерация заданий ЕГЭ по математике + проверка ответов."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app import generator, verifier
from app.config import get_settings
from app.grader import grade_answer
from app.llm import get_llm
from app.logging_events import log_event
from app.models import (
    AppEventView,
    ExampleView,
    GradeAttemptView,
    GradeRequest,
    GradeResponse,
    TaskView,
)
from app.storage.factory import get_repository, init_repository, reset_repository

_MAX_GENERATION_ATTEMPTS = 10


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_repository()
    yield
    reset_repository()


app = FastAPI(title="ЕГЭ-математика: генерация + AI-проверка", lifespan=lifespan)

llm = get_llm()
settings = get_settings()


@app.post("/tasks", response_model=TaskView)
def create_task() -> TaskView:
    """Сгенерировать новое задание и вернуть его условие (без ответа)."""
    repo = get_repository()
    for attempt in range(1, _MAX_GENERATION_ATTEMPTS + 1):
        task = generator.generate_quadratic()
        if verifier.verify_task(task.statement, task.answer):
            task_id = repo.save_task(task.statement, task.answer)
            log_event("INFO", "task_created", task_id=task_id, attempt=attempt)
            return TaskView(id=task_id, statement=task.statement)
        log_event(
            "WARNING",
            "generation_failed",
            payload={"attempt": attempt, "task_type": "quadratic"},
        )
    log_event("ERROR", "generation_exhausted", payload={"attempts": _MAX_GENERATION_ATTEMPTS})
    raise HTTPException(status_code=500, detail="Не удалось сгенерировать валидное задание")


@app.post("/tasks/from-example/{example_id}", response_model=TaskView)
def create_task_from_example(example_id: str) -> TaskView:
    """Создать задание из заранее подготовленного примера"""
    repo = get_repository()
    example = repo.get_example(example_id)
    if example is None:
        raise HTTPException(status_code=404, detail="Пример не найден")
    if not verifier.verify_task(example["statement"], example["answer"]):
        raise HTTPException(status_code=500, detail="Пример в хранилище некорректен")
    task_id = repo.save_task(
        example["statement"],
        example["answer"],
        task_type=example.get("task_type", "quadratic"),
    )
    log_event("INFO", "task_created_from_example", task_id=task_id, example_id=example_id)
    return TaskView(id=task_id, statement=example["statement"])


@app.get("/examples", response_model=list[ExampleView])
def list_examples() -> list[ExampleView]:
    """Список демонстрационных примеров (без эталонного ответа)."""
    repo = get_repository()
    return [ExampleView(**item) for item in repo.list_examples()]


@app.post("/tasks/{task_id}/grade", response_model=GradeResponse)
def grade(task_id: str, body: GradeRequest) -> GradeResponse:
    """Проверить ответ ученика по сгенерированному заданию."""
    repo = get_repository()
    task = repo.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Задание не найдено")

    cached = repo.find_grade_attempt(
        task_id,
        body.answer,
        llm_provider=settings.llm_provider,
    )
    if cached is not None:
        repo.save_grade_attempt(
            task_id,
            body.answer,
            is_correct=cached["is_correct"],
            feedback=cached["feedback"],
            llm_provider=settings.llm_provider,
            duration_ms=0,
        )
        log_event(
            "INFO",
            "grade_cached",
            task_id=task_id,
            is_correct=cached["is_correct"],
            llm_provider=settings.llm_provider,
        )
        return GradeResponse(
            is_correct=cached["is_correct"],
            feedback=cached["feedback"],
        )

    started = time.perf_counter()
    result = grade_answer(llm, task["statement"], task["answer"], body.answer)
    duration_ms = int((time.perf_counter() - started) * 1000)

    repo.save_grade_attempt(
        task_id,
        body.answer,
        is_correct=result["is_correct"],
        feedback=result["feedback"],
        llm_provider=settings.llm_provider,
        duration_ms=duration_ms,
    )
    log_event(
        "INFO",
        "grade_completed",
        task_id=task_id,
        is_correct=result["is_correct"],
        llm_provider=settings.llm_provider,
        duration_ms=duration_ms,
    )
    return GradeResponse(**result)


@app.get("/tasks/{task_id}/attempts", response_model=list[GradeAttemptView])
def list_task_attempts(task_id: str) -> list[GradeAttemptView]:
    """История проверок ответов по заданию."""
    repo = get_repository()
    if repo.get_task(task_id) is None:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    return [GradeAttemptView(**item) for item in repo.list_grade_attempts(task_id)]


@app.get("/attempts/{attempt_id}", response_model=GradeAttemptView)
def get_attempt(attempt_id: str) -> GradeAttemptView:
    """Просмотр результата одной проверки."""
    repo = get_repository()
    attempt = repo.get_grade_attempt(attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Результат проверки не найден")
    return GradeAttemptView(**attempt)


@app.get("/events", response_model=list[AppEventView])
def list_events(task_id: str | None = None, limit: int = 100) -> list[AppEventView]:
    """История структурных событий приложения."""
    if limit < 1 or limit > 500:
        raise HTTPException(status_code=400, detail="limit должен быть от 1 до 500")
    repo = get_repository()
    if task_id is not None and repo.get_task(task_id) is None:
        raise HTTPException(status_code=404, detail="Задание не найдено")
    return [AppEventView(**item) for item in repo.list_events(task_id=task_id, limit=limit)]
