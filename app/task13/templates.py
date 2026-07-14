"""Шаблоны тригонометрических уравнений для задания 13."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass

import sympy as sp

from app.task13.models import TemplateFamily

_X = sp.symbols("x")
_SIN_TARGETS = [
    sp.Integer(0),
    sp.Rational(1, 2),
    sp.Rational(-1, 2),
    sp.sqrt(2) / 2,
    -sp.sqrt(2) / 2,
    sp.sqrt(3) / 2,
    -sp.sqrt(3) / 2,
    sp.Integer(1),
    sp.Integer(-1),
]
_COS_TARGETS = list(_SIN_TARGETS)


@dataclass(frozen=True)
class TemplateResult:
    equation: sp.Expr
    template_family: TemplateFamily
    solution_template: str


def _pick_two_targets(rnd: random.Random, values: list[sp.Expr]) -> tuple[sp.Expr, sp.Expr]:
    first, second = rnd.sample(values, 2)
    return first, second


def _quadratic_trig(
    rnd: random.Random,
    *,
    trig_fn: Callable[[sp.Expr], sp.Expr],
    family: TemplateFamily,
    substitution: str,
) -> TemplateResult:
    t1, t2 = _pick_two_targets(rnd, _SIN_TARGETS)
    equation = trig_fn(_X) ** 2 - (t1 + t2) * trig_fn(_X) + t1 * t2
    return TemplateResult(
        equation=sp.expand(equation),
        template_family=family,
        solution_template=(
            f"Замена t = {substitution}. "
            f"Квадратное уравнение t² − ({sp.sstr(t1 + t2)})t + ({sp.sstr(t1 * t2)}) = 0."
        ),
    )


def template_sin_squared(seed: int) -> TemplateResult:
    rnd = random.Random(seed)
    return _quadratic_trig(
        rnd,
        trig_fn=sp.sin,
        family="sin_squared_substitution",
        substitution="sin x",
    )


def template_cos_squared(seed: int) -> TemplateResult:
    rnd = random.Random(seed)
    return _quadratic_trig(
        rnd,
        trig_fn=sp.cos,
        family="cos_squared_substitution",
        substitution="cos x",
    )


def template_sin_cos_product(seed: int) -> TemplateResult:
    rnd = random.Random(seed)
    target = rnd.choice(_COS_TARGETS)
    equation = sp.expand(sp.sin(_X) * (sp.cos(_X) - target))
    return TemplateResult(
        equation=equation,
        template_family="sin_cos_product",
        solution_template=(
            "Разложение: sin x · (cos x − "
            f"{sp.sstr(target)}) = 0 → sin x = 0 или cos x = {sp.sstr(target)}."
        ),
    )


def template_factorization(seed: int) -> TemplateResult:
    rnd = random.Random(seed)
    a, b = _pick_two_targets(rnd, _SIN_TARGETS)
    equation = sp.expand((sp.sin(_X) - a) * (sp.sin(_X) - b))
    return TemplateResult(
        equation=equation,
        template_family="factorization",
        solution_template=(f"Разложение: (sin x − {sp.sstr(a)})(sin x − {sp.sstr(b)}) = 0."),
    )


def template_sin_cos_factorization(seed: int) -> TemplateResult:
    rnd = random.Random(seed)
    sin_target = rnd.choice(_SIN_TARGETS)
    cos_target = rnd.choice(_COS_TARGETS)
    equation = sp.expand((sp.sin(_X) - sin_target) * (sp.cos(_X) - cos_target))
    return TemplateResult(
        equation=equation,
        template_family="factorization",
        solution_template=(
            f"Разложение: (sin x − {sp.sstr(sin_target)})(cos x − {sp.sstr(cos_target)}) = 0."
        ),
    )


def template_double_angle(seed: int) -> TemplateResult:
    rnd = random.Random(seed)
    coefficient = rnd.choice([0, 1, 2, -1, -2])
    equation = sp.expand(sp.sin(2 * _X) - coefficient * sp.sin(_X))
    return TemplateResult(
        equation=equation,
        template_family="double_angle",
        solution_template=(
            f"sin(2x) − {coefficient}·sin x = 0 → 2 sin x cos x − {coefficient} sin x = 0."
        ),
    )


def template_sin2_minus_cos(seed: int) -> TemplateResult:
    rnd = random.Random(seed)
    cos_target = rnd.choice(_COS_TARGETS)
    # 2 sin²x - cos x - 1 = 0 with cos x = t -> 2(1-t²) - t - 1 = 0
    equation = sp.expand(2 * sp.sin(_X) ** 2 - sp.cos(_X) - 1)
    return TemplateResult(
        equation=equation,
        template_family="sin_squared_substitution",
        solution_template=(
            "Замена через sin²x + cos²x = 1 или t = cos x; "
            f"ожидаемые значения cos x включают {sp.sstr(cos_target)}."
        ),
    )


TEMPLATE_BUILDERS: list[Callable[[int], TemplateResult]] = [
    template_sin_squared,
    template_cos_squared,
    template_sin_cos_product,
    template_factorization,
    template_sin_cos_factorization,
    template_double_angle,
    template_sin2_minus_cos,
]


def build_template(seed: int) -> TemplateResult:
    rnd = random.Random(seed)
    builder = rnd.choice(TEMPLATE_BUILDERS)
    return builder(seed + rnd.randint(0, 10_000))
