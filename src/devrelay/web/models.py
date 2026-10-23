"""Request models and the stable HTTP envelope."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

WEB_SCHEMA_VERSION = 1

#: Hard request-body cap.  The API only accepts small JSON control documents.
MAX_BODY_BYTES = 64 * 1024

#: Bounded list windows; larger values are clamped by the route.
MAX_LIST_LIMIT = 100


class SessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    token: str = Field(min_length=1, max_length=512)


class ConfigValidateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    config: dict[str, Any]


class ConfigWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    config: dict[str, Any]
    confirm: Literal["apply"]


class WiringWriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    wiring: dict[str, Any]
    confirm: Literal["apply"]


class RunDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_updated_at: str
    decision: Literal["complete", "request_changes", "stop"]
    confirm: Literal["apply"]


class RunInterruptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["implementer", "reviewer"]
    confirm: Literal["apply"]


class RunHoldRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_updated_at: str
    reason: str = Field(min_length=1, max_length=500)
    confirm: Literal["apply"]

    @field_validator("reason")
    @classmethod
    def _reason_not_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("reason must not be blank")
        return text


class RunHoldReleaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: Literal["apply"]


class RunPromptRecoverRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: Literal["apply"]


class ProjectActivateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirm: Literal["apply"]


class RunPromptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["implementer", "reviewer"]
    prompt: str = Field(min_length=1, max_length=16_000)
    confirm: Literal["apply"]

    @field_validator("prompt")
    @classmethod
    def _prompt_not_blank(cls, value: str) -> str:
        text = value.strip()
        if not text:
            raise ValueError("prompt must not be blank")
        return text


def success(data: Any, *, request_id: str = "") -> dict[str, Any]:
    return {
        "schema_version": WEB_SCHEMA_VERSION,
        "ok": True,
        "data": data,
        "request_id": request_id,
    }


def failure(code: str, message: str, *, request_id: str = "") -> dict[str, Any]:
    return {
        "schema_version": WEB_SCHEMA_VERSION,
        "ok": False,
        "error": {"code": code, "message": message},
        "request_id": request_id,
    }
