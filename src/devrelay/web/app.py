"""The v0.4-A loopback HTTP control API (Starlette ASGI app)."""

from __future__ import annotations

import json
import secrets
import sys
import threading
from pathlib import Path
from typing import Any, Awaitable, Callable

from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

from devrelay.web.auth import (
    SESSION_HEADER,
    SESSION_TTL_SECONDS,
    AuthManager,
    generate_token,
    validate_host,
    validate_origin,
)
from devrelay.web.errors import WebApiError
from devrelay.web.models import (
    MAX_BODY_BYTES,
    ConfigValidateRequest,
    ConfigWriteRequest,
    ProjectActivateRequest,
    RunDecisionRequest,
    RunInterruptRequest,
    RunPromptRequest,
    SessionRequest,
    WiringWriteRequest,
    failure,
    success,
)
from devrelay.web.registry import ProjectRegistry
from devrelay.web.service import WebReadService
from devrelay.web.workspace import resolve_workspace

STATIC_DIR = Path(__file__).resolve().parent / "static"
_ASSET_TYPES = {
    "app.js": "text/javascript; charset=utf-8",
    "styles.css": "text/css; charset=utf-8",
}


# ---------------------------------------------------------------------------
# response helpers
# ---------------------------------------------------------------------------
def _headers(request: Request) -> dict[str, str]:
    return {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
        "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
        "Cross-Origin-Resource-Policy": "same-origin",
        "X-Request-ID": str(getattr(request.state, "request_id", "")),
    }


def _json(
    request: Request,
    data: dict[str, Any],
    *,
    status_code: int = 200,
    extra_headers: dict[str, str] | None = None,
) -> JSONResponse:
    headers = _headers(request)
    if extra_headers:
        headers.update(extra_headers)
    return JSONResponse(data, status_code=status_code, headers=headers)


def _ui_headers() -> dict[str, str]:
    """CSP for the local UI; API responses keep the stricter default-src none."""
    return {
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "X-Frame-Options": "DENY",
        "Cross-Origin-Resource-Policy": "same-origin",
        "Content-Security-Policy": (
            "default-src 'none'; script-src 'self'; style-src 'self'; "
            "connect-src 'self'; img-src 'self' data:; base-uri 'none'; "
            "form-action 'none'; frame-ancestors 'none'"
        ),
    }


def _static(name: str) -> Response:
    media_type = _ASSET_TYPES.get(name, "text/html; charset=utf-8")
    if name not in _ASSET_TYPES and name != "index.html":
        raise WebApiError("not_found", "asset not found", status_code=404)
    path = STATIC_DIR / name
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise WebApiError("not_found", "asset not found", status_code=404) from exc
    return Response(payload, media_type=media_type, headers=_ui_headers())


def _error_response(
    request: Request,
    error: WebApiError,
) -> JSONResponse:
    body = failure(error.code, error.message, request_id=str(getattr(request.state, "request_id", "")))
    return _json(request, body, status_code=error.status_code, extra_headers=error.headers)


def _request_id(scope: dict[str, Any]) -> str:
    state = scope.setdefault("state", {})
    value = state.get("request_id")
    if not value:
        value = "req_" + secrets.token_hex(8)
        state["request_id"] = value
    return str(value)


# ---------------------------------------------------------------------------
# request body parsing
# ---------------------------------------------------------------------------
async def _read_json(request: Request, model: type[Any]) -> Any:
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        raise WebApiError(
            "unsupported_media_type",
            "Content-Type must be application/json",
            status_code=415,
        )
    raw_length = request.headers.get("content-length")
    if raw_length:
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise WebApiError("invalid_content_length", "invalid Content-Length") from exc
        if length < 0 or length > MAX_BODY_BYTES:
            raise WebApiError("body_too_large", "request body exceeds 64 KiB", status_code=413)
    body = b""
    while True:
        try:
            message = await request.receive()
        except Exception as exc:  # pragma: no cover - transport-level
            raise WebApiError("invalid_body", "request body could not be read") from exc
        if message.get("type") == "http.disconnect":
            raise WebApiError("invalid_body", "client disconnected before the body was complete")
        chunk = message.get("body", b"")
        if len(chunk) > MAX_BODY_BYTES - len(body):
            raise WebApiError("body_too_large", "request body exceeds 64 KiB", status_code=413)
        body += chunk
        if not message.get("more_body", False):
            break
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise WebApiError("invalid_json", "request body is not valid UTF-8 JSON") from exc
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise WebApiError(
            "invalid_request",
            "request does not match the expected schema",
            status_code=422,
        ) from exc


