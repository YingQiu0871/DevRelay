"""Request models and the stable HTTP envelope."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

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
