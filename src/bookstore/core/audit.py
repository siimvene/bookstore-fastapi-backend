"""Structured audit logging matching the Spring Boot AuditLogger format.

Reads request_id, client_ip, and user_id from structlog contextvars automatically.
Backward-compatible static API — no changes needed at call sites.
"""

from datetime import UTC, datetime
from functools import lru_cache
from typing import Any
from uuid import UUID

import structlog

from bookstore.config.settings import get_settings
from bookstore.core.audit_models import (
    AuditActivity,
    AuditActor,
    AuditApplication,
    AuditClient,
    AuditLog,
    AuditResult,
)

RESULT_SUCCESS = "SUCCESS"


@lru_cache
def _get_audit_logger() -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(get_settings().audit_logger_name)


def _now_iso() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _get_context() -> dict[str, str]:
    """Read request-scoped values from structlog contextvars."""
    ctx = structlog.contextvars.get_contextvars()
    return {
        "request_id": ctx.get("request_id", ""),
        "client_ip": ctx.get("client_ip", "unknown"),
        "user_id": ctx.get("user_id", "system"),
    }


def _build_audit_log(
    action: str,
    extra_info: dict[str, Any] | None = None,
    user: str | None = None,
) -> AuditLog:
    settings = get_settings()
    ctx = _get_context()

    return AuditLog(
        correlation_id=ctx["request_id"],
        time=_now_iso(),
        application=AuditApplication(
            name=settings.app_name,
            extra_info={"environment": settings.environment},
        ),
        activity=AuditActivity(action=action, extra_info=extra_info),
        actor=AuditActor(name=user or ctx["user_id"]),
        client=AuditClient(
            id=settings.audit_client_id,
            source="INTERNAL",
            extra_info={"sourceIp": ctx["client_ip"]},
        ),
        result=AuditResult(
            code=RESULT_SUCCESS,
            explanation="Operation completed successfully",
        ),
    )


class AuditLogger:
    @staticmethod
    def log_create(
        resource: str, resource_id: UUID, data: dict[str, Any], user: str = "system"
    ) -> None:
        audit = _build_audit_log(
            action=f"{resource.upper()}_CREATED",
            extra_info={"id": str(resource_id), **data},
            user=user if user != "system" else None,
        )
        _get_audit_logger().info("audit_event", audit_data=audit.to_log_dict())

    @staticmethod
    def log_update(
        resource: str,
        resource_id: UUID,
        old_data: dict[str, Any],
        new_data: dict[str, Any],
        user: str = "system",
    ) -> None:
        audit = _build_audit_log(
            action=f"{resource.upper()}_UPDATED",
            extra_info={"id": str(resource_id), "old": old_data, "new": new_data},
            user=user if user != "system" else None,
        )
        _get_audit_logger().info("audit_event", audit_data=audit.to_log_dict())

    @staticmethod
    def log_delete(resource: str, resource_id: UUID, user: str = "system") -> None:
        audit = _build_audit_log(
            action=f"{resource.upper()}_DELETED",
            extra_info={"id": str(resource_id)},
            user=user if user != "system" else None,
        )
        _get_audit_logger().info("audit_event", audit_data=audit.to_log_dict())

    @staticmethod
    def log_read(resource: str, resource_id: UUID | str, user: str = "system") -> None:
        audit = _build_audit_log(
            action=f"{resource.upper()}_ACCESSED",
            extra_info={"id": str(resource_id)},
            user=user if user != "system" else None,
        )
        _get_audit_logger().info("audit_event", audit_data=audit.to_log_dict())
