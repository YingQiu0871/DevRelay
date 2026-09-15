"""OpenCode session bridge (v0.3-A).

A narrow, provider-contained bridge between DevRelay and **one explicitly
configured, already-running OpenCode server**:

* one configured endpoint (never port scanning, never process discovery);
* one workspace (session ownership is validated, mismatches are hard failures);
* one explicitly selected session per operation (no "most recent" guessing);
* explicit operation states, explicit per-request accounting, no retries, no
  autonomous orchestration, no approval decisions.

Hard validation failures (bad configuration, unknown session, workspace
mismatch, unsupported capability raised by the caller) raise; provider
conditions (transport failure, timeout, HTTP error, malformed response) are
returned as :class:`OpenCodeOperationResult` states so a caller can never mistake
them for success.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from devrelay.errors import (
    OpenCodeConfigError,
    OpenCodeSessionNotFoundError,
    OpenCodeSessionWorkspaceMismatchError,
    OpenCodeUnsupportedError,
)
from devrelay.opencode.accounting import (
    FilesystemOpenCodeLedger,
    NullOpenCodeLedger,
    OpenCodeLedger,
)
from devrelay.opencode.models import (
    MAX_ID_CHARS,
    MAX_MESSAGES,
    MAX_PARTS,
    MAX_SESSIONS,
    MAX_TEXT_CHARS,
    MAX_TITLE_CHARS,
    MAX_WORKSPACE_CHARS,
    OpenCodeCallRecord,
    OpenCodeCallState,
    OpenCodeHealth,
    OpenCodeMessage,
    OpenCodeMessagePage,
    OpenCodeMessagePart,
    OpenCodeOperationResult,
    OpenCodeOperationState,
    OpenCodeSession,
    OpenCodeSessionState,
    _clean,
    prompt_digest,
)
from devrelay.opencode.transport import OpenCodePaths, OpenCodeTransport, TransportResponse
from devrelay.models import utcnow_iso

# Health capability names DevRelay understands (unknown names are ignored).
CAP_INTERRUPT = "interrupt"
CAP_LIST_SESSIONS = "list_sessions"
CAP_MESSAGES = "messages"

_SESSION_STATE_MAP = {
    "idle": OpenCodeSessionState.IDLE,
    "ready": OpenCodeSessionState.IDLE,
    "completed": OpenCodeSessionState.IDLE,
    "busy": OpenCodeSessionState.BUSY,
    "running": OpenCodeSessionState.BUSY,
    "working": OpenCodeSessionState.BUSY,
    "in_progress": OpenCodeSessionState.BUSY,
    "error": OpenCodeSessionState.ERROR,
    "failed": OpenCodeSessionState.ERROR,
}


def _normalize_state(value: object) -> OpenCodeSessionState:
    if isinstance(value, dict):
        for key in ("state", "status", "type"):
            if key in value:
                return _normalize_state(value[key])
        return OpenCodeSessionState.UNKNOWN
    text = str(value or "").strip().lower()
    return _SESSION_STATE_MAP.get(text, OpenCodeSessionState.UNKNOWN)


def _first(mapping: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return None


class OpenCodeBridge:
    """The v0.3-A capability surface (see the module docstring for the contract)."""

    def __init__(
        self,
        *,
        base_url: str,
        workspace_root: str | Path,
        token: str = "",
        timeout_seconds: float = 30.0,
        idle_timeout_seconds: float = 300.0,
        poll_interval_seconds: float = 1.0,
        max_response_bytes: int = 1_048_576,
        max_messages: int = 50,
        allow_unknown_workspace: bool = False,
        paths: OpenCodePaths | None = None,
        transport: OpenCodeTransport | None = None,
        ledger: OpenCodeLedger | None = None,
        devrelay_dir: Path | None = None,
        sleep: Callable[[float], None] | None = None,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        if not base_url or not str(base_url).strip():
            raise OpenCodeConfigError(
                "opencode.base_url is required: configure the OpenCode server "
                "endpoint explicitly (DevRelay never scans for servers)"
            )
        self.base_url = str(base_url).strip().rstrip("/")
        self.workspace_root = str(Path(workspace_root).resolve())
        self.idle_timeout_seconds = float(idle_timeout_seconds)
        self.poll_interval_seconds = max(0.05, float(poll_interval_seconds))
        self.max_messages = max(1, int(max_messages))
        self.allow_unknown_workspace = bool(allow_unknown_workspace)
        self.paths = paths or OpenCodePaths()
        self.transport = transport or OpenCodeTransport(
            self.base_url,
            paths=self.paths,
            token=token,
            timeout_seconds=timeout_seconds,
            max_response_bytes=max_response_bytes,
        )
        if ledger is not None:
            self.ledger: OpenCodeLedger = ledger
        elif devrelay_dir is not None:
            self.ledger = FilesystemOpenCodeLedger(Path(devrelay_dir))
        else:
            self.ledger = NullOpenCodeLedger()
        self._sleep = sleep or time.sleep
        self._monotonic = monotonic or time.monotonic

    # ------------------------------------------------------------------
    # 1. health
    # ------------------------------------------------------------------
    def health(self) -> OpenCodeOperationResult:
        """Probe the configured server (capability view; no session data)."""
        result, response = self._request("health", "GET", self.paths.health)
        if not response.ok:
            return self._failure(result, response)
        payload = response.data if isinstance(response.data, dict) else {}
        healthy = bool(_first(payload, "healthy", "ok", "up"))
        if not payload:
            healthy = True  # a 2xx JSON body without flags still means "reachable"
        capabilities = [
            str(item)[:64]
            for item in (payload.get("capabilities") or [])
            if isinstance(item, (str, int))
        ] if isinstance(payload.get("capabilities"), list) else []
        version = _clean(_first(payload, "version", "server_version"), 64)
        detail = _clean(_first(payload, "detail", "message", "status"), 300)
        health = OpenCodeHealth(
            healthy=healthy,
            version=version,
            capabilities=capabilities,
            detail=detail,
        )
        return self._complete(
            result,
            response,
            health=health,
            session=None,
        )

    # ------------------------------------------------------------------
    # 2. list_sessions
    # ------------------------------------------------------------------
    def list_sessions(self, *, include_other_workspaces: bool = False) -> OpenCodeOperationResult:
        """List sessions; every session carries its ownership verdict."""
        result, response = self._request("list_sessions", "GET", self.paths.sessions)
        if not response.ok:
            return self._failure(result, response)
        raw = response.data
        if isinstance(raw, dict):
            raw = _first(raw, "sessions", "data", "items") or []
        if not isinstance(raw, list):
            return self._malformed(result, response, "session list is not an array")
        sessions: list[OpenCodeSession] = []
        for item in raw[:MAX_SESSIONS]:
            if not isinstance(item, dict):
                continue
            session = self._normalize_session(item)
            if not session.session_id:
                continue
            if include_other_workspaces or session.workspace_match:
                sessions.append(session)
        return self._complete(result, response, sessions=sessions)

    # ------------------------------------------------------------------
    # 3. get_session
    # ------------------------------------------------------------------
    def get_session(self, session_id: str) -> OpenCodeOperationResult:
        """Read one explicitly selected session (ownership validated)."""
        session_id = self._require_session_id(session_id)
        result, response = self._request(
            "get_session", "GET", self.paths.session_path(session_id), session_id=session_id
        )
        if not response.ok:
            if response.status == 404:
                raise OpenCodeSessionNotFoundError(
                    f"session {session_id} does not exist on {self.base_url}"
                )
            return self._failure(result, response)
        payload = response.data
        if isinstance(payload, dict) and isinstance(payload.get("session"), dict):
            payload = payload["session"]
        if not isinstance(payload, dict):
            return self._malformed(result, response, "session payload is not an object")
        session = self._normalize_session(payload)
        if not session.session_id:
            session = session.model_copy(update={"session_id": session_id})
        self._assert_ownership(session)
        return self._complete(result, response, session=session)

    # ------------------------------------------------------------------
    # 4. read_messages
    # ------------------------------------------------------------------
    def read_messages(
        self, session_id: str, cursor: str | None = None
    ) -> OpenCodeOperationResult:
        """Read the message window; cursor semantics are explicit."""
        session_id = self._require_session_id(session_id)
        _session, failure, probe = self._probe_ownership("read_messages", session_id)
        if failure is not None:
            return failure
        result, response = self._request(
            "read_messages",
            "GET",
            self.paths.messages_path(session_id),
            session_id=session_id,
            result=probe,
        )
        if not response.ok:
            if response.status == 404:
                raise OpenCodeSessionNotFoundError(
                    f"session {session_id} has no message endpoint on {self.base_url}"
                )
            return self._failure(result, response)
        raw = response.data
        if isinstance(raw, dict):
            raw = _first(raw, "messages", "data", "items")
        if not isinstance(raw, list):
            return self._malformed(result, response, "message list is not an array")
        messages = [
            message
            for message in (self._normalize_message(item) for item in raw[:MAX_MESSAGES])
            if message is not None and message.message_id
        ]
        cursor_unknown = False
        replayed = False
        if cursor:
            ids = [message.message_id for message in messages]
            if cursor in ids:
                start = ids.index(cursor) + 1
                new_messages = messages[start:]
                replayed = not new_messages
            else:
                # The cursor is outside the current window: report it instead of
                # silently re-delivering (or dropping) messages.
                cursor_unknown = True
                new_messages = messages
        else:
            new_messages = messages[-self.max_messages :]
        page = OpenCodeMessagePage(
            session_id=session_id,
            messages=new_messages,
            next_cursor=(new_messages[-1].message_id if new_messages else (cursor or "")),
            cursor_unknown=cursor_unknown,
            replayed=replayed,
        )
        return self._complete(result, response, page=page, messages=new_messages)

    # ------------------------------------------------------------------
    # 5. send_prompt
    # ------------------------------------------------------------------
    def send_prompt(
        self,
        session_id: str,
        prompt: str,
        *,
        agent: str = "",
        model: str = "",
    ) -> OpenCodeOperationResult:
        """Send exactly one prompt to one explicitly selected session."""
        session_id = self._require_session_id(session_id)
        if not prompt or not prompt.strip():
            raise OpenCodeConfigError("send_prompt requires a non-empty prompt")
        _session, failure, probe = self._probe_ownership("send_prompt", session_id)
        if failure is not None:
            return failure
        body: dict[str, Any] = {
            "parts": [{"type": "text", "text": prompt}],
        }
        if agent:
            body["agent"] = agent
        if model:
            body["model"] = model
        result, response = self._request(
            "send_prompt",
            "POST",
            self.paths.prompt_path(session_id),
            json_body=body,
            session_id=session_id,
            prompt=prompt,
            agent=agent,
            model=model,
            result=probe,
        )
        if not response.ok:
            if response.status == 404:
                raise OpenCodeSessionNotFoundError(
                    f"session {session_id} has no prompt endpoint on {self.base_url}"
                )
            return self._failure(result, response)
        message = self._assistant_from_payload(response.data)
        if message is None:
            # Some servers answer with an acknowledgement only: read the window
            # instead of guessing (still exactly one extra issued request).
            follow_up = self.read_messages(session_id)
            if follow_up.state is OpenCodeOperationState.COMPLETED and follow_up.messages:
                message = follow_up.messages[-1]
                result.call_ids.extend(follow_up.call_ids)
                result.request_count += follow_up.request_count
        return self._complete(
            result,
            response,
            session=None,
            messages=[message] if message is not None else [],
        )

    # ------------------------------------------------------------------
    # 6. wait_idle
    # ------------------------------------------------------------------
    def wait_idle(
        self, session_id: str, timeout: float | None = None
    ) -> OpenCodeOperationResult:
        """Poll until the session is idle/terminal or the bound expires."""
        session_id = self._require_session_id(session_id)
        _session, failure, probe = self._probe_ownership("wait_idle", session_id)
        if failure is not None:
            return failure
        budget = float(self.idle_timeout_seconds if timeout is None else timeout)
        deadline = self._monotonic() + max(0.0, budget)
        result = probe.model_copy(
            update={
                "operation": "wait_idle",
                "state": OpenCodeOperationState.IN_FLIGHT,
                "session": None,
            }
        )
        last_session: OpenCodeSession | None = None
        while True:
            result, response = self._request(
                "wait_idle",
                "GET",
                self.paths.session_path(session_id),
                session_id=session_id,
                result=result,
            )
            if not response.ok:
                if response.status == 404:
                    raise OpenCodeSessionNotFoundError(
                        f"session {session_id} disappeared while waiting"
                    )
                return self._failure(result, response)
            payload = response.data
            if isinstance(payload, dict) and isinstance(payload.get("session"), dict):
                payload = payload["session"]
            if not isinstance(payload, dict):
                return self._malformed(result, response, "session payload is not an object")
            session = self._normalize_session(payload)
            if not session.session_id:
                session = session.model_copy(update={"session_id": session_id})
            last_session = session
            if session.state.terminal:
                return self._complete(
                    result, response, session=session, state=OpenCodeOperationState.COMPLETED
                )
            if self._monotonic() >= deadline:
                finished = self._settle(
                    result,
                    response,
                    state=OpenCodeCallState.COMPLETED,
                    http_status=response.status,
                )
                finished = finished.model_copy(
                    update={
                        "state": OpenCodeOperationState.TIMED_OUT,
                        "session": session,
                        "completed_at": utcnow_iso(),
                        "error_type": "idle_timeout",
                        "error": (
                            f"session {session_id} was still "
                            f"{session.state.value} after {budget:g}s; no retry is "
                            "attempted"
                        ),
                    }
                )
                return finished
            self._sleep(self.poll_interval_seconds)

    # ------------------------------------------------------------------
    # 7. interrupt
    # ------------------------------------------------------------------
    def interrupt(self, session_id: str) -> OpenCodeOperationResult:
        """Abort an in-flight operation (capability must be supported)."""
        session_id = self._require_session_id(session_id)
        _session, failure, probe = self._probe_ownership("interrupt", session_id)
        if failure is not None:
            return failure
        result, response = self._request(
            "interrupt",
            "POST",
            self.paths.abort_path(session_id),
            session_id=session_id,
            result=probe,
        )
        if response.status in (404, 405, 501):
            settle = self._settle(
                result, response, state=OpenCodeCallState.PROVIDER_UNAVAILABLE,
                http_status=response.status,
            )
            return settle.model_copy(
                update={
                    "state": OpenCodeOperationState.PROVIDER_UNAVAILABLE,
                    "error_type": "interrupt_unsupported",
                    "error": (
                        f"the configured server does not support interrupting "
                        f"session {session_id} (HTTP {response.status}); DevRelay "
                        "will not claim the operation was cancelled"
                    ),
                    "completed_at": utcnow_iso(),
                }
            )
        if not response.ok:
            return self._failure(result, response)
        return self._complete(
            result,
            response,
            state=OpenCodeOperationState.INTERRUPTED,
            session=None,
        )

    # ------------------------------------------------------------------
    # ownership / validation
    # ------------------------------------------------------------------
    def _require_session_id(self, session_id: str) -> str:
        value = (session_id or "").strip()
        if not value:
            raise OpenCodeConfigError(
                "an explicit session id is required (v0.3-A never guesses the "
                "'most recent' session)"
            )
        if len(value) > MAX_ID_CHARS:
            raise OpenCodeConfigError("session id is implausibly long")
        return value

    def _normalize_workspace(self, value: object) -> tuple[str, bool]:
        text = _clean(value, MAX_WORKSPACE_CHARS)
        if not text:
            return "", False
        try:
            return str(Path(text).resolve()), True
        except OSError:  # pragma: no cover - defensive
            return text, True

    def _probe_ownership(
        self, operation: str, session_id: str
    ) -> tuple[
        OpenCodeSession | None, OpenCodeOperationResult | None, OpenCodeOperationResult
    ]:
        """Validate ownership; propagate a provider condition instead of guessing.

        Returns ``(session, None)`` when the session is owned by this workspace,
        ``(None, failure_result)`` when the probe itself hit a provider condition
        (the failure keeps its own call accounting and state), and raises for
        hard validation failures (unknown session / workspace mismatch).
        """
        probe = self.get_session(session_id)
        if probe.ok and probe.session is not None:
            return probe.session, None, probe
        failure = probe.model_copy(
            update={
                "operation": operation,
                "session_id": session_id,
                "completed_at": probe.completed_at or utcnow_iso(),
            }
        )
        return None, failure, probe

    def _assert_ownership(self, session: OpenCodeSession | None) -> None:
        """Hard failure: a session must belong to the configured workspace."""
        if session is None:  # pragma: no cover - defensive
            raise OpenCodeSessionNotFoundError("session payload was empty")
        if not session.workspace_known:
            if self.allow_unknown_workspace:
                return
            raise OpenCodeSessionWorkspaceMismatchError(
                f"session {session.session_id} does not report a workspace; "
                "DevRelay cannot prove it belongs to this repository (set "
                "opencode.allow_unknown_workspace explicitly to accept that risk)"
            )
        if not session.workspace_match:
            raise OpenCodeSessionWorkspaceMismatchError(
                f"session {session.session_id} belongs to {session.workspace!r}, "
                f"but this workspace is {self.workspace_root!r}; cross-workspace "
                "session reuse is refused"
            )

    # ------------------------------------------------------------------
    # normalization
    # ------------------------------------------------------------------
    def _normalize_session(self, payload: Mapping[str, Any]) -> OpenCodeSession:
        session_id = _clean(_first(payload, "id", "session_id", "sessionID"), MAX_ID_CHARS)
        workspace_raw = _first(
            payload, "workspace", "directory", "cwd", "worktree", "path", "project"
        )
        if isinstance(workspace_raw, dict):
            workspace_raw = _first(workspace_raw, "path", "directory", "cwd")
        workspace, workspace_known = self._normalize_workspace(workspace_raw)
        match = bool(workspace_known and workspace == self.workspace_root)
        return OpenCodeSession(
            session_id=session_id,
            workspace=workspace,
            workspace_known=workspace_known,
            workspace_match=match,
            title=_clean(_first(payload, "title", "name", "summary"), MAX_TITLE_CHARS),
            state=_normalize_state(_first(payload, "state", "status")),
            agent=_clean(_first(payload, "agent", "agent_name"), 64),
            model=_clean(
                _first(payload, "model", "model_id", "modelID"), 128
            )
            if not isinstance(_first(payload, "model", "model_id", "modelID"), dict)
            else _clean(
                _first(_first(payload, "model", "model_id", "modelID"), "id", "name"),
                128,
            ),
            updated_at=_clean(
                _first(payload, "updated_at", "updatedAt", "time", "created_at"), 64
            ),
            parent_id=_clean(_first(payload, "parent_id", "parentID"), MAX_ID_CHARS),
        )

    def _normalize_message(self, payload: Any) -> OpenCodeMessage | None:
        if not isinstance(payload, dict):
            return None
        info = payload.get("info") if isinstance(payload.get("info"), dict) else payload
        message_id = _clean(
            _first(info, "id", "message_id", "messageID"), MAX_ID_CHARS
        )
        if not message_id:
            return None
        role_raw = _first(info, "role", "type")
        role = str(role_raw or "unknown").strip().lower()
        if role not in ("assistant", "user", "system"):
            role = "assistant" if role in ("ai", "model") else "unknown"
        parts: list[OpenCodeMessagePart] = []
        raw_parts = _first(payload, "parts", "content", "blocks")
        if isinstance(raw_parts, str):
            parts.append(OpenCodeMessagePart(kind="text", text=_clean(raw_parts, MAX_TEXT_CHARS)))
        elif isinstance(raw_parts, list):
            for item in raw_parts[:MAX_PARTS]:
                if isinstance(item, str):
                    parts.append(
                        OpenCodeMessagePart(kind="text", text=_clean(item, MAX_TEXT_CHARS))
                    )
                    continue
                if not isinstance(item, dict):
                    continue
                kind_raw = str(_first(item, "type", "kind") or "").strip().lower()
                if kind_raw in ("text", "reasoning"):
                    parts.append(
                        OpenCodeMessagePart(
                            kind="text", text=_clean(_first(item, "text", "content"), MAX_TEXT_CHARS)
                        )
                    )
                elif kind_raw in ("tool", "tool-call", "tool_use", "tool_result"):
                    parts.append(
                        OpenCodeMessagePart(
                            kind="tool",
                            name=_clean(
                                _first(item, "tool", "name", "tool_name"), 128
                            ),
                        )
                    )
                else:
                    parts.append(OpenCodeMessagePart(kind="other"))
        text = _first(info, "text", "summary")
        if not parts and isinstance(text, str):
            parts.append(OpenCodeMessagePart(kind="text", text=_clean(text, MAX_TEXT_CHARS)))
        return OpenCodeMessage(
            message_id=message_id,
            role=role,
            created_at=_clean(
                _first(info, "created_at", "createdAt", "time"), 64
            ),
            parts=parts,
        )

    def _assistant_from_payload(self, payload: Any) -> OpenCodeMessage | None:
        if isinstance(payload, dict):
            for key in ("message", "result", "data"):
                candidate = payload.get(key)
                if isinstance(candidate, dict):
                    message = self._normalize_message(candidate)
                    if message is not None:
                        return message
            message = self._normalize_message(payload)
            if message is not None:
                return message
        return None

    # ------------------------------------------------------------------
    # request plumbing (accounting + result shaping)
    # ------------------------------------------------------------------
    def _request(
        self,
        operation: str,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        session_id: str = "",
        prompt: str = "",
        agent: str = "",
        model: str = "",
        result: OpenCodeOperationResult | None = None,
    ) -> tuple[OpenCodeOperationResult, TransportResponse]:
        """Issue exactly one request, recording it before it leaves the machine."""
        call_id = self.ledger.allocate_call_id()
        started = utcnow_iso()
        record = OpenCodeCallRecord(
            call_id=call_id,
            operation=operation,
            state=OpenCodeCallState.ISSUED,
            method=method,
            path=path,
            session_id=session_id,
            issued=True,
            external_request_count=1,
            started_at=started,
            prompt_sha256=prompt_digest(prompt) if prompt else "",
            prompt_chars=len(prompt),
            agent=_clean(agent, 64),
            model=_clean(model, 128),
        )
        self.ledger.begin(record)
        response = self.transport.request(method, path, json_body=json_body)
        settled = record.model_copy(
            update={
                "state": response.state,
                "http_status": response.status,
                "error_type": response.error_type,
                "error": response.error,
                "completed_at": utcnow_iso(),
                "duration_ms": response.duration_ms,
                "response_bytes": response.response_bytes,
                "response_truncated": response.response_truncated,
            }
        )
        self.ledger.finish(settled)
        base = result or OpenCodeOperationResult(
            operation=operation,
            state=OpenCodeOperationState.ISSUED,
            session_id=session_id,
            started_at=started,
        )
        base = base.model_copy(
            update={
                "operation": operation,
                "session_id": session_id or base.session_id,
                "call_ids": list(base.call_ids) + [call_id],
                "request_count": base.request_count + 1,
                "http_status": response.status,
            }
        )
        return base, response

    def _complete(
        self,
        result: OpenCodeOperationResult,
        response: TransportResponse,
        *,
        state: OpenCodeOperationState = OpenCodeOperationState.COMPLETED,
        health: OpenCodeHealth | None = None,
        session: OpenCodeSession | None = None,
        sessions: Sequence[OpenCodeSession] | None = None,
        page: OpenCodeMessagePage | None = None,
        messages: Sequence[OpenCodeMessage] | None = None,
    ) -> OpenCodeOperationResult:
        return result.model_copy(
            update={
                "state": state,
                "completed_at": utcnow_iso(),
                "duration_ms": sum(
                    record.duration_ms for record in self._records_for(result)
                ),
                "health": health if health is not None else result.health,
                "session": session if session is not None else result.session,
                "sessions": list(sessions) if sessions is not None else list(result.sessions),
                "page": page if page is not None else result.page,
                "messages": list(messages) if messages is not None else list(result.messages),
                "error_type": "",
                "error": "",
            }
        )

    def _records_for(self, result: OpenCodeOperationResult) -> list[OpenCodeCallRecord]:
        wanted = set(result.call_ids)
        return [record for record in self.ledger.records() if record.call_id in wanted]

    def _failure(
        self, result: OpenCodeOperationResult, response: TransportResponse
    ) -> OpenCodeOperationResult:
        if response.state is OpenCodeCallState.TIMED_OUT:
            state = OpenCodeOperationState.TIMED_OUT
        elif response.state is OpenCodeCallState.MALFORMED_RESPONSE:
            state = OpenCodeOperationState.MALFORMED_RESPONSE
        else:
            state = OpenCodeOperationState.PROVIDER_UNAVAILABLE
        return result.model_copy(
            update={
                "state": state,
                "completed_at": utcnow_iso(),
                "duration_ms": sum(
                    record.duration_ms for record in self._records_for(result)
                ),
                "http_status": response.status,
                "error_type": response.error_type or "provider_unavailable",
                "error": response.error,
            }
        )

    def _malformed(
        self, result: OpenCodeOperationResult, response: TransportResponse, detail: str
    ) -> OpenCodeOperationResult:
        return result.model_copy(
            update={
                "state": OpenCodeOperationState.MALFORMED_RESPONSE,
                "completed_at": utcnow_iso(),
                "duration_ms": sum(
                    record.duration_ms for record in self._records_for(result)
                ),
                "http_status": response.status,
                "error_type": response.error_type or "unexpected_shape",
                "error": detail,
            }
        )

    def _settle(
        self,
        result: OpenCodeOperationResult,
        response: TransportResponse,
        *,
        state: OpenCodeCallState,
        http_status: int | None,
    ) -> OpenCodeOperationResult:
        """Settle the *last* call of ``result`` explicitly (interrupt/timeout)."""
        if result.call_ids:
            call_id = result.call_ids[-1]
            existing = next(
                (r for r in self.ledger.records() if r.call_id == call_id), None
            )
            if existing is not None:
                self.ledger.finish(
                    existing.model_copy(
                        update={
                            "state": state,
                            "http_status": http_status,
                            "completed_at": utcnow_iso(),
                        }
                    )
                )
        return result
