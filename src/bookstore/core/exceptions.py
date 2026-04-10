from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from bookstore.config.settings import get_settings

PROBLEM_JSON_MEDIA_TYPE = "application/problem+json"


class ProblemDetail(Exception):
    def __init__(
        self,
        status: int,
        title: str,
        detail: str,
        type_uri: str | None = None,
        instance: str | None = None,
        extra: dict[str, Any] | None = None,
    ):
        self.status = status
        self.title = title
        self.detail = detail
        self.type_uri = type_uri or "about:blank"
        self.instance = instance
        self.extra = extra or {}

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "type": self.type_uri,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
        }
        if self.instance:
            body["instance"] = self.instance
        body.update(self.extra)
        return body


class NotFoundError(ProblemDetail):
    def __init__(self, resource: str, identifier: Any, request: Request | None = None):
        settings = get_settings()
        instance = str(request.url) if request else None
        super().__init__(
            status=404,
            title="Not Found",
            detail=f"{resource} with identifier '{identifier}' not found",
            type_uri=f"{settings.problem_base_uri}/not-found",
            instance=instance,
        )


class ValidationError(ProblemDetail):
    def __init__(self, detail: str, request: Request | None = None):
        settings = get_settings()
        instance = str(request.url) if request else None
        super().__init__(
            status=400,
            title="Validation Error",
            detail=detail,
            type_uri=f"{settings.problem_base_uri}/validation-error",
            instance=instance,
        )


async def problem_detail_handler(_request: Request, exc: ProblemDetail) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status,
        content=exc.to_dict(),
        media_type=PROBLEM_JSON_MEDIA_TYPE,
    )


async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    settings = get_settings()
    errors = exc.errors()
    detail = "; ".join(
        f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in errors
    )
    return JSONResponse(
        status_code=400,
        content={
            "type": f"{settings.problem_base_uri}/validation-error",
            "title": "Validation Error",
            "status": 400,
            "detail": detail,
            "instance": str(request.url),
        },
        media_type=PROBLEM_JSON_MEDIA_TYPE,
    )


async def unhandled_exception_handler(
    _request: Request, _exc: Exception
) -> JSONResponse:
    settings = get_settings()
    return JSONResponse(
        status_code=500,
        content={
            "type": f"{settings.problem_base_uri}/internal-error",
            "title": "Internal Server Error",
            "status": 500,
            "detail": "An unexpected error occurred",
        },
        media_type=PROBLEM_JSON_MEDIA_TYPE,
    )
