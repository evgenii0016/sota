"""Разбор ответа ученика по заданию 13."""

from __future__ import annotations

import re
from dataclasses import dataclass

import sympy as sp

from app.task13.trig import RootSeries, angle_to_storage

_PI = sp.pi

_DECIMAL_APPROX_RE = re.compile(r"≈|~\s*\d|(?<![\w.])(?:\d+\.\d+|\.\d+)(?![\w.])")
_PARAM_MARKER_RE = re.compile(
    r"(?P<param>[a-z])\s*(?:∈|in|∊|belongs\s+to|\\in)\s*(?:Z|ℤ)"
    r"|(?P<param_ru>[a-z])\s*(?:—|-)\s*цел(?:ое|ые)?",
    re.IGNORECASE,
)
_X_EQUALS_RE = re.compile(r"x\s*=\s*(.+)", re.IGNORECASE)
_SET_BRACES_RE = re.compile(r"^\s*\{(.+)\}\s*$")


class ParseError(ValueError):
    """Ошибка разбора ответа ученика."""


class DecimalApproximationError(ParseError):
    """Десятичное приближение вместо точного значения."""


@dataclass(frozen=True)
class ParsedSeries:
    offset: sp.Expr
    period: sp.Expr
    param: str | None
    raw: str
    has_integer_param: bool


@dataclass(frozen=True)
class ParsedSeriesResult:
    series: list[ParsedSeries]
    errors: list[str]


@dataclass(frozen=True)
class ParsedRootsResult:
    roots: list[str]
    errors: list[str]


def normalize_math_text(text: str) -> str:
    """Привести π/pi/\\pi и типографику к единому виду."""
    normalized = text.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    normalized = normalized.replace(r"\left", "").replace(r"\right", "")
    normalized = normalized.replace(r"\cdot", "*").replace(r"\times", "*")
    normalized = normalized.replace(r"\mathbb{Z}", "ℤ")

    fraction_pattern = re.compile(r"\\(?:d?frac)\s*\{([^{}]+)\}\s*\{([^{}]+)\}")
    while fraction_pattern.search(normalized):
        normalized = fraction_pattern.sub(r"(\1)/(\2)", normalized)

    normalized = normalized.replace("\\pi", "pi").replace("π", "pi")
    normalized = normalized.replace("·", "*").replace("×", "*").replace("²", "^2")
    normalized = normalized.replace("^{", "^").replace("}", "")
    normalized = normalized.replace("{", "").replace("}", "")
    normalized = re.sub(r"(\d)\s*pi", r"\1*pi", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"pi\s*([a-z])", r"pi*\1", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(\d)\s*([a-z])", r"\1*\2", normalized, flags=re.IGNORECASE)
    return normalized.strip()


def _reject_decimal_approximation(text: str) -> None:
    if _DECIMAL_APPROX_RE.search(text):
        raise DecimalApproximationError("нужно точное значение")


def _sympify_angle(text: str) -> sp.Expr:
    cleaned = normalize_math_text(text)
    cleaned = cleaned.replace("^2", "**2")
    cleaned = re.sub(r"\s+", "", cleaned)
    cleaned = cleaned.rstrip(",").strip()
    if "," in cleaned:
        cleaned = cleaned.split(",", 1)[0]
    return sp.nsimplify(sp.sympify(cleaned, locals={"pi": _PI}), [_PI])


def _split_series_lines(text: str) -> list[str]:
    chunks = re.split(r"[;\n]+", text)
    lines: list[str] = []
    for chunk in chunks:
        piece = chunk.strip()
        if not piece:
            continue
        if re.search(r"x\s*=", piece, re.IGNORECASE):
            lines.append(piece)
    return lines


def _parse_series_line(line: str) -> ParsedSeries:
    normalized = normalize_math_text(line)
    param_match = _PARAM_MARKER_RE.search(normalized)
    param = None
    has_integer_param = False
    if param_match:
        param = (param_match.group("param") or param_match.group("param_ru")).lower()
        has_integer_param = True

    x_match = _X_EQUALS_RE.search(normalized)
    if not x_match:
        raise ParseError(f"не найдена запись серии: {line!r}")

    body = x_match.group(1).strip()
    if param_match:
        body = normalized[: param_match.start()]
        body = _X_EQUALS_RE.search(body)
        if not body:
            raise ParseError(f"не найдена запись серии: {line!r}")
        body = body.group(1).strip()

    if param:
        body = re.sub(
            rf"\*?\s*{re.escape(param)}\s*,?\s*$",
            "",
            body,
            flags=re.IGNORECASE,
        ).strip()

    if "+" not in body:
        raise ParseError(f"ожидался вид offset + period·param: {line!r}")

    offset_text, period_text = body.rsplit("+", 1)
    offset = _sympify_angle(offset_text)
    period = _sympify_angle(period_text)

    return ParsedSeries(
        offset=offset,
        period=period,
        param=param,
        raw=line.strip(),
        has_integer_param=has_integer_param,
    )


def parse_series_from_solution(text: str) -> ParsedSeriesResult:
    """Извлечь серии корней из развёрнутого решения пункта а."""
    _reject_decimal_approximation(text)
    errors: list[str] = []
    series: list[ParsedSeries] = []

    for line in _split_series_lines(text):
        try:
            parsed = _parse_series_line(line)
        except (ParseError, sp.SympifyError, TypeError, ValueError) as exc:
            errors.append(str(exc))
            continue
        if not parsed.has_integer_param:
            errors.append(f"серия без параметра ∈ Z: {line.strip()!r}")
        series.append(parsed)

    if not series and not errors:
        errors.append("не найдено ни одной серии корней вида x = ... + 2πk, k ∈ Z")

    return ParsedSeriesResult(series=series, errors=errors)


def _split_roots_text(text: str) -> list[str]:
    stripped = text.strip()
    set_match = _SET_BRACES_RE.match(stripped)
    if set_match:
        inner = set_match.group(1)
        return [part.strip() for part in re.split(r"[;,]", inner) if part.strip()]

    parts: list[str] = []
    for chunk in re.split(r"[;\n]+", stripped):
        piece = chunk.strip()
        if not piece:
            continue
        if re.search(r"x\s*=", piece, re.IGNORECASE):
            x_match = _X_EQUALS_RE.search(piece)
            if x_match:
                parts.append(x_match.group(1).strip())
            continue
        parts.extend(part.strip() for part in piece.split(",") if part.strip())
    return parts


def parse_roots_from_answer(text: str) -> ParsedRootsResult:
    """Разобрать корни пункта б."""
    _reject_decimal_approximation(text)
    errors: list[str] = []
    roots: list[str] = []

    for part in _split_roots_text(text):
        try:
            value = _sympify_angle(part)
            roots.append(angle_to_storage(value))
        except (ParseError, sp.SympifyError, TypeError, ValueError) as exc:
            errors.append(f"не удалось разобрать корень {part!r}: {exc}")

    if not roots and not errors:
        errors.append("не найдено ни одного корня")

    return ParsedRootsResult(roots=roots, errors=errors)


def parsed_series_to_root_series(parsed: ParsedSeries) -> RootSeries:
    param = parsed.param or "k"
    formula = f"{angle_to_storage(parsed.offset)} + {angle_to_storage(parsed.period)}*{param}"
    return RootSeries(
        offset=parsed.offset,
        period=parsed.period,
        param=param,
        formula=formula,
        display=parsed.raw,
    )