# ---------------------------------------------------------------------------
# security middleware
# ---------------------------------------------------------------------------
class SecurityMiddleware:
    """Host/Origin/auth checks before a route can see the request."""

    def __init__(self, app: Callable[..., Awaitable[None]], *, auth: AuthManager) -> None:
        self.app = app
        self.auth = auth

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] == "websocket":
            # No WebSocket route exists in v0.4-A; fail closed rather than let a
            # future route inherit an unauthenticated handshake.
            await send({"type": "websocket.close", "code": 1008})
            return
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = _request_id(scope)
        request = Request(scope, receive=receive)
        try:
            headers = Headers(scope=scope)
            validate_host(headers.get("host", ""), self.auth.port)
            validate_origin(headers.get("origin"), self.auth.port)
            method = str(scope.get("method", "GET")).upper()
            path = str(scope.get("path", ""))
            scope["state"]["auth"] = self._authenticate(request, method, path)
        except WebApiError as exc:
            await _error_response(request, exc)(scope, receive, send)
            return
        await self.app(scope, receive, send)

    def _authenticate(self, request: Request, method: str, path: str) -> dict[str, Any]:
        if method == "OPTIONS":
            # No CORS negotiation is offered.  Let the router answer 405 rather
            # than turning an unauthenticated preflight into a misleading 401.
            return {"mode": "anonymous"}
        if method in ("GET", "HEAD") and path in ("/", "/ui"):
            return {"mode": "anonymous"}
        if method in ("GET", "HEAD") and path.startswith("/assets/"):
            return {"mode": "anonymous"}
        if path == "/healthz" and method in ("GET", "HEAD"):
            return {"mode": "anonymous"}
        if path == "/api/session" and method == "POST":
            return {"mode": "exchange"}

        authorization = request.headers.get("authorization")
        if authorization and self.auth.bearer_identity(authorization):
            return {"mode": "bearer"}

        session = self.auth.resolve_session(request.headers.get(SESSION_HEADER))
        if session is None:
            raise WebApiError(
                "unauthorized",
                "authentication required",
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"mode": "session", "session": session}


