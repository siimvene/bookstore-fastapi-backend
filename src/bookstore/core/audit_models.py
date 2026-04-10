"""Structured audit log DTO matching the Spring Boot AuditLog format."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AuditApplication(BaseModel):
    name: str
    extra_info: dict[str, Any] | None = Field(default=None, serialization_alias="extraInfo")


class AuditActivity(BaseModel):
    action: str
    extra_info: dict[str, Any] | None = Field(default=None, serialization_alias="extraInfo")


class AuditActor(BaseModel):
    name: str
    person_code: str | None = Field(default=None, serialization_alias="personCode")


class AuditClient(BaseModel):
    id: str
    source: str = "INTERNAL"
    extra_info: dict[str, Any] | None = Field(default=None, serialization_alias="extraInfo")


class AuditResult(BaseModel):
    code: str
    explanation: str


class AuditLog(BaseModel):
    correlation_id: str = Field(serialization_alias="correlationId")
    time: str
    application: AuditApplication
    activity: AuditActivity
    actor: AuditActor
    client: AuditClient
    result: AuditResult

    def to_log_dict(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True, exclude_none=True)
