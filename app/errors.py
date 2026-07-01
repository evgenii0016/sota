"""Единый формат ошибок API и обработчики исключений"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str
    field: str | None = None


class AppHTTPException(HTTPException):
    def __init__(
        self,
        status_code: int,
        *,
        code: str,
        message: str,
        field: str | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail=ErrorResponse(code=code, message=message, field=field).model_dump(),
        )


def _validation_message(error: dict[str, Any]) -> tuple[str, str, str | None]:
    error_type = error.get("type", "")
    loc = error.get("loc", ())
    field = str(loc[-1]) if loc and loc[-1] != "body" else None
    ctx = error.get("ctx", {})
    message = error.get("msg", "Некорректные данные запроса")

    if error_type == "missing":
        return "missing_field", "Обязательное поле не заполнено", field
    if error_type == "uuid_parsing":
        return "invalid_id", "Некорректный идентификатор", field
    if error_type == "string_too_short" and field == "answer":
        return "invalid_answer_format", "Укажите хотя бы один корень", field
    if error_type == "value_error":
        ctx_error = ctx.get("error")
        if isinstance(ctx_error, ValueError):
            return "invalid_answer_format", str(ctx_error), field
        if message.startswith("Value error, "):
            message = message.removeprefix("Value error, ")
        return "invalid_answer_format", message, field
    if error_type.startswith("greater_than") or error_type.startswith("less_than"):
        return "invalid_query_param", message, field

    return "validation_error", message, field


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        code, message, field = _validation_message(first)
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(code=code, message=message, field=field).model_dump(),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
            return JSONResponse(status_code=exc.status_code, content=exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                code="http_error",
                message=str(exc.detail),
            ).model_dump(),
        )
