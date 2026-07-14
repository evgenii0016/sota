"""SymPy-утилиты для генерации и проверки задания 13."""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

import sympy as sp

_X = sp.symbols("x")
_PI = sp.pi
_TABULAR_VALUES = {
    sp.Integer(0),
    sp.Rational(1, 2),
    sp.Rational(-1, 2),
    sp.sqrt(2) / 2,
    -sp.sqrt(2) / 2,
    sp.sqrt(3) / 2,
    -sp.sqrt(3) / 2,
    sp.Integer(1),
    sp.Integer(-1),
}

_PARAM_NAMES = "knmlopqrstuvw"


@dataclass(frozen=True)
class RootSeries:
    offset: sp.Expr
    period: sp.Expr
    param: str
    formula: str
    display: str

    def values_in(
        self, left: sp.Expr, right: sp.Expr, *, k_range: range | None = None
    ) -> set[sp.Expr]:
        values: set[sp.Expr] = set()
        if k_range is None:
            if self.period == 0:
                if left <= self.offset <= right:
                    values.add(sp.nsimplify(self.offset, [_PI]))
                return values
            try:
                k_min = int(sp.ceiling((left - self.offset) / self.period)) - 1
                k_max = int(sp.floor((right - self.offset) / self.period)) + 1
            except (TypeError, ValueError):
                k_min, k_max = -20, 20
            k_range = range(k_min, k_max + 1)
        for k in k_range:
            value = sp.nsimplify(self.offset + self.period * k, [_PI])
            if not value.is_real:
                continue
            if left <= value <= right:
                values.add(value)
        return values

    def to_dict(self) -> dict[str, str]:
        return {
            "formula": self.formula,
            "param": self.param,
            "display": self.display,
        }


def parse_equation(sympy_text: str) -> sp.Expr:
    local_dict = {"sin": sp.sin, "cos": sp.cos, "pi": _PI, "x": _X}
    expr = sp.sympify(sympy_text, locals=local_dict)
    if expr.has(_X):
        return expr
    raise ValueError(f"выражение не содержит x: {sympy_text!r}")


def expr_to_sympy_text(expr: sp.Expr) -> str:
    return sp.sstr(expr)


def angle_to_storage(expr: sp.Expr) -> str:
    simplified = sp.nsimplify(expr, [_PI])
    text = sp.sstr(simplified)
    text = text.replace("**", "^")
    return text


def angle_to_display(expr: sp.Expr) -> str:
    text = angle_to_storage(expr)
    text = text.replace("*pi", "π").replace("pi", "π")
    text = text.replace("-π", "−π")
    return text


def is_tabular_value(value: sp.Expr) -> bool:
    simplified = sp.nsimplify(value)
    return any(sp.simplify(simplified - candidate) == 0 for candidate in _TABULAR_VALUES)


def is_tabular_angle(angle: sp.Expr) -> bool:
    simplified = sp.nsimplify(angle, [_PI])
    sin_value = sp.simplify(sp.sin(simplified))
    cos_value = sp.simplify(sp.cos(simplified))
    return is_tabular_value(sin_value) or is_tabular_value(cos_value)


def _parse_linear_lambda(lam: sp.Lambda) -> tuple[sp.Expr, sp.Expr]:
    variable = lam.variables[0]
    expr = sp.expand(lam.expr)
    period = sp.nsimplify(expr.coeff(variable), [_PI])
    offset = sp.nsimplify(expr.subs(variable, 0), [_PI])
    return offset, period


def _series_from_imageset(image_set: sp.ImageSet, param: str) -> RootSeries:
    offset, period = _parse_linear_lambda(image_set.lamda)
    formula = f"{angle_to_storage(offset)} + {angle_to_storage(period)}*{param}"
    display = f"x = {angle_to_display(offset)} + {angle_to_display(period)}{param}, {param} ∈ ℤ"
    return RootSeries(
        offset=offset,
        period=period,
        param=param,
        formula=formula,
        display=display,
    )


