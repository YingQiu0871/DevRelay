"""OpenCode session bridge (v0.3-A).

A narrow, provider-contained bridge between DevRelay and **one explicitly
configured, already-running OpenCode server**:

* one configured endpoint (never port scanning, never process discovery);
* one workspace (session ownership is validated, mismatches are hard failures);
* one explicitly selected session per operation (no "most recent" guessing);
* explicit operation states, explicit per-request accounting, no retries, no
  autonomous orchestration, no approval decisions.

Two rules drive the error model:

* **hard validation failures raise** (bad configuration, invalid session id,
  unknown session, workspace mismatch) - they are user/programming errors;
* **provider conditions are returned** as :class:`OpenCodeOperationResult` states
  (unavailable, timeout, malformed, interrupt unsupported, reply still pending)
  so a caller can never mistake them for success.

v0.3-A remediation notes: ``wait_idle`` obeys a whole-operation deadline (every
request is clamped to the remaining budget), ``read_messages`` keeps the *newest*
messages of the provider payload, ``send_prompt`` correlates a reply against a
boundary taken before submission, and ``interrupt`` distinguishes an accepted
abort request from a verified terminal state.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from devrelay.errors import (
    OpenCodeConfigError,
    OpenCodeSessionNotFoundError,
    OpenCodeSessionWorkspaceMismatchError,
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
    MAX_STATE_DEPTH,
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
    valid_session_id,
)
from devrelay.opencode.transport import OpenCodePaths, OpenCodeTransport, TransportResponse
from devrelay.models import utcnow_iso

# Health capability names DevRelay understands (unknown names are ignored).
CAP_INTERRUPT = "interrupt"
CAP_LIST_SESSIONS = "list_sessions"
CAP_MESSAGES = "messages"

#: The provider payload may deliver more messages than we keep; the newest ones
#: always win.  This is a *local* window, not server pagination.
HARD_MAX_MESSAGES = MAX_MESSAGES

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

#: Role markers accepted as an assistant message (provider spellings).
_ASSISTANT_ROLES = {"assistant", "ai", "model"}

#: Keys that indicate a non-message envelope even when it carries an ``id``.
_ENVELOPE_KEYS = ("directory", "workspace", "cwd", "session_id", "worktree")


def _normalize_state(
    value: object, *, max_depth: int = MAX_STATE_DEPTH
) -> tuple[OpenCodeSessionState, bool]:
    """Bounded iterative unwrapping of provider state.

    Returns ``(state, overflow)``; ``overflow`` is True when the provider nested
    state deeper than ``max_depth`` (malformed/protocol condition) - never an
    uncaught ``RecursionError``.
    """
    current = value
    for _ in range(max_depth):
        if isinstance(current, dict):
            for key in ("state", "status", "type"):
                if key in current:
                    current = current[key]
                    break
            else:
                return OpenCodeSessionState.UNKNOWN, False
            continue
        text = str(current or "").strip().lower()
        return _SESSION_STATE_MAP.get(text, OpenCodeSessionState.UNKNOWN), False
    return OpenCodeSessionState.UNKNOWN, True


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
        if max_messages > HARD_MAX_MESSAGES:
            # No server pagination is implemented in v0.3-A, so a larger window
            # could not be honoured honestly.
            raise OpenCodeConfigError(
                f"opencode.max_messages must be <= {HARD_MAX_MESSAGES} "
                "(v0.3-A has no server-side pagination; the provider payload is "
                "windowed locally and the newest messages are kept)"
            )
        self.base_url = str(base_url).strip().rstrip("/")
        self.workspace_root = os.path.normpath(str(Path(workspace_root).resolve()))
        self.idle_timeout_seconds = float(idle_timeout_seconds)
        self.poll_interval_seconds = max(0.05, float(poll_interval_seconds))
        self.max_messages = max(1, min(int(max_messages), HARD_MAX_MESSAGES))
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
        return self._complete(result, health=health)

    # ------------------------------------------------------------------
    # 2. list_sessions
    # ------------------------------------------------------------------
    def list_sessions(
        self, *, include_other_workspaces: bool = False
    ) -> OpenCodeOperationResult:
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
        return self._complete(result, sessions=sessions)

    # ------------------------------------------------------------------
    # 3. get_session
    # ------------------------------------------------------------------
    def get_session(self, session_id: str) -> OpenCodeOperationResult:
        """Read one explicitly selected session (ownership validated)."""
        session_id = self._require_session_id(session_id)
        session, failure, merged, _response = self._fetch_session(
            "get_session", session_id
        )
        if session is None:
            if failure is not None:
                return failure
            raise OpenCodeSessionNotFoundError(
                f"session {session_id} does not exist on {self.base_url}"
            )
        return self._complete(merged, session=session)

    # ------------------------------------------------------------------
    # 4. read_messages
    # ------------------------------------------------------------------
    def read_messages(
        self,
        session_id: str,
        cursor: str | None = None,
        *,
        prior: OpenCodeOperationResult | None = None,
        accounting: list[OpenCodeOperationResult] | None = None,
        redact_values: Sequence[str] = (),
    ) -> OpenCodeOperationResult:
        """Read the message window (newest messages win; cursor is explicit).

        ``prior``/``accounting`` exist for the internal follow-up read of
        :meth:`send_prompt`: ``accounting`` always receives the newest merged
        result, including immediately before a typed failure is raised, so an
        attempt that issued requests can never lose them from the operation's
        accounting (P1-3: operation accounting == ledger accounting).

        ``redact_values`` are in-memory literals (typically the prompt that was
        just submitted) that must never survive a provider echo into a persisted
        error snippet (P2-D).  They are never stored anywhere.
        """
        session_id = self._require_session_id(session_id)
        session, failure, merged, _response = self._fetch_session(
            "read_messages",
            session_id,
            result=prior,
            redact_values=redact_values,
        )
        if accounting is not None:
            accounting.append(merged)
        if session is None and failure is not None:
            return failure
        if session is None:
            raise OpenCodeSessionNotFoundError(
                f"session {session_id} does not exist on {self.base_url}"
            )
        result, response = self._request(
            "read_messages",
            "GET",
            self.paths.messages_path(session_id),
            session_id=session_id,
            result=merged,
            extra_redactions=redact_values,
        )
        if accounting is not None:
            accounting.append(result)
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
        provider_count = len(raw)
        messages = [
            message
            for message in (
                self._normalize_message(item) for item in raw[: MAX_MESSAGES * 10]
            )
            if message is not None and message.message_id
        ]
        # P1-2: the *newest* messages are the useful ones - never head-truncate.
        window_truncated = (
            len(messages) > self.max_messages or provider_count > MAX_MESSAGES
        )
        window = messages[-self.max_messages :]
        cursor_unknown = False
        replayed = False
        if cursor:
            ids = [message.message_id for message in window]
            if cursor in ids:
                start = ids.index(cursor) + 1
                new_messages = window[start:]
                # "Nothing new" is only honest when the cursor is the newest
                # message actually present in the received payload.
                replayed = not new_messages and ids[-1] == cursor
            else:
                # The cursor is outside the kept window: report it instead of
                # silently re-delivering (or dropping) messages.
                cursor_unknown = True
                new_messages = window
        else:
            new_messages = window
        page = OpenCodeMessagePage(
            session_id=session_id,
            messages=new_messages,
            next_cursor=(
                new_messages[-1].message_id if new_messages else (cursor or "")
            ),
            cursor_unknown=cursor_unknown,
            replayed=replayed,
            provider_message_count=provider_count,
            window_truncated=window_truncated,
            hard_max_messages=HARD_MAX_MESSAGES,
        )
        return self._complete(result, page=page, messages=new_messages)

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
        """Send exactly one prompt and correlate any reply honestly (P1-3)."""
        session_id = self._require_session_id(session_id)
        if not prompt or not prompt.strip():
            raise OpenCodeConfigError("send_prompt requires a non-empty prompt")
        _session, failure, merged = self._probe_ownership("send_prompt", session_id)
        if failure is not None:
            return failure
        # Boundary BEFORE submission: everything already visible is "old".
        boundary_result = self.read_messages(session_id)
        if not boundary_result.ok:
            return self._as_operation(boundary_result, "send_prompt", session_id)
        known_ids = {message.message_id for message in boundary_result.messages}
        boundary_cursor = (
            boundary_result.page.next_cursor if boundary_result.page is not None else ""
        )
        merged = merged.model_copy(
            update={
                "call_ids": list(merged.call_ids) + list(boundary_result.call_ids),
                "request_count": merged.request_count + boundary_result.request_count,
            }
        )
        body: dict[str, Any] = {"parts": [{"type": "text", "text": prompt}]}
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
            result=merged,
        )
        if not response.ok:
            if response.status == 404:
                raise OpenCodeSessionNotFoundError(
                    f"session {session_id} has no prompt endpoint on {self.base_url}"
                )
            return self._failure(result, response)

        # ---- inline candidate: only an explicit, *new* assistant message -----
        candidate = self._assistant_from_payload(response.data)
        if candidate is not None and candidate.message_id not in known_ids:
            return self._complete(
                result, messages=[candidate], reply_boundary=boundary_cursor
            )

        # ---- ack-only / asynchronous: one explicit follow-up read ------------
        follow_up = self._read_after_prompt(
            session_id, boundary_cursor, result, prompt
        )
        if follow_up.state is OpenCodeOperationState.MALFORMED_RESPONSE:
            return follow_up
        if not follow_up.ok:
            # The prompt WAS accepted: never suggest it was not submitted, never
            # encourage a transparent resubmission.
            return follow_up.model_copy(
                update={
                    "operation": "send_prompt",
                    "session_id": session_id,
                    "reply_pending": True,
                    "reply_boundary": boundary_cursor,
                    "follow_up_state": follow_up.state.value,
                }
            )
        fresh = [
            message
            for message in follow_up.messages
            if message.role == "assistant" and message.message_id not in known_ids
        ]
        if fresh:
            return follow_up.model_copy(
                update={
                    "operation": "send_prompt",
                    "session_id": session_id,
                    "reply_pending": False,
                    "reply_boundary": boundary_cursor,
                    "follow_up_state": follow_up.state.value,
                    "messages": [fresh[-1]],
                }
            )
        return follow_up.model_copy(
            update={
                "operation": "send_prompt",
                "session_id": session_id,
                "reply_pending": True,
                "reply_boundary": boundary_cursor,
                "follow_up_state": follow_up.state.value,
                "error_type": "reply_pending",
                "error": (
                    "the prompt was accepted but no new assistant message was "
                    "visible yet; DevRelay does not substitute a stale reply and "
                    "does not resubmit automatically"
                ),
                "messages": [],
            }
        )

    def _read_after_prompt(
        self,
        session_id: str,
        boundary_cursor: str,
        prior: OpenCodeOperationResult,
        prompt: str,
    ) -> OpenCodeOperationResult:
        """One explicit follow-up read whose accounting always merges (P1-3)."""
        # Even a follow-up that fails after issuing requests must be accounted
        # for: the ledger recorded them, so the operation result must too.
        accounting: list[OpenCodeOperationResult] = []
        try:
            follow_up = self.read_messages(
                session_id,
                boundary_cursor or None,
                prior=prior,
                accounting=accounting,
                redact_values=(prompt,),
            )
        except OpenCodeSessionNotFoundError as exc:
            # Post-acceptance: a vanished session is a follow-up condition, not a
            # "your prompt was never submitted" failure.
            merged = accounting[-1] if accounting else prior
            return merged.model_copy(
                update={
                    "operation": "send_prompt",
                    "session_id": session_id,
                    "state": OpenCodeOperationState.PROVIDER_UNAVAILABLE,
                    "completed_at": utcnow_iso(),
                    "duration_ms": self._elapsed_ms(merged),
                    "reply_pending": True,
                    "reply_boundary": boundary_cursor,
                    "follow_up_state": OpenCodeOperationState.PROVIDER_UNAVAILABLE.value,
                    "error_type": "follow_up_session_not_found",
                    "error": str(exc),
                }
            )
        # ``follow_up`` was seeded with ``prior``, so it *already* carries the
        # merged accounting: adding ``prior`` again would double-count every
        # call the prompt operation has made so far.
        return follow_up.model_copy(
            update={
                "completed_at": follow_up.completed_at or utcnow_iso(),
                "duration_ms": self._elapsed_ms(follow_up),
            }
        )

    # ------------------------------------------------------------------
    # 6. wait_idle
    # ------------------------------------------------------------------
    def wait_idle(
        self,
        session_id: str,
        timeout: float | None = None,
        *,
        redact_values: Sequence[str] = (),
    ) -> OpenCodeOperationResult:
        """Poll until idle/terminal or the whole-operation deadline expires.

        The deadline is established *before* the ownership probe, and every
        request that participates (probe and polls alike) is clamped to the
        remaining budget, so the operation can never run past it (P1-1).
        """
        session_id = self._require_session_id(session_id)
        budget = float(self.idle_timeout_seconds if timeout is None else timeout)
        budget = max(0.0, budget)
        started = self._monotonic()
        deadline = started + budget
        result = OpenCodeOperationResult(
            operation="wait_idle",
            state=OpenCodeOperationState.IN_FLIGHT,
            session_id=session_id,
            started_at=utcnow_iso(),
        )

        remaining = deadline - self._monotonic()
        if remaining <= 0:
            return self._idle_timeout(result, None, budget)
        session, failure, result, _response = self._fetch_session(
            "wait_idle",
            session_id,
            result=result,
            timeout_seconds=remaining,
            redact_values=redact_values,
        )
        if session is None and failure is not None:
            return failure
        if session is None:
            raise OpenCodeSessionNotFoundError(
                f"session {session_id} does not exist on {self.base_url}"
            )
        last_session = session
        if last_session.state.terminal:
            return self._complete(result, session=last_session)

        while True:
            remaining = deadline - self._monotonic()
            if remaining <= 0:
                return self._idle_timeout(result, last_session, budget)
            result, response = self._request(
                "wait_idle",
                "GET",
                self.paths.session_path(session_id),
                session_id=session_id,
                result=result,
                timeout_seconds=remaining,
                extra_redactions=redact_values,
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
                return self._malformed(
                    result, response, "session payload is not an object"
                )
            session = self._normalize_session(payload)
            if not session.session_id:
                session = session.model_copy(update={"session_id": session_id})
            if session.state_overflow:
                return self._malformed(
                    result, response, "provider session state nested too deeply"
                )
            last_session = session
            if session.state.terminal:
                return self._complete(result, session=session)
            remaining = deadline - self._monotonic()
            if remaining <= 0:
                return self._idle_timeout(result, last_session, budget)
            # Never sleep past the deadline.
            self._sleep(min(self.poll_interval_seconds, remaining))

    def _idle_timeout(
        self,
        result: OpenCodeOperationResult,
        session: OpenCodeSession | None,
        budget: float,
    ) -> OpenCodeOperationResult:
        """Explicit TIMED_OUT with *actual* whole-operation duration evidence."""
        return result.model_copy(
            update={
                "state": OpenCodeOperationState.TIMED_OUT,
                "session": session,
                "completed_at": utcnow_iso(),
                "duration_ms": self._elapsed_ms(result),
                "error_type": "idle_timeout",
                "error": (
                    f"session did not become idle/terminal within {budget:g}s; "
                    "no retry is attempted and no polling continues after return"
                ),
            }
        )

    # ------------------------------------------------------------------
    # 7. interrupt
    # ------------------------------------------------------------------
    def interrupt(self, session_id: str) -> OpenCodeOperationResult:
        """Abort an in-flight operation (capability must be supported)."""
        session_id = self._require_session_id(session_id)
        _session, failure, merged = self._probe_ownership("interrupt", session_id)
        if failure is not None:
            return failure
        result, response = self._request(
            "interrupt",
            "POST",
            self.paths.abort_path(session_id),
            session_id=session_id,
            result=merged,
            expect_json=False,
        )
        if response.state is OpenCodeCallState.MALFORMED_RESPONSE:
            # Oversized/unusable interrupt responses are their own condition; they
            # are never reported as "the capability is unsupported" (P2-C).
            return self._malformed(
                result, response, "interrupt response was unusable"
            )
        if response.status == 404:
            return self._as_state(
                result,
                OpenCodeOperationState.PROVIDER_UNAVAILABLE,
                "interrupt_session_not_found",
                f"session {session_id} no longer exists on {self.base_url}; the "
                "abort was not applied",
            )
        if response.status in (405, 501):
            return self._as_state(
                result,
                OpenCodeOperationState.PROVIDER_UNAVAILABLE,
                "interrupt_unsupported",
                "the configured server does not support interrupting session "
                f"{session_id} (HTTP {response.status}); DevRelay will not claim "
                "the operation was cancelled",
            )
        if not response.ok:
            return self._failure(result, response)
        # 2xx (including an empty 204) means the abort request was accepted.  It
        # is *not* a verified terminal state, and DevRelay says so explicitly.
        return self._as_state(
            result,
            OpenCodeOperationState.INTERRUPTED,
            "",
            "",
            interrupt_verified=False,
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
        if not valid_session_id(value):
            # P2-B: identifiers are interpolated into URL paths, so anything that
            # could change the path meaning (``/``, ``?``, ``#``, whitespace,
            # control characters, traversal, overlong ids) is rejected before a
            # request is constructed.
            raise OpenCodeConfigError(
                "session id is not a valid opaque OpenCode identifier "
                "(allowed: unreserved characters [A-Za-z0-9._~-], length 1-200, "
                "no path separators, query/fragment markers or traversal)"
            )
        return value

    def _normalize_workspace(self, value: object) -> tuple[str, bool]:
        """Normalize a provider-reported workspace identity.

        Only **absolute** paths are trusted: a relative provider value has an
        undefined base (provider namespace, container, remote host), and assuming
        DevRelay's own working directory would silently weaken the ownership
        check.  Relative/ambiguous values are reported as *unknown*, which fails
        closed unless ``allow_unknown_workspace`` is explicitly set.
        """
        text = _clean(value, MAX_WORKSPACE_CHARS)
        if not text:
            return "", False
        if not os.path.isabs(text):
            return text, False
        try:
            return os.path.normpath(os.path.abspath(text)), True
        except OSError:  # pragma: no cover - defensive
            return text, False

    def _assert_ownership(self, session: OpenCodeSession | None) -> None:
        """Hard failure: a session must belong to the configured workspace."""
        if session is None:  # pragma: no cover - defensive
            raise OpenCodeSessionNotFoundError("session payload was empty")
        if not session.workspace_known:
            if self.allow_unknown_workspace:
                return
            raise OpenCodeSessionWorkspaceMismatchError(
                f"session {session.session_id} does not report an absolute "
                "workspace path; DevRelay cannot prove it belongs to this "
                "repository (set opencode.allow_unknown_workspace explicitly to "
                "accept that risk)"
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
        session_id = _clean(
            _first(payload, "id", "session_id", "sessionID"), MAX_ID_CHARS
        )
        workspace_raw = _first(
            payload, "workspace", "directory", "cwd", "worktree", "path", "project"
        )
        if isinstance(workspace_raw, dict):
            workspace_raw = _first(workspace_raw, "path", "directory", "cwd")
        workspace, workspace_known = self._normalize_workspace(workspace_raw)
        match = bool(workspace_known and workspace == self.workspace_root)
        state, state_overflow = _normalize_state(_first(payload, "state", "status"))
        return OpenCodeSession(
            session_id=session_id,
            workspace=workspace,
            workspace_known=workspace_known,
            workspace_match=match,
            title=_clean(_first(payload, "title", "name", "summary"), MAX_TITLE_CHARS),
            state=state,
            state_overflow=state_overflow,
            agent=_clean(_first(payload, "agent", "agent_name"), 64),
            model=self._normalize_model(payload),
            updated_at=_clean(
                _first(payload, "updated_at", "updatedAt", "time", "created_at"), 64
            ),
            parent_id=_clean(_first(payload, "parent_id", "parentID"), MAX_ID_CHARS),
        )

    @staticmethod
    def _normalize_model(payload: Mapping[str, Any]) -> str:
        raw = _first(payload, "model", "model_id", "modelID")
        if isinstance(raw, dict):
            raw = _first(raw, "id", "name")
        return _clean(raw, 128)

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
            role = "assistant" if role in _ASSISTANT_ROLES else "unknown"
        parts: list[OpenCodeMessagePart] = []
        raw_parts = _first(payload, "parts", "content", "blocks")
        if isinstance(raw_parts, str):
            parts.append(
                OpenCodeMessagePart(kind="text", text=_clean(raw_parts, MAX_TEXT_CHARS))
            )
        elif isinstance(raw_parts, list):
            for item in raw_parts[:MAX_PARTS]:
                if isinstance(item, str):
                    parts.append(
                        OpenCodeMessagePart(
                            kind="text", text=_clean(item, MAX_TEXT_CHARS)
                        )
                    )
                    continue
                if not isinstance(item, dict):
                    continue
                kind_raw = str(_first(item, "type", "kind") or "").strip().lower()
                if kind_raw in ("text", "reasoning"):
                    parts.append(
                        OpenCodeMessagePart(
                            kind="text",
                            text=_clean(
                                _first(item, "text", "content"), MAX_TEXT_CHARS
                            ),
                        )
                    )
                elif kind_raw in ("tool", "tool-call", "tool_use", "tool_result"):
                    parts.append(
                        OpenCodeMessagePart(
                            kind="tool",
                            name=_clean(_first(item, "tool", "name", "tool_name"), 128),
                        )
                    )
                else:
                    parts.append(OpenCodeMessagePart(kind="other"))
        text = _first(info, "text", "summary")
        if not parts and isinstance(text, str):
            parts.append(
                OpenCodeMessagePart(kind="text", text=_clean(text, MAX_TEXT_CHARS))
            )
        return OpenCodeMessage(
            message_id=message_id,
            role=role,
            created_at=_clean(_first(info, "created_at", "createdAt", "time"), 64),
            parts=parts,
        )

    def _assistant_from_payload(self, payload: Any) -> OpenCodeMessage | None:
        """Accept an inline reply only when it is an explicit assistant message.

        A session object, a result envelope or any arbitrary id-bearing dict is
        **not** a reply (P1-3); those are rejected here and handled by the
        follow-up path instead.
        """
        candidates: list[Any] = []
        if isinstance(payload, dict):
            for key in ("message", "reply", "result", "data"):
                candidate = payload.get(key)
                if isinstance(candidate, dict):
                    candidates.append(candidate)
            candidates.append(payload)
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            if any(key in candidate for key in _ENVELOPE_KEYS) and not isinstance(
                candidate.get("info"), dict
            ):
                continue  # looks like a session/envelope, not a message
            message = self._normalize_message(candidate)
            if message is None or not message.message_id:
                continue
            if message.role != "assistant":
                continue
            if not message.parts:
                continue
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
        timeout_seconds: float | None = None,
        expect_json: bool = True,
        extra_redactions: Sequence[str] = (),
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
        response = self.transport.request(
            method,
            path,
            json_body=json_body,
            timeout_seconds=timeout_seconds,
            redact_values=(
                tuple(extra_redactions) + ((prompt,) if prompt else ())
            ),
            expect_json=expect_json,
        )
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

    def _fetch_session(
        self,
        operation: str,
        session_id: str,
        *,
        result: OpenCodeOperationResult | None = None,
        timeout_seconds: float | None = None,
        redact_values: Sequence[str] = (),
    ) -> tuple[
        OpenCodeSession | None,
        OpenCodeOperationResult | None,
        OpenCodeOperationResult,
        TransportResponse,
    ]:
        """Fetch + validate one session, returning merged accounting.

        Returns ``(session, failure, merged_result, response)``.  A ``404`` yields
        ``(None, None, merged, response)`` so the caller can decide between a hard
        not-found failure and an honest post-acceptance result.
        """
        merged, response = self._request(
            operation,
            "GET",
            self.paths.session_path(session_id),
            session_id=session_id,
            result=result,
            timeout_seconds=timeout_seconds,
            extra_redactions=redact_values,
        )
        if response.status == 404:
            return None, None, merged, response
        if not response.ok:
            return None, self._failure(merged, response), merged, response
        payload = response.data
        if isinstance(payload, dict) and isinstance(payload.get("session"), dict):
            payload = payload["session"]
        if not isinstance(payload, dict):
            return (
                None,
                self._malformed(merged, response, "session payload is not an object"),
                merged,
                response,
            )
        session = self._normalize_session(payload)
        if session.session_id and session.session_id != session_id:
            # The endpoint contract supplied an id that is not the requested one.
            return (
                None,
                self._malformed(
                    merged,
                    response,
                    f"server returned session {session.session_id!r} for request "
                    f"{session_id!r}",
                ),
                merged,
                response,
            )
        if not session.session_id:
            session = session.model_copy(update={"session_id": session_id})
        if session.state_overflow:
            return (
                None,
                self._malformed(
                    merged, response, "provider session state nested too deeply"
                ),
                merged,
                response,
            )
        self._assert_ownership(session)
        return session, None, merged, response

    def _probe_ownership(
        self, operation: str, session_id: str
    ) -> tuple[
        OpenCodeSession | None, OpenCodeOperationResult | None, OpenCodeOperationResult
    ]:
        """Ownership probe: hard failure for unknown/mismatched sessions."""
        session, failure, merged, _response = self._fetch_session(
            operation, session_id
        )
        if session is None:
            if failure is not None:
                return None, failure, merged
            raise OpenCodeSessionNotFoundError(
                f"session {session_id} does not exist on {self.base_url}"
            )
        return session, None, merged

    # ------------------------------------------------------------------
    # result shaping
    # ------------------------------------------------------------------
    def _complete(
        self,
        result: OpenCodeOperationResult,
        *,
        state: OpenCodeOperationState = OpenCodeOperationState.COMPLETED,
        health: OpenCodeHealth | None = None,
        session: OpenCodeSession | None = None,
        sessions: Sequence[OpenCodeSession] | None = None,
        page: OpenCodeMessagePage | None = None,
        messages: Sequence[OpenCodeMessage] | None = None,
        reply_boundary: str = "",
    ) -> OpenCodeOperationResult:
        return result.model_copy(
            update={
                "state": state,
                "completed_at": utcnow_iso(),
                "duration_ms": self._elapsed_ms(result),
                "health": health if health is not None else result.health,
                "session": session if session is not None else result.session,
                "sessions": (
                    list(sessions) if sessions is not None else list(result.sessions)
                ),
                "page": page if page is not None else result.page,
                "messages": (
                    list(messages) if messages is not None else list(result.messages)
                ),
                "reply_boundary": reply_boundary or result.reply_boundary,
                "error_type": "",
                "error": "",
            }
        )

    def _as_state(
        self,
        result: OpenCodeOperationResult,
        state: OpenCodeOperationState,
        error_type: str,
        error: str,
        *,
        interrupt_verified: bool | None = None,
    ) -> OpenCodeOperationResult:
        update: dict[str, Any] = {
            "state": state,
            "completed_at": utcnow_iso(),
            "duration_ms": self._elapsed_ms(result),
            "error_type": error_type,
            "error": error,
        }
        if interrupt_verified is not None:
            update["interrupt_verified"] = interrupt_verified
        return result.model_copy(update=update)

    def _as_operation(
        self, result: OpenCodeOperationResult, operation: str, session_id: str
    ) -> OpenCodeOperationResult:
        return result.model_copy(
            update={"operation": operation, "session_id": session_id}
        )

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
                "duration_ms": self._elapsed_ms(result),
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
                "duration_ms": self._elapsed_ms(result),
                "http_status": response.status,
                "error_type": response.error_type or "unexpected_shape",
                "error": detail,
            }
        )

    def _elapsed_ms(self, result: OpenCodeOperationResult) -> int:
        """Actual total operation duration, from the recorded per-call evidence."""
        total = 0
        wanted = set(result.call_ids)
        for record in self.ledger.records():
            if record.call_id in wanted:
                total += record.duration_ms
        return max(total, 0)
