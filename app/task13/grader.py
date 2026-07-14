"""Единая точка входа для проверки задания 13."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass

from app.llm import LLM
from app.task13.feedback import build_comments
from app.task13.justification import (
    FakeJustificationLLM,
    JustificationInput,
    evaluate_justification,
)
from app.task13.models import Task13GradeRequest, Task13GradeResponse, Task13Metadata
from app.task13.scoring import score
from app.task13.verifier import verify_part_a, verify_part_b


def task13_cache_key(request: Task13GradeRequest) -> str:
    payload = f"{request.solution_part_a}\0{request.answer_part_b}"
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclass(frozen=True)
class Task13GradeResult:
    response: Task13GradeResponse
    cache_key: str
    duration_ms: int


def grade_task13(
    llm: LLM | FakeJustificationLLM,
    metadata: Task13Metadata | dict,
    statement: str,
    request: Task13GradeRequest,
    *,
    llm_provider: str = "fake",
    attempt_id: str | None = None,
) -> Task13GradeResult:
    """Пайплайн: SymPy → LLM → scoring → feedback."""
    if isinstance(metadata, dict):
        metadata = Task13Metadata.model_validate(metadata)

    started = time.perf_counter()

    part_a = verify_part_a(statement, request.solution_part_a, metadata.part_a)
    part_b = verify_part_b(
        metadata.part_b.roots,
        request.answer_part_b,
        metadata.interval,
    )

    justification = evaluate_justification(
        llm,
        JustificationInput(
            statement=statement,
            solution_part_a=request.solution_part_a,
            answer_part_b=request.answer_part_b,
            part_a_correct=part_a.correct,
            part_b_correct=part_b.correct,
        ),
        llm_provider=llm_provider,
    )

    final_score = score(
        part_a_correct=part_a.correct,
        part_b_correct=part_b.correct,
        justified=justification.justified,
        method_errors=justification.method_errors,
        justified_part_a=justification.justified_part_a,
        justified_part_b=justification.justified_part_b,
    )

    comments = build_comments(part_a=part_a, part_b=part_b, justification=justification)

    duration_ms = int((time.perf_counter() - started) * 1000)
    response = Task13GradeResponse(
        score=final_score,
        part_a_correct=part_a.correct,
        part_b_correct=part_b.correct,
        justified=justification.justified,
        justified_part_a=justification.justified_part_a,
        justified_part_b=justification.justified_part_b,
        method_errors=justification.method_errors,
        comments=comments,
        attempt_id=attempt_id,
    )
    return Task13GradeResult(
        response=response,
        cache_key=task13_cache_key(request),
        duration_ms=duration_ms,
    )