def _series_from_finite_root(root: sp.Expr, equation: sp.Expr, param: str) -> RootSeries:
    if not root.is_real:
        raise ValueError("комплексный корень недопустим")
    period = _detect_period(root, equation)
    formula = f"{angle_to_storage(root)} + {angle_to_storage(period)}*{param}"
    display = f"x = {angle_to_display(root)} + {angle_to_display(period)}{param}, {param} ∈ ℤ"
    return RootSeries(
        offset=sp.nsimplify(root, [_PI]),
        period=period,
        param=param,
        formula=formula,
        display=display,
    )


def _detect_period(root: sp.Expr, equation: sp.Expr) -> sp.Expr:
    for period in (_PI, 2 * _PI):
        if sp.simplify(equation.subs(_X, root + period)) == 0:
            return period
    return 2 * _PI


def _flatten_solutions(solution_set: sp.Set) -> list[sp.Basic]:
    if isinstance(solution_set, sp.Union):
        return list(solution_set.args)
    if isinstance(solution_set, sp.ImageSet):
        return [solution_set]
    if isinstance(solution_set, sp.FiniteSet):
        return list(solution_set.args)
    if solution_set in (sp.S.Reals, sp.EmptySet):
        return []
    raise ValueError(f"неподдерживаемый тип множества решений: {type(solution_set)}")


def _sample_values(series: RootSeries, *, left: sp.Expr, right: sp.Expr) -> set[sp.Expr]:
    return series.values_in(left, right)


def merge_equivalent_series(series_list: list[RootSeries]) -> list[RootSeries]:
    if not series_list:
        return []

    left = -4 * _PI
    right = 4 * _PI
    grouped: list[tuple[RootSeries, set[sp.Expr]]] = []
    for series in series_list:
        samples = _sample_values(series, left=left, right=right)
        merged = False
        for index, (existing, existing_samples) in enumerate(grouped):
            if samples & existing_samples:
                grouped[index] = (existing, existing_samples | samples)
                merged = True
                break
        if not merged:
            grouped.append((series, samples))

    canonical: list[RootSeries] = []
    for index, (series, _) in enumerate(grouped):
        param = series.param or _PARAM_NAMES[index % len(_PARAM_NAMES)]
        formula = f"{angle_to_storage(series.offset)} + {angle_to_storage(series.period)}*{param}"
        canonical.append(
            RootSeries(
                offset=series.offset,
                period=series.period,
                param=param,
                formula=formula,
                display=(
                    f"x = {angle_to_display(series.offset)} + "
                    f"{angle_to_display(series.period)}{param}, {param} ∈ ℤ"
                ),
            )
        )
    return sorted(canonical, key=lambda item: float(sp.N(item.offset)))


def solve_equation_series(equation: sp.Expr) -> list[RootSeries]:
    solution_set = sp.solveset(sp.Eq(equation, 0), _X, sp.S.Reals)
    parts = _flatten_solutions(solution_set)
    if not parts:
        finite = sp.solve(equation, _X)
        if not finite:
            raise ValueError("уравнение не имеет действительных корней")
        parts = finite

    raw_series: list[RootSeries] = []
    for index, part in enumerate(parts):
        param = _PARAM_NAMES[index % len(_PARAM_NAMES)]
        try:
            if isinstance(part, sp.ImageSet):
                raw_series.append(_series_from_imageset(part, param))
            else:
                raw_series.append(_series_from_finite_root(part, equation, param))
        except ValueError:
            continue

    if not raw_series:
        raise ValueError("не удалось построить действительные серии корней")

    merged = merge_equivalent_series(raw_series)
    if not merged:
        raise ValueError("не удалось построить серии корней")
    return merged


def interval_candidates() -> list[sp.Expr]:
    return [sp.nsimplify(n * _PI / 6, [_PI]) for n in range(-24, 25)]


