"""Prometheus-метрики качества и производительности проверки"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

GRADES_TOTAL = Counter(
    "ege_grader_grades_total",
    "Число запросов на проверку ответа",
    ["is_correct", "verify_status", "cached", "llm_provider", "feedback_source"],
)

GRADE_DURATION_SECONDS = Histogram(
    "ege_grader_grade_duration_seconds",
    "Длительность проверки ответа",
    ["cached", "llm_provider"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
)

LLM_CALLS_TOTAL = Counter(
    "ege_grader_llm_calls_total",
    "Вызовы LLM для пояснения ошибки",
    ["provider", "outcome"],
)

LLM_CALL_DURATION_SECONDS = Histogram(
    "ege_grader_llm_call_duration_seconds",
    "Длительность вызова LLM",
    ["provider"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 120),
)

VERIFY_DURATION_SECONDS = Histogram(
    "ege_grader_verify_duration_seconds",
    "Длительность символьной проверки (sympy)",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1),
)

VALIDATION_ERRORS_TOTAL = Counter(
    "ege_grader_validation_errors_total",
    "Ошибки валидации входных данных",
    ["code"],
)

GENERATION_ATTEMPTS_TOTAL = Counter(
    "ege_grader_generation_attempts_total",
    "Попытки генерации задания",
    ["outcome"],
)

TASK13_GENERATION_SUCCESS_TOTAL = Counter(
    "ege_grader_task13_generation_success_total",
    "Успешная генерация задания 13",
)

TASK13_GENERATION_EXHAUSTED_TOTAL = Counter(
    "ege_grader_task13_generation_exhausted_total",
    "Исчерпаны попытки генерации задания 13",
)

TASK13_ASSISTANT_TOTAL = Counter(
    "ege_grader_task13_assistant_total",
    "Обращения к ИИ-помощнику задания 13",
    ["outcome"],
)

HTTP_REQUESTS_TOTAL = Counter(
    "ege_grader_http_requests_total",
    "HTTP-запросы к API",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "ege_grader_http_request_duration_seconds",
    "Длительность HTTP-запросов",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)


def record_grade(
    *,
    is_correct: bool,
    verify_status: str,
    cached: bool,
    llm_provider: str,
    feedback_source: str,
    duration_seconds: float,
) -> None:
    GRADES_TOTAL.labels(
        is_correct=str(is_correct).lower(),
        verify_status=verify_status,
        cached=str(cached).lower(),
        llm_provider=llm_provider,
        feedback_source=feedback_source,
    ).inc()
    GRADE_DURATION_SECONDS.labels(
        cached=str(cached).lower(),
        llm_provider=llm_provider,
    ).observe(duration_seconds)


def record_llm_call(*, provider: str, outcome: str, duration_seconds: float) -> None:
    LLM_CALLS_TOTAL.labels(provider=provider, outcome=outcome).inc()
    LLM_CALL_DURATION_SECONDS.labels(provider=provider).observe(duration_seconds)


def record_validation_error(code: str) -> None:
    VALIDATION_ERRORS_TOTAL.labels(code=code).inc()


def record_generation_attempt(outcome: str) -> None:
    GENERATION_ATTEMPTS_TOTAL.labels(outcome=outcome).inc()


def record_task13_generation_success() -> None:
    TASK13_GENERATION_SUCCESS_TOTAL.inc()


def record_task13_generation_exhausted() -> None:
    TASK13_GENERATION_EXHAUSTED_TOTAL.inc()


def record_task13_assistant(*, outcome: str) -> None:
    TASK13_ASSISTANT_TOTAL.labels(outcome=outcome).inc()


def record_http_request(
    *,
    method: str,
    path: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        path=path,
        status_code=str(status_code),
    ).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, path=path).observe(duration_seconds)


@contextmanager
def observe_verify(operation: str) -> Iterator[None]:
    started = time.perf_counter()
    try:
        yield
    finally:
        VERIFY_DURATION_SECONDS.labels(operation=operation).observe(time.perf_counter() - started)


def metrics_payload() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
