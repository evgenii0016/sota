#!/usr/bin/env python3
"""Автогенерация «испорченных» решений для регрессии task_13.

1. Сгенерировать задание 13
2. Взять solution_template и серии из metadata
3. Применить порчу
4. Прогнать grade_task13 и сохранить в tests/fixtures/task13/generated/
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.task13.generator import generate_task13  # noqa: E402
from app.task13.grader import grade_task13  # noqa: E402
from app.task13.justification import FakeJustificationLLM  # noqa: E402
from app.task13.models import Task13GradeRequest, Task13Metadata  # noqa: E402

OUTPUT_DIR = ROOT / "tests" / "fixtures" / "task13" / "generated"
TARGET_COUNT = 12


def _series_lines(metadata: dict) -> list[str]:
    lines: list[str] = []
    for item in metadata["part_a"]["series"]:
        display = item.get("display")
        if display:
            lines.append(display.replace("∈ ℤ", "∈ Z"))
            continue
        param = item["param"]
        lines.append(f"x = {item['formula'].replace(f'*{param}', f'π{param}')}, {param} ∈ Z")
    return lines


def _full_solution(task) -> tuple[str, str]:
    series = _series_lines(task.metadata)
    part_a = task.metadata.get("solution_template", "Решение уравнения.") + "\n"
    part_a += "\n".join(series)
    part_a += f"\nОтбор на отрезке {task.interval_display}."
    part_b = ";".join(task.part_b)
    return part_a, part_b


def _remove_series(text: str) -> str:
    lines = [line for line in text.splitlines() if "x =" not in line or "∈" not in line]
    kept = [line for line in text.splitlines() if line.strip().startswith("x =")]
    if len(kept) > 1:
        kept = kept[1:]
    body = "\n".join(lines + kept)
    return body


def _flip_sign_in_series(text: str) -> str:
    return text.replace("pi/6", "-pi/6").replace("π/6", "-π/6")


def _remove_selection(text: str) -> str:
    return re.sub(r"Отбор.*", "", text, flags=re.DOTALL).strip()


def _bare_answer(task) -> tuple[str, str]:
    series = _series_lines(task.metadata)
    return "\n".join(series[:2]), ";".join(task.part_b)


def _divide_sin(text: str) -> str:
    return "Делим на sin x без разбора случая sin x = 0.\n" + text


def _drop_root(answer: str) -> str:
    parts = [part.strip() for part in answer.split(";") if part.strip()]
    if len(parts) <= 1:
        return answer
    return ";".join(parts[1:])


CORRUPTIONS = [
    ("remove_series", lambda task, sol_a, sol_b: (_remove_series(sol_a), sol_b)),
    ("flip_sign", lambda task, sol_a, sol_b: (_flip_sign_in_series(sol_a), sol_b)),
    ("remove_selection", lambda task, sol_a, sol_b: (_remove_selection(sol_a), sol_b)),
    ("bare_answer", lambda task, sol_a, sol_b: _bare_answer(task)),
    ("divide_sin", lambda task, sol_a, sol_b: (_divide_sin(sol_a), sol_b)),
    ("drop_root", lambda task, sol_a, sol_b: (sol_a, _drop_root(sol_b))),
]


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    llm = FakeJustificationLLM()
    written = 0
    seed = 1000

    while written < TARGET_COUNT:
        task = generate_task13(seed=seed)
        seed += 1
        sol_a, sol_b = _full_solution(task)
        metadata = Task13Metadata.model_validate(task.metadata)

        for corruption_name, corrupt_fn in CORRUPTIONS:
            if written >= TARGET_COUNT:
                break
            corrupted_a, corrupted_b = corrupt_fn(task, sol_a, sol_b)
            request = Task13GradeRequest(
                solution_part_a=corrupted_a,
                answer_part_b=corrupted_b,
            )
            result = grade_task13(
                llm,
                metadata,
                task.statement,
                request,
            )
            payload = {
                "name": f"seed{seed - 1}_{corruption_name}",
                "corruption": corruption_name,
                "generator_seed": seed - 1,
                "expected_score": result.response.score,
                "actual_part_a_correct": result.response.part_a_correct,
                "actual_part_b_correct": result.response.part_b_correct,
                "statement": task.statement,
                "metadata": task.metadata,
                "solution_part_a": corrupted_a,
                "answer_part_b": corrupted_b,
            }
            out_path = OUTPUT_DIR / f"{payload['name']}.json"
            out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            written += 1

    print(f"Saved {written} fixtures to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
