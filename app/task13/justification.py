"""LLM-оценка обоснованности решения задания 13."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from app.llm import LLM
from app.metrics import record_llm_call
from app.task13.models import CommentSection

SectionName = Literal["одз", "преобразование", "серии", "отбор"]

_VALID_SECTIONS: frozenset[SectionName] = frozenset({"одз", "преобразование", "серии", "отбор"})
_SECTION_ALIASES: dict[str, SectionName] = {
    "одз": "одз",
    "область определения": "одз",
    "преобразование": "преобразование",
    "преобразования": "преобразование",
    "серии": "серии",
    "серия": "серии",
    "отбор": "отбор",
}


class JustificationSection(BaseModel):
    name: SectionName
    ok: bool
    comment: str = ""


class JustificationResult(BaseModel):
    justified: bool
    justified_part_a: bool
    justified_part_b: bool
    method_errors: list[str] = Field(default_factory=list)
    sections: list[JustificationSection] = Field(default_factory=list)
    odz_issue_affects_answer: bool = False


JUSTIFICATION_SYSTEM = (
    "Ты — эксперт по проверке задания 13 ЕГЭ (профильная математика).\n"
    "Тебе даны условие, решение ученика и результаты символьной проверки SymPy "
    "(part_a_correct, part_b_correct).\n"
    "НЕ пересчитывай серии корней и корни на отрезке. НЕ ставь числовой балл 0/1/2.\n"
    "Верни только JSON без markdown:\n"
    "{\n"
    '  "justified": bool,\n'
    '  "justified_part_a": bool,\n'
    '  "justified_part_b": bool,\n'
    '  "method_errors": ["..."],\n'
    '  "sections": [\n'
    '    {"name": "одз", "ok": bool, "comment": "..."},\n'
    '    {"name": "преобразование", "ok": bool, "comment": "..."},\n'
    '    {"name": "серии", "ok": bool, "comment": "..."},\n'
    '    {"name": "отбор", "ok": bool, "comment": "..."}\n'
    "  ],\n"
    '  "odz_issue_affects_answer": bool\n'
    "}\n"
    "Поле sections[].name — строго одно слово из списка: одз, преобразование, серии, отбор. "
    "Не используй символ | и не объединяй несколько имён в одной строке.\n"
    "Критерии: голый ответ без выкладок → justified=false; "
    "деление на sin/cos без разбора 0 → method_errors; "
    "отбор без граничных k → замечание в sections; "
    "чистая тригонометрия без ОДЗ — допустимо."
)

_BARE_ANSWER_RE = re.compile(r"^\s*(x\s*=|[{\-]?\s*pi|[{\-]?\s*\\?pi)", re.IGNORECASE)
_DIVIDE_TRIG_RE = re.compile(
    r"дел(им|ение|я)\s+на\s+(sin|cos)\s*x|/(sin|cos)\s*\(?\s*x\s*\)?",
    re.IGNORECASE,
)
_WORK_MARKERS_RE = re.compile(
    r"замен|пусть|t\s*=|разлож|преобраз|получаем|следовательно"
    r"|→|->|систем|уравнен|(?:sin|cos|tg|ctg)\s*\(?\s*x",
    re.IGNORECASE,
)
_SELECTION_MARKERS_RE = re.compile(
    r"отбор|отрез|интервал|принадлеж|границ|k\s*=|n\s*=|m\s*=|перебор|подстав",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class JustificationInput:
    statement: str
    solution_part_a: str
    answer_part_b: str
    part_a_correct: bool
    part_b_correct: bool


def _extract_json(text: str) -> dict:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    return json.loads(stripped)


def _normalize_section_name(raw: object) -> SectionName | None:
    if not isinstance(raw, str):
        return None
    name = raw.strip().lower()
    if name in _VALID_SECTIONS:
        return name  # type: ignore[return-value]
    if name in _SECTION_ALIASES:
        return _SECTION_ALIASES[name]
    for key, value in (
        ("преобраз", "преобразование"),
        ("сери", "серии"),
        ("отбор", "отбор"),
        ("одз", "одз"),
    ):
        if key in name:
            return value
    return None


def _normalize_section_item(item: object) -> list[dict[str, object]]:
    if not isinstance(item, dict):
        return []
    ok = bool(item.get("ok", False))
    comment = item.get("comment", "")
    if not isinstance(comment, str):
        comment = str(comment) if comment is not None else ""

    raw_name = item.get("name", "")
    if isinstance(raw_name, str) and "|" in raw_name:
        names = [_normalize_section_name(part) for part in raw_name.split("|")]
    else:
        names = [_normalize_section_name(raw_name)]

    return [{"name": name, "ok": ok, "comment": comment} for name in names if name is not None]


def _normalize_llm_payload(payload: dict) -> dict:
    normalized = dict(payload)
    raw_sections = payload.get("sections", [])
    if not isinstance(raw_sections, list):
        raw_sections = []

    sections: list[dict[str, object]] = []
    seen: set[SectionName] = set()
    for item in raw_sections:
        for section in _normalize_section_item(item):
            name = section["name"]
            assert isinstance(name, str)
            if name in seen:
                continue
            seen.add(name)  # type: ignore[arg-type]
            sections.append(section)

    normalized["sections"] = sections
    return normalized


def _merge_section_comments(
    heuristic: list[JustificationSection],
    llm_sections: list[JustificationSection],
) -> list[JustificationSection]:
    """Дополнить отсутствующие у LLM секции эвристическим fallback."""
    llm_by_name = {section.name: section for section in llm_sections}
    merged: list[JustificationSection] = []
    for base in heuristic:
        llm_section = llm_by_name.get(base.name)
        merged.append(llm_section or base)
    for section in llm_sections:
        if section.name not in {item.name for item in merged}:
            merged.append(section)
    return merged


def _combine_with_heuristics(
    heuristic: JustificationResult,
    llm_result: JustificationResult,
) -> JustificationResult:
    """Использовать LLM для обоснованности, эвристики — только как fallback секций."""
    return JustificationResult(
        justified=llm_result.justified,
        justified_part_a=llm_result.justified_part_a,
        justified_part_b=llm_result.justified_part_b,
        method_errors=llm_result.method_errors,
        sections=_merge_section_comments(heuristic.sections, llm_result.sections),
        odz_issue_affects_answer=llm_result.odz_issue_affects_answer,
    )


def _has_substantive_work(text: str) -> bool:
    normalized = text.strip()
    if len(normalized) < 40:
        return False
    if _SELECTION_MARKERS_RE.search(normalized):
        return True
    if _BARE_ANSWER_RE.match(normalized) and not _WORK_MARKERS_RE.search(normalized):
        return False
    return bool(_WORK_MARKERS_RE.search(normalized))


def _has_selection_work(solution_part_a: str, answer_part_b: str) -> bool:
    combined = f"{solution_part_a}\n{answer_part_b}"
    if _SELECTION_MARKERS_RE.search(combined):
        return True
    return len(answer_part_b.strip()) > 0 and _has_substantive_work(solution_part_a)


class FakeJustificationLLM:
    """Детерминированная заглушка для тестов: JSON по эвристикам, без сети."""

    def evaluate(self, data: JustificationInput) -> JustificationResult:
        method_errors: list[str] = []
        if _DIVIDE_TRIG_RE.search(data.solution_part_a):
            method_errors.append("деление на sin x / cos x без разбора случая = 0")

        work_a = _has_substantive_work(data.solution_part_a)
        selection_b = _has_selection_work(data.solution_part_a, data.answer_part_b)

        justified_part_a = work_a and not method_errors
        justified_part_b = selection_b and not method_errors
        justified = justified_part_a and (justified_part_b or not data.answer_part_b.strip())

        sections = [
            JustificationSection(
                name="преобразование",
                ok=work_a,
                comment="Есть преобразования уравнения."
                if work_a
                else "Недостаточно выкладок в пункте а.",
            ),
            JustificationSection(
                name="серии",
                ok=data.part_a_correct and work_a,
                comment="Серии записаны с обоснованием."
                if data.part_a_correct and work_a
                else "Проверьте полноту серий и параметр ∈ ℤ.",
            ),
            JustificationSection(
                name="отбор",
                ok=selection_b,
                comment="Отбор на отрезке описан."
                if selection_b
                else "Покажите граничные значения параметра на отрезке.",
            ),
        ]

        return JustificationResult(
            justified=justified,
            justified_part_a=justified_part_a,
            justified_part_b=justified_part_b,
            method_errors=method_errors,
            sections=sections,
        )


def evaluate_justification(
    llm: LLM | FakeJustificationLLM,
    data: JustificationInput,
    *,
    llm_provider: str = "fake",
) -> JustificationResult:
    """Запросить обоснованность у LLM или детерминированной заглушки."""
    if isinstance(llm, FakeJustificationLLM) or hasattr(llm, "evaluate"):
        return llm.evaluate(data)  # type: ignore[union-attr]

    heuristic = FakeJustificationLLM().evaluate(data)
    prompt = (
        f"Условие:\n{data.statement}\n\n"
        f"Решение пункта а:\n{data.solution_part_a}\n\n"
        f"Ответ пункта б:\n{data.answer_part_b}\n\n"
        f"part_a_correct={data.part_a_correct}\n"
        f"part_b_correct={data.part_b_correct}\n"
    )

    started = time.perf_counter()
    try:
        raw = llm.complete(JUSTIFICATION_SYSTEM, prompt)
        payload = _normalize_llm_payload(_extract_json(raw))
        llm_result = JustificationResult.model_validate(payload)
        result = _combine_with_heuristics(heuristic, llm_result)
        outcome = "success"
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError):
        duration = time.perf_counter() - started
        record_llm_call(provider=llm_provider, outcome="fallback", duration_seconds=duration)
        return heuristic
    except Exception:
        record_llm_call(
            provider=llm_provider,
            outcome="error",
            duration_seconds=time.perf_counter() - started,
        )
        raise

    record_llm_call(
        provider=llm_provider,
        outcome=outcome,
        duration_seconds=time.perf_counter() - started,
    )
    return result


def section_to_comment_section(name: SectionName) -> CommentSection:
    return name  # type: ignore[return-value]