# ---------------------------------------------------------------------------
# API implementation
# ---------------------------------------------------------------------------
class LocalControlApi:
    def __init__(
        self,
        *,
        service: WebReadService,
        registry: ProjectRegistry,
        project_id: str,
        auth: AuthManager,
    ) -> None:
        self.service = service
        self.registry = registry
        self.project_id = project_id
        self.auth = auth
        self._switch_lock = threading.RLock()

    # -- session -----------------------------------------------------
    async def session_create(self, request: Request) -> Response:
        payload: SessionRequest = await _read_json(request, SessionRequest)
        if not self.auth.matches_token(payload.token):
            raise WebApiError(
                "unauthorized",
                "invalid local token",
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
        session = self.auth.create_session()
        return _json(
            request,
            success(
                {
                    "session_token": session.session_id,
                    "expires_in": SESSION_TTL_SECONDS,
                    "transport": "X-DevRelay-Session",
                },
                request_id=str(request.state.request_id),
            ),
        )

    async def session_get(self, request: Request) -> Response:
        identity = request.state.auth
        if identity.get("mode") == "bearer":
            return _json(
                request,
                success(
                    {"authenticated": True, "mode": "bearer"},
                    request_id=str(request.state.request_id),
                ),
            )
        return _json(
            request,
            success(
                {"authenticated": True, "mode": "session"},
                request_id=str(request.state.request_id),
            ),
        )

    async def session_delete(self, request: Request) -> Response:
        identity = request.state.auth
        if identity.get("mode") == "session":
            self.auth.delete_session(identity["session"].session_id)
        return _json(
            request,
            success({"authenticated": False}, request_id=str(request.state.request_id)),
        )

    # -- static UI ---------------------------------------------------
    async def ui_index(self, request: Request) -> Response:
        return _static("index.html")

    async def ui_asset(self, request: Request) -> Response:
        name = str(request.path_params.get("name", ""))
        if name not in _ASSET_TYPES:
            raise WebApiError("not_found", "asset not found", status_code=404)
        return _static(name)

    # -- reads -------------------------------------------------------
    async def healthz(self, request: Request) -> Response:
        return _json(
            request,
            {"ok": True, "schema_version": 1, "request_id": str(request.state.request_id)},
        )

    async def health(self, request: Request) -> Response:
        return _json(
            request,
            success(
                self.service.health(project_id=self.project_id),
                request_id=str(request.state.request_id),
            ),
        )

    async def status(self, request: Request) -> Response:
        return _json(
            request,
            success(self.service.status(), request_id=str(request.state.request_id)),
        )

    async def projects(self, request: Request) -> Response:
        items = [
            project.public(active=project.project_id == self.project_id)
            for project in self.registry.list()
        ]
        return _json(
            request,
            success({"projects": items}, request_id=str(request.state.request_id)),
        )

    async def activate_project(self, request: Request) -> Response:
        if request.headers.get("x-devrelay-confirm") != "apply":
            raise WebApiError(
                "confirmation_required",
                "X-DevRelay-Confirm: apply is required",
                status_code=403,
            )
        payload: ProjectActivateRequest = await _read_json(request, ProjectActivateRequest)
        if payload.confirm != "apply":
            raise WebApiError("confirmation_required", "confirm must be apply", status_code=403)
        project_id = str(request.path_params.get("project_id", ""))
        project = self.registry.get(project_id)
        if not Path(project.root).is_absolute():
            raise WebApiError(
                "invalid_project",
                "registered project root is not absolute",
                status_code=409,
            )
        root, wiring, devrelay_dir = resolve_workspace(project.root)
        # Build outside the lock: holding a thread lock across await can deadlock
        # the single uvicorn event loop.  The swap itself is a no-await critical
        # section; concurrent activations simply last-write-wins.
        service = await run_in_threadpool(
            WebReadService.from_workspace,
            root,
            wiring,
            devrelay_dir,
        )
        with self._switch_lock:
            self.service = service
            self.project_id = project.project_id
        return _json(
            request,
            success(
                {
                    "project": project.public(active=True),
                    "active": True,
                    "restart_required": False,
                },
                request_id=str(request.state.request_id),
            ),
        )

    async def sessions(self, request: Request) -> Response:
        return _json(
            request,
            success(
                self.service.sessions(),
                request_id=str(request.state.request_id),
            ),
        )

    async def runs(self, request: Request) -> Response:
        raw = request.query_params.get("limit", "20")
        try:
            limit = int(raw)
        except ValueError as exc:
            raise WebApiError("invalid_limit", "limit must be an integer") from exc
        if limit < 1 or limit > 100:
            raise WebApiError("invalid_limit", "limit must be between 1 and 100")
        return _json(
            request,
            success(self.service.runs(limit=limit), request_id=str(request.state.request_id)),
        )

    async def run(self, request: Request) -> Response:
        run_id = str(request.path_params.get("run_id", ""))
        return _json(
            request,
            success(self.service.run(run_id), request_id=str(request.state.request_id)),
        )

    async def run_decide(self, request: Request) -> Response:
        if request.headers.get("x-devrelay-confirm") != "apply":
            raise WebApiError(
                "confirmation_required",
                "X-DevRelay-Confirm: apply is required",
                status_code=403,
            )
        payload: RunDecisionRequest = await _read_json(request, RunDecisionRequest)
        run_id = str(request.path_params.get("run_id", ""))
        data = await run_in_threadpool(
            self.service.decide_run,
            run_id,
            payload.decision,
            payload.expected_updated_at,
        )
        return _json(
            request,
            success(data, request_id=str(request.state.request_id)),
        )

    async def run_prompt(self, request: Request) -> Response:
        if request.headers.get("x-devrelay-confirm") != "apply":
            raise WebApiError(
                "confirmation_required",
                "X-DevRelay-Confirm: apply is required",
                status_code=403,
            )
        payload: RunPromptRequest = await _read_json(request, RunPromptRequest)
        run_id = str(request.path_params.get("run_id", ""))
        data = await run_in_threadpool(
            self.service.prompt_run,
            run_id,
            payload.role,
            payload.prompt,
        )
        return _json(
            request,
            success(data, request_id=str(request.state.request_id)),
        )

    async def run_messages(self, request: Request) -> Response:
        role = request.query_params.get("role", "")
        if role not in ("implementer", "reviewer"):
            raise WebApiError(
                "invalid_role",
                "role must be implementer or reviewer",
                status_code=400,
            )
        cursor = request.query_params.get("cursor")
        run_id = str(request.path_params.get("run_id", ""))
        data = await run_in_threadpool(
            self.service.run_messages,
            run_id,
            role,
            cursor,
        )
        return _json(
            request,
            success(data, request_id=str(request.state.request_id)),
        )

    async def run_interrupt(self, request: Request) -> Response:
        if request.headers.get("x-devrelay-confirm") != "apply":
            raise WebApiError(
                "confirmation_required",
                "X-DevRelay-Confirm: apply is required",
                status_code=403,
            )
        payload: RunInterruptRequest = await _read_json(request, RunInterruptRequest)
        run_id = str(request.path_params.get("run_id", ""))
        data = await run_in_threadpool(
            self.service.interrupt_run,
            run_id,
            payload.role,
        )
        return _json(
            request,
            success(data, request_id=str(request.state.request_id)),
        )

    async def tasks(self, request: Request) -> Response:
        raw = request.query_params.get("limit", "20")
        try:
            limit = int(raw)
        except ValueError as exc:
            raise WebApiError("invalid_limit", "limit must be an integer") from exc
        if limit < 1 or limit > 100:
            raise WebApiError("invalid_limit", "limit must be between 1 and 100")
        return _json(
            request,
            success(
                self.service.tasks(limit=limit),
                request_id=str(request.state.request_id),
            ),
        )

    async def task(self, request: Request) -> Response:
        task_id = str(request.path_params.get("task_id", ""))
        return _json(
            request,
            success(
                self.service.task(task_id),
                request_id=str(request.state.request_id),
            ),
        )

    async def roles(self, request: Request) -> Response:
        return _json(
            request,
            success(self.service.roles(), request_id=str(request.state.request_id)),
        )

    async def config(self, request: Request) -> Response:
        return _json(
            request,
            success(self.service.config(), request_id=str(request.state.request_id)),
        )

    async def config_validate(self, request: Request) -> Response:
        payload: ConfigValidateRequest = await _read_json(request, ConfigValidateRequest)
        return _json(
            request,
            success(
                self.service.validate_config(payload.config),
                request_id=str(request.state.request_id),
            ),
        )

    async def config_apply(self, request: Request) -> Response:
        if request.headers.get("x-devrelay-confirm") != "apply":
            raise WebApiError(
                "confirmation_required",
                "X-DevRelay-Confirm: apply is required",
                status_code=403,
            )
        payload: ConfigWriteRequest = await _read_json(request, ConfigWriteRequest)
        return _json(
            request,
            success(
                self.service.apply_config(payload.config, payload.expected_sha256),
                request_id=str(request.state.request_id),
            ),
        )

    async def wiring(self, request: Request) -> Response:
        return _json(
            request,
            success(
                self.service.wiring_status(),
                request_id=str(request.state.request_id),
            ),
        )

    async def wiring_apply(self, request: Request) -> Response:
        if request.headers.get("x-devrelay-confirm") != "apply":
            raise WebApiError(
                "confirmation_required",
                "X-DevRelay-Confirm: apply is required",
                status_code=403,
            )
        payload: WiringWriteRequest = await _read_json(request, WiringWriteRequest)
        return _json(
            request,
            success(
                self.service.apply_wiring(payload.wiring, payload.expected_sha256),
                request_id=str(request.state.request_id),
            ),
        )


# ---------------------------------------------------------------------------
# app construction
# ---------------------------------------------------------------------------
def create_app(
    workspace: str,
    *,
    port: int,
    token: str | None = None,
    registry: ProjectRegistry | None = None,
) -> Any:
    """Build the local API for one explicitly resolved workspace.

    The CLI validates the host, workspace and token shape before binding; this
    factory raises :class:`WebApiError` before serving any route when the
    workspace, token, registry or read service is invalid.
    """
    root, wiring, devrelay_dir = resolve_workspace(workspace)
    registry = registry or ProjectRegistry(devrelay_dir)
    # Validate the token and construct the read service before the registry's
    # idempotent write: a bad startup token or service must fail without touching
    # the workspace.
    auth = AuthManager(token or generate_token(), port=port)
    service = WebReadService.from_workspace(root, wiring, devrelay_dir)
    project = registry.add(root)
    api = LocalControlApi(
        service=service,
        registry=registry,
        project_id=project.project_id,
        auth=auth,
    )

    async def web_error_handler(request: Request, exc: Exception) -> Response:
        assert isinstance(exc, WebApiError)
        return _error_response(request, exc)

    async def http_error_handler(request: Request, exc: Exception) -> Response:
        status_code = getattr(exc, "status_code", 500)
        if status_code == 404:
            error = WebApiError("not_found", "route not found", status_code=404)
        elif status_code == 405:
            error = WebApiError(
                "method_not_allowed",
                "method not allowed",
                status_code=405,
            )
        else:
            error = WebApiError(
                "http_error",
                "request could not be served",
                status_code=int(status_code),
            )
        return _error_response(request, error)

    async def unhandled_error_handler(request: Request, exc: Exception) -> Response:
        print(
            f"[devrelay-web] unhandled {type(exc).__name__} for "
            f"{getattr(request.state, 'request_id', '')}",
            file=sys.stderr,
            flush=True,
        )
        return _error_response(
            request,
            WebApiError("internal_error", "internal server error", status_code=500),
        )

    app = Starlette(
        routes=[
            Route("/", api.ui_index, methods=["GET"]),
            Route("/ui", api.ui_index, methods=["GET"]),
            Route("/assets/{name}", api.ui_asset, methods=["GET"]),
            Route("/healthz", api.healthz, methods=["GET"]),
            Route("/api/session", api.session_create, methods=["POST"]),
            Route("/api/session", api.session_get, methods=["GET"]),
            Route("/api/session", api.session_delete, methods=["DELETE"]),
            Route("/api/health", api.health, methods=["GET"]),
            Route("/api/status", api.status, methods=["GET"]),
            Route("/api/projects", api.projects, methods=["GET"]),
            Route(
                "/api/projects/{project_id}/activate",
                api.activate_project,
                methods=["POST"],
            ),
            Route("/api/sessions", api.sessions, methods=["GET"]),
            Route("/api/runs", api.runs, methods=["GET"]),
            Route("/api/runs/{run_id}", api.run, methods=["GET"]),
            Route("/api/runs/{run_id}/decide", api.run_decide, methods=["POST"]),
            Route("/api/runs/{run_id}/interrupt", api.run_interrupt, methods=["POST"]),
            Route("/api/runs/{run_id}/prompt", api.run_prompt, methods=["POST"]),
            Route("/api/runs/{run_id}/messages", api.run_messages, methods=["GET"]),
            Route("/api/tasks", api.tasks, methods=["GET"]),
            Route("/api/tasks/{task_id}", api.task, methods=["GET"]),
            Route("/api/roles", api.roles, methods=["GET"]),
            Route("/api/config", api.config, methods=["GET"]),
            Route("/api/config", api.config_apply, methods=["PUT"]),
            Route("/api/config/validate", api.config_validate, methods=["POST"]),
            Route("/api/wiring", api.wiring, methods=["GET"]),
            Route("/api/wiring", api.wiring_apply, methods=["PUT"]),
        ],
        exception_handlers={
            WebApiError: web_error_handler,
            HTTPException: http_error_handler,
            Exception: unhandled_error_handler,
        },
    )
    app.state.api = api
    app.state.auth = auth
    return SecurityMiddleware(app, auth=auth)
