"""FastAPI-сервис: генерация заданий ЕГЭ по математике + проверка ответов."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from uuid import UUID, uuid4

from fastapi import FastAPI, Header, Query, Request, Response
from starlette.routing import Match

from app import generator, verifier
from app.config import get_settings
from app.errors import AppHTTPException, register_exception_handlers
from app.grader import grade_answer
from app.llm import get_llm
from app.logging_events import log_event
from app.metrics import (
    metrics_payload,
    record_generation_attempt,
    record_grade,
    record_http_request,
)
from app.models import (
    AppEventView,
    ExampleView,
    GradeAttemptView,
    GradeRequest,
    GradeResponse,
    TaskView,
)
from app.storage.factory import get_repository, init_repository, reset_repository
from app.structured_log import configure_logging
from app.structured_log import log as log_stdout
from app.task_types import ALL_TASK_TYPES, extended_access_granted, is_extended_task_type

_MAX_GENERATION_ATTEMPTS = 10
_EXTENDED_KEY_HEADER = "X-Extended-Examples-Key"


def _resolve_extended_access(extended_key: str | None) -> bool:
    return extended_access_granted(extended_key)


def _require_extended_access(extended_key: str | None) -> None:
    if not _resolve_extended_access(extended_key):
        raise AppHTTPException(
            status_code=403,
            code="extended_access_required",
            message="Для этого типа заданий нужен ключ расширенных примеров",
        )


def _generate_task_with_retries(task_type: str) -> generator.GeneratedTask:
    for attempt in range(1, _MAX_GENERATION_ATTEMPTS + 1):
        task = generator.generate_task(task_type)  # type: ignore[arg-type]
        if verifier.verify_task(task.statement, task.answer):
            record_generation_attempt("success")
            return task
        record_generation_attempt("verifier_rejected")
        log_event(
            "WARNING",
            "generation_failed",
            payload={"attempt": attempt, "task_type": task_type},
        )
    record_generation_attempt("exhausted")
    log_event("ERROR", "generation_exhausted", payload={"attempts": _MAX_GENERATION_ATTEMPTS})
    raise AppHTTPException(
        status_code=500,
        code="generation_failed",
        message="Не удалось сгенерировать валидное задание",
    )


def _resolve_route_path(request: Request) -> str:
    for route in request.app.routes:
        match, _ = route.matches(request.scope)
        if match == Match.FULL:
            return getattr(route, "path", request.url.path)
    return request.url.path


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    init_repository()
    log_stdout(
        "INFO",
        "app_started",
        storage="postgres" if settings.uses_postgres else "memory",
        llm_provider=settings.llm_provider,
        metrics_enabled=settings.metrics_enabled,
    )
    yield
    reset_repository()


app = FastAPI(title="ЕГЭ-математика: генерация + AI-проверка", lifespan=lifespan)
register_exception_handlers(app)

llm = get_llm()
settings = get_settings()


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    if request.url.path == "/metrics":
        return await call_next(request)

    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    route_path = _resolve_route_path(request)
    started = time.perf_counter()

    response = await call_next(request)
    duration_seconds = time.perf_counter() - started

    if settings.metrics_enabled:
        record_http_request(
            method=request.method,
            path=route_path,
            status_code=response.status_code,
            duration_seconds=duration_seconds,
        )

    log_stdout(
        "INFO",
        "http_request",
        request_id=request_id,
        method=request.method,
        path=route_path,
        status_code=response.status_code,
        duration_ms=int(duration_seconds * 1000),
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/metrics")
def metrics() -> Response:
    """Prometheus-метрики для мониторинга качества проверки."""
    if not settings.metrics_enabled:
        raise AppHTTPException(
            status_code=404,
            code="metrics_disabled",
            message="Метрики отключены",
        )
    payload, content_type = metrics_payload()
    return Response(content=payload, media_type=content_type)


@app.post("/tasks", response_model=TaskView)
def create_task(
    task_type: str = Query(default="quadratic", description="Тип задания"),
    extended_key: str | None = Header(default=None, alias=_EXTENDED_KEY_HEADER),
) -> TaskView:
    """Сгенерировать новое задание и вернуть его условие (без ответа)."""
    if task_type not in ALL_TASK_TYPES:
        raise AppHTTPException(
            status_code=422,
            code="invalid_task_type",
            message=f"Неизвестный тип задания: {task_type}",
            field="task_type",
        )
    if is_extended_task_type(task_type):
        _require_extended_access(extended_key)

    repo = get_repository()
    task = _generate_task_with_retries(task_type)
    task_id = repo.save_task(task.statement, task.answer, task_type=task.task_type)
    log_event("INFO", "task_created", task_id=task_id)
    return TaskView(id=task_id, statement=task.statement)


@app.post("/tasks/from-example/{example_id}", response_model=TaskView)
def create_task_from_example(
    example_id: UUID,
    extended_key: str | None = Header(default=None, alias=_EXTENDED_KEY_HEADER),
) -> TaskView:
    """Создать задание из заранее подготовленного примера"""
    include_extended = _resolve_extended_access(extended_key)
    repo = get_repository()
    example = repo.get_example(str(example_id), include_extended=include_extended)
    if example is None:
        raise AppHTTPException(
            status_code=404,
            code="example_not_found",
            message="Пример не найден",
        )
    if not verifier.verify_task(example["statement"], example["answer"]):
        raise AppHTTPException(
            status_code=500,
            code="example_invalid",
            message="Пример в хранилище некорректен",
        )
    task_id = repo.save_task(
        example["statement"],
        example["answer"],
        task_type=example.get("task_type", "quadratic"),
    )
    log_event("INFO", "task_created_from_example", task_id=task_id, example_id=str(example_id))
    return TaskView(id=task_id, statement=example["statement"])


@app.get("/examples", response_model=list[ExampleView])
def list_examples(
    extended_key: str | None = Header(default=None, alias=_EXTENDED_KEY_HEADER),
) -> list[ExampleView]:
    """Список демонстрационных примеров (без эталонного ответа)."""
    repo = get_repository()
    include_extended = _resolve_extended_access(extended_key)
    return [ExampleView(**item) for item in repo.list_examples(include_extended=include_extended)]


@app.post("/tasks/{task_id}/grade", response_model=GradeResponse)
def grade(task_id: UUID, body: GradeRequest) -> GradeResponse:
    """Проверить ответ ученика по сгенерированному заданию."""
    repo = get_repository()
    task = repo.get_task(str(task_id))
    if task is None:
        raise AppHTTPException(
            status_code=404,
            code="task_not_found",
            message="Задание не найдено",
        )

    cached = repo.find_grade_attempt(
        str(task_id),
        body.answer,
        llm_provider=settings.llm_provider,
    )
    if cached is not None:
        verify_status = "correct" if cached["is_correct"] else "unknown"
        feedback_source = "correct" if cached["is_correct"] else "cached"
        repo.save_grade_attempt(
            str(task_id),
            body.answer,
            is_correct=cached["is_correct"],
            feedback=cached["feedback"],
            llm_provider=settings.llm_provider,
            duration_ms=0,
        )
        if settings.metrics_enabled:
            record_grade(
                is_correct=cached["is_correct"],
                verify_status=verify_status,
                cached=True,
                llm_provider=settings.llm_provider,
                feedback_source=feedback_source,
                duration_seconds=0.0,
            )
        log_event(
            "INFO",
            "grade_cached",
            task_id=str(task_id),
            is_correct=cached["is_correct"],
            llm_provider=settings.llm_provider,
            verify_status=verify_status,
            feedback_source=feedback_source,
        )
        return GradeResponse(
            is_correct=cached["is_correct"],
            feedback=cached["feedback"],
        )

    started = time.perf_counter()
    result = grade_answer(
        llm,
        task["statement"],
        task["answer"],
        body.answer,
        llm_provider=settings.llm_provider,
    )
    duration_ms = int((time.perf_counter() - started) * 1000)

    repo.save_grade_attempt(
        str(task_id),
        body.answer,
        is_correct=result.is_correct,
        feedback=result.feedback,
        llm_provider=settings.llm_provider,
        duration_ms=duration_ms,
    )
    if settings.metrics_enabled:
        record_grade(
            is_correct=result.is_correct,
            verify_status=result.verify_status,
            cached=False,
            llm_provider=settings.llm_provider,
            feedback_source=result.feedback_source,
            duration_seconds=duration_ms / 1000,
        )
    log_event(
        "INFO",
        "grade_completed",
        task_id=str(task_id),
        is_correct=result.is_correct,
        llm_provider=settings.llm_provider,
        duration_ms=duration_ms,
        verify_status=result.verify_status,
        feedback_source=result.feedback_source,
        llm_duration_ms=result.llm_duration_ms,
        cached=False,
    )
    return GradeResponse(**result.as_api_dict())


@app.get("/tasks/{task_id}/attempts", response_model=list[GradeAttemptView])
def list_task_attempts(task_id: UUID) -> list[GradeAttemptView]:
    """История проверок ответов по заданию."""
    repo = get_repository()
    if repo.get_task(str(task_id)) is None:
        raise AppHTTPException(
            status_code=404,
            code="task_not_found",
            message="Задание не найдено",
        )
    return [GradeAttemptView(**item) for item in repo.list_grade_attempts(str(task_id))]


@app.get("/attempts/{attempt_id}", response_model=GradeAttemptView)
def get_attempt(attempt_id: UUID) -> GradeAttemptView:
    """Просмотр результата одной проверки."""
    repo = get_repository()
    attempt = repo.get_grade_attempt(str(attempt_id))
    if attempt is None:
        raise AppHTTPException(
            status_code=404,
            code="attempt_not_found",
            message="Результат проверки не найден",
        )
    return GradeAttemptView(**attempt)


@app.get("/events", response_model=list[AppEventView])
def list_events(
    task_id: UUID | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AppEventView]:
    """История структурных событий приложения."""
    repo = get_repository()
    task_id_str = str(task_id) if task_id is not None else None
    if task_id_str is not None and repo.get_task(task_id_str) is None:
        raise AppHTTPException(
            status_code=404,
            code="task_not_found",
            message="Задание не найдено",
        )
    return [AppEventView(**item) for item in repo.list_events(task_id=task_id_str, limit=limit)]