def pick_interval(
    series_list: list[RootSeries],
    *,
    rnd: int | None = None,
    max_attempts: int = 50,
) -> tuple[sp.Expr, sp.Expr, list[sp.Expr]]:
    import random

    generator = random.Random(rnd)
    candidates = interval_candidates()
    left_indices = list(range(len(candidates)))
    right_indices = list(range(len(candidates)))
    generator.shuffle(left_indices)

    attempts = 0
    for left_index in left_indices:
        left = candidates[left_index]
        shuffled_right = right_indices.copy()
        generator.shuffle(shuffled_right)
        for right_index in shuffled_right:
            if attempts >= max_attempts:
                break
            right = candidates[right_index]
            if left >= right:
                continue
            attempts += 1
            roots = roots_on_interval(series_list, left, right)
            if 2 <= len(roots) <= 4:
                return left, right, roots
        if attempts >= max_attempts:
            break

    raise RuntimeError("не удалось подобрать отрезок с 2–4 корнями")


def roots_on_interval(
    series_list: list[RootSeries],
    left: sp.Expr,
    right: sp.Expr,
) -> list[sp.Expr]:
    values: set[sp.Expr] = set()
    for series in series_list:
        values |= series.values_in(left, right)
    return sorted(values, key=lambda value: float(sp.N(value)))


def roots_to_storage(roots: Iterable[sp.Expr]) -> list[str]:
    return [angle_to_storage(root) for root in roots]


def interval_to_storage(left: sp.Expr, right: sp.Expr) -> tuple[str, str, str]:
    left_text = angle_to_storage(left)
    right_text = angle_to_storage(right)
    display = f"[{angle_to_display(left)}; {angle_to_display(right)}]"
    return left_text, right_text, display


def series_sets_match(left: list[RootSeries], right: list[RootSeries]) -> bool:
    probe_left = -4 * _PI
    probe_right = 4 * _PI
    left_values: set[sp.Expr] = set()
    right_values: set[sp.Expr] = set()
    for series in left:
        left_values |= series.values_in(probe_left, probe_right)
    for series in right:
        right_values |= series.values_in(probe_left, probe_right)
    return left_values == right_values


def parse_series_from_metadata(items: list[dict[str, str]]) -> list[RootSeries]:
    parsed: list[RootSeries] = []
    for index, item in enumerate(items):
        formula = item["formula"]
        param = item.get("param") or _PARAM_NAMES[index % len(_PARAM_NAMES)]
        suffix = f"*{param}"
        if not formula.endswith(suffix):
            raise ValueError(f"некорректная формула серии: {formula!r}")
        body = formula[: -len(suffix)]
        if " + " not in body:
            raise ValueError(f"некорректная формула серии: {formula!r}")
        offset_text, period_text = body.rsplit(" + ", 1)
        offset = sp.nsimplify(sp.sympify(offset_text.strip(), locals={"pi": _PI}), [_PI])
        period = sp.nsimplify(sp.sympify(period_text.strip(), locals={"pi": _PI}), [_PI])
        parsed.append(
            RootSeries(
                offset=offset,
                period=period,
                param=param,
                formula=formula,
                display=item.get("display") or formula,
            )
        )
    return parsed


def parse_roots_from_storage(values: Iterable[str]) -> list[sp.Expr]:
    return [sp.nsimplify(sp.sympify(value, locals={"pi": _PI}), [_PI]) for value in values]


def expr_to_latex(equation: sp.Expr) -> str:
    return sp.latex(sp.Eq(equation, 0))


def readable_equation_text(equation: sp.Expr) -> str:
    text = sp.sstr(equation, order="none")
    replacements = (
        ("sin(x)**2", "sin²x"),
        ("cos(x)**2", "cos²x"),
        ("sin(2*x)", "sin(2x)"),
        ("sin(x)", "sin x"),
    )
    for source, target in replacements:
        text = text.replace(source, target)
    text = re.sub(r"cos\(x\)(?!/)", "cos x", text)
    text = re.sub(r"sqrt\((\d+)\)", r"√\1", text)
    text = text.replace("*", "·")
    text = re.sub(r"(?<![√/])(\d)·(?=(?:sin|cos|\d))", r"\1", text)
    return f"{text} = 0"
