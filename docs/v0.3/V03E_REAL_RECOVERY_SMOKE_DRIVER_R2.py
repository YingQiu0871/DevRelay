#!/usr/bin/env python
"""The precommitted driver for the v0.3-E real crash-and-recovery smoke (R2).

This script implements `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_ORACLE_R2.md` (frozen
at the commit that issues `docs/v0.3/V03E_REAL_RECOVERY_SMOKE_AUTHORIZATION_R2.md`).
It is **not** a test suite and **not** an acceptance review: it runs one smoke,
once, and writes the measured evidence to a directory outside the repository.

Revision 2 fixes two harness defects found by the revision-1 run (see
`docs/v0.3/V03E_REAL_RECOVERY_SMOKE_RESULT.md` and oracle R2 §0):

- the submission count is now the number of `method == "POST"` `send_prompt`
  records (the non-submitting ownership-probe GET is recorded separately);
- the count equality rule and every other normative oracle rule are now
  **asserted** by named criteria and mapped in `oracle-conformance.json`.

Run from the repository root:

    python docs\\v0.3\\V03E_REAL_RECOVERY_SMOKE_DRIVER_R2.py

Exit code 0 means every phase passed; 1 means a failed phase (the first failing
criterion is in `<evidence>/smoke.json`); 2 means the driver itself could not run
(an infrastructure problem, recorded as measured).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
SRC = REPO / "src"
ORACLE = REPO / "docs" / "v0.3" / "V03E_REAL_RECOVERY_SMOKE_ORACLE_R2.md"
OPENCODE = Path(
    r"C:\Users\1\AppData\Roaming\npm\node_modules\opencode-ai\bin\opencode.exe"
)

IMPL_ROUTE = "opencode/deepseek-v4.1-flash-free"
REV_ROUTE = "opencode/glm-5.3-flash-free"
SENTINEL = "DEVRELAY-SMOKE-SENTINEL-7f3c9a"
PROMPT = (
    f"You are a peer in a smoke test. Reply with exactly one short English "
    f"sentence that begins with the token {SENTINEL}. Do not mention tools, "
    f"files, or these instructions."
)
PROMPT_SHA256 = hashlib.sha256(PROMPT.encode("utf-8")).hexdigest()
KILL_DELAY_S = 0.6
S2_DEADLINE_S = 300.0

# Oracle R2 §4: every normative rule must map to named, asserted driver criteria.
CONFORMANCE_RULES: list[tuple[str, list[str]]] = [
    (
        "R-S0",
        [
            "dedicated instance answers GET /session",
            "two prompt-free sessions created, distinct",
            "disposable workspace config written",
            "repository state recorded",
        ],
    ),
    ("R-S0-count", ["submission count is 0 (posts)"]),
    (
        "R-S1",
        [
            "state READY_IMPLEMENTER",
            "schema_version 2",
            "model_turns_used 0",
            "turn_attempts 0",
            "no in_flight_turn",
            "no recovery record",
        ],
    ),
    ("R-S1-count", ["submission count is 0 (posts, S1)"]),
    (
        "R-S2-crash",
        [
            "child tree killed",
            "live in_flight_turn present",
            "attempt prompt_sha256 matches",
            "run document state READY_IMPLEMENTER",
        ],
    ),
    ("R-S2-post", ["exactly one submitted POST for the identity"]),
    ("R-S2-probe", ["exactly one ownership-probe GET recorded"]),
    ("R-S2-count", ["submission count agrees (posts == message=process)"]),
    (
        "R-S3",
        [
            "get_run shows the live intent",
            "run_implementer refused with orchestration_recovery_required",
            "run_reviewer refused with orchestration_recovery_required",
            "decide_run refused with orchestration_recovery_required",
            "run document byte-identical",
            "submission count unchanged",
        ],
    ),
    (
        "R-S4",
        [
            "manifest identical (no durable write)",
            "ledger outcome is exactly_one_match or evidence_gap",
            "remote outcome evidence_gap",
            "adoption unavailable",
            "checklist has the nine items",
            "blockers name the disabled adoption",
            "submission count unchanged",
        ],
    ),
    (
        "R-S5",
        [
            "state BLOCKED",
            "terminal",
            "legal_next_actions empty",
            "blocked_reason equals recovery_reason",
            "evidence digest recomputes from its canonical fields",
            "frozen attempt booked exactly once",
            "last_transition action recover",
        ],
    ),
    (
        "R-S6",
        [
            "run_implementer refused with orchestration_invalid_transition",
            "resolve_recovery refused with orchestration_recovery_already_resolved",
            "reconcile_run refused with orchestration_recovery_unsupported",
            "run document byte-identical",
        ],
    ),
    (
        "R-S7",
        [
            "sentinel absent from every file under <ws>/.devrelay",
            "run document contains no prompt text",
            "no credential material under <ws>/.devrelay",
        ],
    ),
    (
        "R-S8",
        [
            "implementer session deleted",
            "reviewer session deleted",
            "dedicated instance stopped",
            "dedicated port is free",
            "repository head unchanged",
            "no MCP child process survives",
            "disposable workspace removed",
        ],
    ),
]

PINNED_DROP = ("PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP")


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def child_env() -> dict[str, str]:
    """Environment for a child MCP server: candidate checkout pinned."""
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith("DEVRELAY_") and key not in PINNED_DROP
    }
    env["PYTHONPATH"] = str(SRC)
    env["PYTHONIOENCODING"] = "utf-8"
    return env


CRASH_CHILD = '''\
import asyncio
import json
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def main(ws, run_id, prompt):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    async def run():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "devrelay", "mcp", "serve", "--workspace", ws],
            cwd=ws,
            env={
                key: value
                for key, value in __import__("os").environ.items()
                if not key.startswith("DEVRELAY_")
            },
        )
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "devrelay_run_implementer",
                    {"run_id": run_id, "prompt": prompt},
                )
                payload = result.structured_content or {}
                print("CHILD_CALL_RETURNED", json.dumps(payload)[:400], flush=True)

    asyncio.run(run())


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
'''


class Checker:
    """Collects PASS/FAIL criteria for one phase, keeping measured values."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.items: list[dict[str, Any]] = []

    def check(self, label: str, condition: bool, measured: Any = None) -> bool:
        item = {"label": label, "pass": bool(condition), "measured": measured}
        self.items.append(item)
        status = "PASS" if condition else "FAIL"
        print(f"  [{status}] {self.name}: {label} -> {measured!r}", flush=True)
        return bool(condition)

    def equal(self, label: str, actual: Any, expected: Any) -> bool:
        return self.check(label, actual == expected, {"actual": actual, "expected": expected})

    @property
    def passed(self) -> bool:
        return all(item["pass"] for item in self.items)

    def to_dict(self) -> dict[str, Any]:
        return {"phase": self.name, "pass": self.passed, "criteria": self.items}


class Smoke:
    def __init__(self) -> None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.base_dir = Path(os.environ.get("TEMP", tempfile_fallback())) / f"devrelay-recovery-smoke-{stamp}"
        self.ws = self.base_dir / "ws"
        self.evidence = self.base_dir / "evidence"
        self.port: int = 0
        self.server: subprocess.Popen[bytes] | None = None
        self.server_log = self.evidence / "server.log"
        self.server_handle = None
        self.impl_session = ""
        self.rev_session = ""
        self.run_id = ""
        self.phases: list[Checker] = []
        self.notes: dict[str, Any] = {}
        self.repo_before: dict[str, Any] = {}

    # -- infrastructure ---------------------------------------------------
    def setup(self) -> None:
        self.ws.mkdir(parents=True, exist_ok=True)
        self.evidence.mkdir(parents=True, exist_ok=True)
        self.counts: dict[str, Any] = {}
        (self.evidence / "crash_child.py").write_text(CRASH_CHILD, encoding="utf-8")
        print(f"smoke: workspace {self.ws}", flush=True)
        print(f"smoke: evidence  {self.evidence}", flush=True)

    def free_port(self) -> int:
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

    def http(self, method: str, path: str, body: Any = None, timeout: float = 60.0) -> Any:
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}{path}", data=data, method=method)
        if data is not None:
            request.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return json.loads(raw) if raw else None

    def start_server(self) -> None:
        self.port = self.free_port()
        self.server_handle = self.server_log.open("w", encoding="utf-8")
        self.server = subprocess.Popen(
            [
                str(OPENCODE),
                "serve",
                "--port",
                str(self.port),
                "--hostname",
                "127.0.0.1",
                "--print-logs",
                "--log-level",
                "INFO",
            ],
            cwd=str(self.ws),
            stdout=self.server_handle,
            stderr=subprocess.STDOUT,
        )
        deadline = time.monotonic() + 60.0
        while time.monotonic() < deadline:
            try:
                if self.http("GET", "/session", timeout=3.0) is not None:
                    print(f"smoke: instance up on 127.0.0.1:{self.port}", flush=True)
                    return
            except Exception:  # noqa: BLE001 - not up yet
                time.sleep(0.3)
        raise RuntimeError("the dedicated OpenCode instance did not answer GET /session in 60 s")

    def stop_server(self) -> None:
        if self.server is not None and self.server.poll() is None:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(self.server.pid)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            try:
                self.server.wait(timeout=20)
            except subprocess.TimeoutExpired:
                pass
        if self.server_handle is not None:
            self.server_handle.close()
            self.server_handle = None

    def server_log_text(self) -> str:
        try:
            return self.server_log.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""

    def log_process_lines(self) -> list[str]:
        session = self.impl_session
        if not session:
            return []
        return [
            line
            for line in self.server_log_text().splitlines()
            if "message=process" in line and f"session.id={session}" in line
        ]

    def ledger_dir(self) -> Path:
        return self.ws / ".devrelay" / "opencode" / "calls"

    def ledger_records(self) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for path in sorted(self.ledger_dir().glob("*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001 - a live/torn record is reported as such
                records.append({"file": path.name, "unreadable": True})
                continue
            if isinstance(payload, dict):
                payload["_file"] = path.name
                records.append(payload)
        return records

    def ledger_sequence(self) -> Any:
        path = self.ws / ".devrelay" / "opencode" / "sequence.json"
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return None

    def send_prompt_records(self) -> list[dict[str, Any]]:
        return [
            record
            for record in self.ledger_records()
            if record.get("operation") == "send_prompt"
            and record.get("session_id") == self.impl_session
        ]

    def submitted_posts(self) -> list[dict[str, Any]]:
        """Model-bearing submissions: POST records carrying the prompt digest."""
        return [
            record
            for record in self.send_prompt_records()
            if record.get("method") == "POST" and record.get("prompt_sha256")
        ]

    def probe_gets(self) -> list[dict[str, Any]]:
        """The non-submitting ownership probes (`send_prompt` GET, no digest)."""
        return [
            record
            for record in self.send_prompt_records()
            if record.get("method") == "GET" and not record.get("prompt_sha256")
        ]

    def submission_count(self, *, settle: bool = True) -> dict[str, Any]:
        """Posts, probe GETs and server-log lines: the oracle R2 count view."""
        attempts = 3 if settle else 1
        measured: dict[str, Any] = {}
        for attempt in range(attempts):
            records = self.send_prompt_records()
            posts = self.submitted_posts()
            probes = self.probe_gets()
            lines = self.log_process_lines()
            measured = {
                "ledger_submission_posts": len(posts),
                "ledger_probe_gets": len(probes),
                "ledger_send_prompt_records": len(records),
                "log_message_process": len(lines),
                "ledger_call_ids": [record.get("call_id") for record in records],
                "post_call_ids": [record.get("call_id") for record in posts],
                "probe_call_ids": [record.get("call_id") for record in probes],
                "sequence": self.ledger_sequence(),
            }
            if len(posts) == len(lines) or attempt == attempts - 1:
                break
            time.sleep(1.0)
        measured["agree"] = measured["ledger_submission_posts"] == measured["log_message_process"]
        return measured

    def run_doc_path(self) -> Path:
        return self.ws / ".devrelay" / "orchestration" / "runs" / f"{self.run_id}.json"

    def run_doc(self) -> dict[str, Any]:
        return json.loads(self.run_doc_path().read_text(encoding="utf-8"))

    def run_doc_hash(self) -> str:
        return hashlib.sha256(self.run_doc_path().read_bytes()).hexdigest()

    def tree_manifest(self) -> dict[str, str]:
        root = self.ws / ".devrelay"
        manifest: dict[str, str] = {}
        for path in sorted(root.rglob("*")):
            if path.is_file():
                manifest[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        return manifest

    def repo_state(self) -> dict[str, Any]:
        def git(*args: str) -> str:
            result = subprocess.run(
                ["git", "-C", str(REPO), *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=60,
            )
            return result.stdout.strip()

        return {
            "head": git("rev-parse", "HEAD"),
            "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "porcelain": git("status", "--porcelain"),
        }

    # -- MCP surface ------------------------------------------------------
    def mcp_calls(self, calls: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
        """Run sequential tool calls on one fresh MCP stdio surface."""
        return asyncio.run(self._mcp_calls(calls))

    async def _mcp_calls(self, calls: list[tuple[str, dict[str, Any]]]) -> list[dict[str, Any]]:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client

        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "devrelay", "mcp", "serve", "--workspace", str(self.ws)],
            cwd=str(self.ws),
            env=child_env(),
        )
        envelopes: list[dict[str, Any]] = []
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                for tool, arguments in calls:
                    result = await asyncio.wait_for(
                        session.call_tool(tool, arguments), timeout=240.0
                    )
                    envelopes.append(
                        {
                            "tool": tool,
                            "isError": bool(result.is_error),
                            "envelope": result.structured_content,
                        }
                    )
        return envelopes

    # -- phases -----------------------------------------------------------
    def phase_s0(self) -> Checker:
        check = Checker("S0 preflight")
        self.start_server()
        check.check("dedicated instance answers GET /session", True, f"127.0.0.1:{self.port}")
        self.impl_session = self.http("POST", "/session", {})["id"]
        self.rev_session = self.http("POST", "/session", {})["id"]
        check.check(
            "two prompt-free sessions created, distinct",
            bool(self.impl_session) and bool(self.rev_session) and self.impl_session != self.rev_session,
            {"implementer": self.impl_session, "reviewer": self.rev_session},
        )
        check.check(
            "remote confirms both sessions exist",
            {s["id"] for s in self.http("GET", "/session")} >= {self.impl_session, self.rev_session},
            None,
        )
        self.write_workspace_config()
        check.check(
            "disposable workspace config written",
            (self.ws / ".devrelay" / "config.yaml").is_file()
            and (self.ws / ".devrelay" / "state.json").is_file(),
            {"ws": str(self.ws)},
        )
        self.repo_before = self.repo_state()
        check.check("repository state recorded", bool(self.repo_before["head"]), self.repo_before)
        submission = self.submission_count(settle=False)
        self.counts["S0"] = submission
        check.check(
            "submission count is 0 (posts)",
            submission["ledger_submission_posts"] == 0
            and submission["log_message_process"] == 0
            and submission["ledger_probe_gets"] == 0,
            submission,
        )
        write_json(self.evidence / "phase-S0.json", check.to_dict() | {"repo_before": self.repo_before, "submission": submission})
        return check

    def write_workspace_config(self) -> None:
        import yaml  # the package's own dependency, used only to write the fixture

        (self.ws / ".devrelay").mkdir(parents=True, exist_ok=True)
        source = REPO / ".devrelay" / "config.yaml"
        data = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
        opencode = data.setdefault("opencode", {})
        opencode["base_url"] = f"http://127.0.0.1:{self.port}"
        opencode["workspace"] = ""
        opencode["default_session"] = ""
        opencode["agent"] = ""
        opencode["model"] = ""
        opencode["poll_interval_seconds"] = 0.5
        opencode["idle_timeout_seconds"] = 120
        data["roles"] = {
            "implementer": {"model": IMPL_ROUTE, "agent": None},
            "reviewer": {"model": REV_ROUTE, "agent": None},
        }
        (self.ws / ".devrelay" / "config.yaml").write_text(
            yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
        )
        (self.ws / ".devrelay" / "state.json").write_text("{}", encoding="utf-8")

    def phase_s1(self) -> Checker:
        check = Checker("S1 baseline")
        envelopes = self.mcp_calls(
            [
                (
                    "devrelay_start_run",
                    {
                        "implementer_session_id": self.impl_session,
                        "reviewer_session_id": self.rev_session,
                        "max_cycles": 1,
                    },
                )
            ]
        )
        envelope = envelopes[0]
        dump(check, "start_run envelope", envelope)
        data = (envelope.get("envelope") or {}).get("data") or {}
        check.check("start_run ok", envelope["isError"] is False and (envelope.get("envelope") or {}).get("ok") is True, data.get("run_id"))
        self.run_id = str(data.get("run_id", ""))
        check.check("run id recorded", bool(self.run_id), self.run_id)
        check.equal("state READY_IMPLEMENTER", data.get("state"), "READY_IMPLEMENTER")
        check.equal("schema_version 2", data.get("schema_version"), 2)
        check.equal("model_turns_used 0", data.get("model_turns_used"), 0)
        check.equal("turn_attempts 0", data.get("turn_attempts"), 0)
        check.equal("no in_flight_turn", data.get("in_flight"), False)
        check.equal("no recovery record", data.get("recovery"), None)
        submission = self.submission_count(settle=False)
        self.counts["S1"] = submission
        check.check(
            "submission count is 0 (posts, S1)",
            submission["ledger_submission_posts"] == 0
            and submission["log_message_process"] == 0,
            submission,
        )
        write_json(self.evidence / "phase-S1.json", check.to_dict() | {"envelope": envelope})
        return check

    def phase_s2(self) -> Checker:
        check = Checker("S2 real crash")
        started = time.monotonic()
        child_out = (self.evidence / "crash-child.out").open("w", encoding="utf-8")
        child_err = (self.evidence / "crash-child.err").open("w", encoding="utf-8")
        child = subprocess.Popen(
            [sys.executable, str(self.evidence / "crash_child.py"), str(self.ws), self.run_id, PROMPT],
            cwd=str(self.ws),
            env=child_env(),
            stdout=child_out,
            stderr=child_err,
        )
        print(f"smoke: crash child pid {child.pid}", flush=True)
        try:
            record: dict[str, Any] | None = None
            while time.monotonic() - started < S2_DEADLINE_S:
                candidates = [
                    entry
                    for entry in self.send_prompt_records()
                    if entry.get("prompt_sha256") == PROMPT_SHA256
                ]
                if candidates:
                    record = candidates[0]
                    break
                if child.poll() is not None:
                    break
                time.sleep(0.1)
            observed_at = time.monotonic() - started
            check.check(
                "a send_prompt ledger record for the oracle prompt appeared",
                record is not None,
                {"record": record, "after_s": round(observed_at, 2)},
            )
            if record is None:
                return check
            ledger_call_id = record.get("call_id")
            ledger_state = record.get("state")
            time.sleep(KILL_DELAY_S)
            killed = subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(child.pid)],
                capture_output=True,
                text=True,
                timeout=30,
            )
            check.check("child tree killed", child.wait(timeout=60) is not None, {"taskkill": killed.returncode})
            child_out.close()
            child_err.close()
            time.sleep(1.0)
            doc = self.run_doc()
            attempt = doc.get("in_flight_turn")
            check.check("live in_flight_turn present", isinstance(attempt, dict), attempt)
            if isinstance(attempt, dict):
                check.equal("attempt role implementer", attempt.get("role"), "implementer")
                check.equal("attempt cycle 1", attempt.get("cycle"), 1)
                check.equal("attempt prompt_sha256 matches", attempt.get("prompt_sha256"), PROMPT_SHA256)
                check.equal("attempt prompt_chars matches", attempt.get("prompt_chars"), len(PROMPT))
            check.equal("run document schema_version 2", doc.get("schema_version"), 2)
            check.equal("run document state READY_IMPLEMENTER", doc.get("state"), "READY_IMPLEMENTER")
            records = [entry for entry in self.send_prompt_records() if entry.get("prompt_sha256") == PROMPT_SHA256]
            posts = [entry for entry in self.submitted_posts() if entry.get("prompt_sha256") == PROMPT_SHA256]
            probes = self.probe_gets()
            check.equal("exactly one submitted POST for the identity", len(posts), 1)
            check.equal("exactly one ownership-probe GET recorded", len(probes), 1)
            if posts:
                check.check(
                    "ledger record is not settled (submission outcome unknown)",
                    posts[0].get("state") == "ISSUED" or posts[0].get("submission_uncertain") is True,
                    {"state": posts[0].get("state"), "submission_uncertain": posts[0].get("submission_uncertain")},
                )
            lines = self.log_process_lines()
            check.equal(
                "submission count agrees (posts == message=process)",
                (len(posts), len(lines)),
                (1, 1),
            )
            lines = self.log_process_lines()
            check.check("instance accepted the submission (message=process)", len(lines) >= 1, len(lines))
            check.check("run document contains no prompt text", PROMPT not in json.dumps(doc), None)
            remote_messages = self.http("GET", f"/session/{self.impl_session}/message")
            assistant = [
                message
                for message in remote_messages
                if (message.get("info") or {}).get("role") == "assistant"
            ]
            self.notes["remote_assistant_at_kill"] = len(assistant)
            self.counts["S2"] = self.submission_count()
            self.notes["crash"] = {
                "ledger_call_id": ledger_call_id,
                "ledger_state": ledger_state,
                "kill_after_s": round(observed_at + KILL_DELAY_S, 2),
                "remote_assistant_messages_at_kill": len(assistant),
                "child_exit": child.returncode,
                "taskkill_rc": killed.returncode,
            }
            write_json(
                self.evidence / "phase-S2.json",
                check.to_dict()
                | {
                    "run_document": doc,
                    "ledger_records": records,
                    "remote_message_count": len(remote_messages),
                    "remote_roles": [
                        (message.get("info") or {}).get("role") for message in remote_messages
                    ],
                },
            )
            return check
        finally:
            child_out.close()
            child_err.close()

    def phase_s3(self) -> Checker:
        check = Checker("S3 refusal on a fresh surface")
        before_hash = self.run_doc_hash()
        before_count = self.submission_count()
        envelopes = self.mcp_calls(
            [
                ("devrelay_get_run", {"run_id": self.run_id}),
                ("devrelay_run_implementer", {"run_id": self.run_id, "prompt": "S3 must refuse this prompt"}),
                ("devrelay_run_reviewer", {"run_id": self.run_id, "prompt": "S3 must refuse this prompt"}),
                ("devrelay_decide_run", {"run_id": self.run_id, "decision": "complete"}),
            ]
        )
        get_envelope = envelopes[0]["envelope"] or {}
        get_data = get_envelope.get("data") or {}
        check.check("get_run ok", envelopes[0]["isError"] is False and get_envelope.get("ok") is True, get_data.get("state"))
        check.equal("get_run shows the live intent", get_data.get("in_flight"), True)
        check.equal("get_run shows READY_IMPLEMENTER", get_data.get("state"), "READY_IMPLEMENTER")
        check.equal("legal_next_actions names the resolution", get_data.get("legal_next_actions"), ["devrelay_resolve_recovery"])
        for index, tool in ((1, "run_implementer"), (2, "run_reviewer"), (3, "decide_run")):
            envelope = envelopes[index]["envelope"] or {}
            check.check(
                f"{tool} refused with orchestration_recovery_required",
                envelopes[index]["isError"] is True
                and (envelope.get("error") or {}).get("type") == "orchestration_recovery_required",
                envelope.get("error"),
            )
        check.equal("run document byte-identical", self.run_doc_hash(), before_hash)
        after_count = self.submission_count()
        self.counts["S3"] = {"before": before_count, "after": after_count}
        check.equal("submission count unchanged", after_count, before_count)
        write_json(self.evidence / "phase-S3.json", check.to_dict() | {"envelopes": envelopes})
        return check

    def phase_s4(self) -> Checker:
        check = Checker("S4 reconcile is read-only")
        manifest_before = self.tree_manifest()
        count_before = self.submission_count()
        envelopes = self.mcp_calls([("devrelay_reconcile_run", {"run_id": self.run_id})])
        envelope = envelopes[0]["envelope"] or {}
        report = envelope.get("data") or {}
        manifest_after = self.tree_manifest()
        check.check("reconcile ok", envelopes[0]["isError"] is False and envelope.get("ok") is True, report.get("run_id"))
        check.check("manifest identical (no durable write)", manifest_after == manifest_before, diff_manifest(manifest_before, manifest_after))
        after_count = self.submission_count()
        self.counts["S4"] = {"before": count_before, "after": after_count}
        check.equal("submission count unchanged", after_count, count_before)
        check.equal("recoverable", report.get("recoverable"), True)
        check.equal("v1_frozen", report.get("v1_frozen"), False)
        check.equal("state READY_IMPLEMENTER", report.get("state"), "READY_IMPLEMENTER")
        attempt = report.get("attempt") or {}
        check.equal("attempt role implementer", attempt.get("role"), "implementer")
        check.equal("attempt cycle 1", attempt.get("cycle"), 1)
        check.equal("attempt prompt_sha256 matches", attempt.get("prompt_sha256"), PROMPT_SHA256)
        ledger = report.get("ledger") or {}
        check.check(
            "ledger outcome is exactly_one_match or evidence_gap",
            ledger.get("outcome") in {"exactly_one_match", "evidence_gap"},
            ledger.get("outcome"),
        )
        if ledger.get("outcome") == "exactly_one_match":
            check.check("attributed call_id present", bool(ledger.get("call_id")), ledger.get("call_id"))
        else:
            check.check("evidence gap has a reason", bool(ledger.get("gap_reason")), ledger.get("gap_reason"))
        if ledger.get("interval_proven") is True:
            check.check(
                "proven interval carries floor and ceiling",
                bool(ledger.get("floor")) and bool(ledger.get("ceiling")),
                {"floor": ledger.get("floor"), "ceiling": ledger.get("ceiling")},
            )
        remote = report.get("remote") or {}
        check.equal("remote outcome evidence_gap", remote.get("outcome"), "evidence_gap")
        check.check(
            "remote gap reason says the local surface reads no session history",
            "no session history" in str(remote.get("gap_reason", "")),
            remote.get("gap_reason"),
        )
        check.equal("adoption unavailable", (report.get("adoption") or {}).get("available"), False)
        check.equal("no submission by recovery", (report.get("submission") or {}).get("submitted_by_recovery"), False)
        expected_items = [
            "document",
            "attempt identity",
            "ledger attribution",
            "ledger settlement",
            "remote correlation",
            "route stability",
            "resolution state",
            "adoption capability",
            "platform proofs",
        ]
        checklist = report.get("checklist") or []
        check.equal("checklist has the nine items", [entry.get("item") for entry in checklist], expected_items)
        check.check(
            "every checklist status is pass/fail/unknown",
            all(entry.get("status") in {"pass", "fail", "unknown"} for entry in checklist),
            [(entry.get("item"), entry.get("status")) for entry in checklist],
        )
        blockers = report.get("blockers") or []
        check.check("blockers are non-empty", bool(blockers), blockers)
        check.check(
            "blockers name the disabled adoption",
            any("adoption is disabled" in str(blocker) for blocker in blockers),
            blockers,
        )
        write_json(
            self.evidence / "phase-S4.json",
            check.to_dict()
            | {
                "manifest_before_count": len(manifest_before),
                "manifest_after_count": len(manifest_after),
                "report": report,
            },
        )
        return check

    def phase_s5(self) -> Checker:
        check = Checker("S5 mark_unrecoverable")
        count_before = self.submission_count()
        hash_before = self.run_doc_hash()
        envelopes = self.mcp_calls(
            [("devrelay_resolve_recovery", {"run_id": self.run_id, "resolution": "mark_unrecoverable"})]
        )
        envelope = envelopes[0]["envelope"] or {}
        data = envelope.get("data") or {}
        check.check("resolve ok", envelopes[0]["isError"] is False and envelope.get("ok") is True, data.get("resolution"))
        check.equal("state BLOCKED", data.get("state"), "BLOCKED")
        check.equal("terminal", data.get("terminal"), True)
        check.equal("legal_next_actions empty", data.get("legal_next_actions"), [])
        reason = data.get("recovery_reason")
        check.check(
            "recovery_reason is one of the three legal reasons",
            reason in {"submission_uncertain", "reply_pending", "turn_interrupted"},
            reason,
        )
        check.equal("blocked_reason equals recovery_reason", data.get("blocked_reason"), reason)
        recovery = data.get("recovery") or {}
        check.equal("resolution mark_unrecoverable", recovery.get("resolution"), "mark_unrecoverable")
        check.check("resolved_at non-empty", bool(recovery.get("resolved_at")), recovery.get("resolved_at"))
        check.check("run document changed once", self.run_doc_hash() != hash_before, {"before": hash_before, "after": self.run_doc_hash()})
        check.check(
            "no temp residue next to the run document",
            [path.name for path in self.run_doc_path().parent.glob("*.tmp")] == [],
            None,
        )
        evidence = recovery.get("evidence") or {}
        digest_ok, digest_detail = verify_digest(evidence)
        check.check("evidence digest recomputes from its canonical fields", digest_ok, digest_detail)
        attempt = recovery.get("attempt") or {}
        check.equal("frozen attempt outcome blocked", attempt.get("outcome"), "blocked")
        check.equal("frozen attempt blocked for the recovery reason", attempt.get("blocked_reason"), reason)
        history = [entry for entry in data.get("implementer_turns") or [] if entry.get("cycle") == 1]
        check.check("frozen attempt booked exactly once", len(history) == 1, len(history))
        transition = data.get("last_transition") or {}
        check.equal("last_transition action recover", transition.get("action"), "recover")
        check.equal("last_transition previous_state RECOVERY_REQUIRED", transition.get("previous_state"), "RECOVERY_REQUIRED")
        check.equal("last_transition next_state BLOCKED", transition.get("next_state"), "BLOCKED")
        after_count = self.submission_count()
        self.counts["S5"] = {"before": count_before, "after": after_count}
        check.equal("submission count unchanged", after_count, count_before)
        write_json(self.evidence / "phase-S5.json", check.to_dict() | {"envelope": envelope, "run_document": self.run_doc()})
        return check

    def phase_s6(self) -> Checker:
        check = Checker("S6 terminality")
        hash_before = self.run_doc_hash()
        count_before = self.submission_count()
        envelopes = self.mcp_calls(
            [
                ("devrelay_run_implementer", {"run_id": self.run_id, "prompt": "S6 must refuse this prompt"}),
                ("devrelay_run_reviewer", {"run_id": self.run_id, "prompt": "S6 must refuse this prompt"}),
                ("devrelay_decide_run", {"run_id": self.run_id, "decision": "complete"}),
                ("devrelay_resolve_recovery", {"run_id": self.run_id, "resolution": "mark_unrecoverable"}),
                ("devrelay_reconcile_run", {"run_id": self.run_id}),
            ]
        )
        expected = [
            "orchestration_invalid_transition",
            "orchestration_invalid_transition",
            "orchestration_invalid_transition",
            "orchestration_recovery_already_resolved",
            "orchestration_recovery_unsupported",
        ]
        for envelope, error_type in zip(envelopes, expected):
            payload = envelope["envelope"] or {}
            check.check(
                f"{envelope['tool']} refused with {error_type}",
                envelope["isError"] is True and (payload.get("error") or {}).get("type") == error_type,
                payload.get("error"),
            )
        check.equal("run document byte-identical", self.run_doc_hash(), hash_before)
        after_count = self.submission_count()
        self.counts["S6"] = {"before": count_before, "after": after_count}
        check.equal("submission count unchanged", after_count, count_before)
        write_json(self.evidence / "phase-S6.json", check.to_dict() | {"envelopes": envelopes})
        return check

    def phase_s7(self) -> Checker:
        check = Checker("S7 no adoption, no persistence")
        remote_messages = self.http("GET", f"/session/{self.impl_session}/message")
        assistant_texts = [
            " ".join(
                str(part.get("text", ""))
                for part in message.get("parts") or []
                if isinstance(part, dict) and part.get("type") == "text"
            )
            for message in remote_messages
            if (message.get("info") or {}).get("role") == "assistant"
        ]
        assistant_texts = [text for text in assistant_texts if text.strip()]
        self.notes["remote_reply_present"] = bool(assistant_texts)
        scan_terms = [SENTINEL]
        if assistant_texts:
            longest = max(assistant_texts, key=len)
            scan_terms.append(longest[:400])
        else:
            scan_terms.append("unavailable: no assistant message was produced before the crash")
        hits: dict[str, list[str]] = {}
        secret_hits: dict[str, list[str]] = {}
        secret_needles = ["Authorization", "Bearer ", "sk-", "api_key", "API_KEY"]
        token = os.environ.get("DEVRELAY_OPENCODE_TOKEN", "")
        if token:
            secret_needles.append(token)
        for path in sorted((self.ws / ".devrelay").rglob("*")):
            if not path.is_file():
                continue
            try:
                raw = path.read_bytes().decode("utf-8", errors="replace")
            except OSError:
                continue
            lowercase = raw.lower()
            for term in scan_terms:
                if term and term.lower() in lowercase:
                    hits.setdefault(term, []).append(path.name)
            for needle in secret_needles:
                if needle and needle in raw:
                    secret_hits.setdefault(needle, []).append(path.name)
        doc_raw = self.run_doc_path().read_text(encoding="utf-8", errors="replace")
        check.check(
            "sentinel absent from every file under <ws>/.devrelay",
            not hits.get(SENTINEL),
            hits.get(SENTINEL),
        )
        if assistant_texts:
            check.check(
                "remote reply text absent from every file under <ws>/.devrelay",
                not hits.get(assistant_texts and max(assistant_texts, key=len)[:400]),
                hits.get(max(assistant_texts, key=len)[:400]),
            )
        check.check("run document contains no prompt text", PROMPT not in doc_raw, None)
        check.check("no credential material under <ws>/.devrelay", not secret_hits, secret_hits)
        write_json(
            self.evidence / "phase-S7.json",
            check.to_dict() | {"assistant_messages": len(assistant_texts), "hits": hits, "secret_hits": secret_hits},
        )
        return check

    def phase_s8(self) -> Checker:
        check = Checker("S8 containment and cleanup")
        delete_impl = self.delete_session(self.impl_session)
        delete_rev = self.delete_session(self.rev_session)
        check.check("implementer session deleted", delete_impl[0] == 200, delete_impl)
        check.check("reviewer session deleted", delete_rev[0] == 200, delete_rev)
        remaining = {session["id"] for session in self.http("GET", "/session")}
        check.check("no disposable session survives", not ({self.impl_session, self.rev_session} & remaining), sorted(remaining)[:5])
        self.stop_server()
        check.check("dedicated instance stopped", self.server is None or self.server.poll() is not None, None)
        free = True
        sock = socket.socket()
        try:
            sock.bind(("127.0.0.1", self.port))
        except OSError:
            free = False
        finally:
            sock.close()
        check.check("dedicated port is free", free, self.port)
        repo_after = self.repo_state()
        check.equal("repository head unchanged", repo_after["head"], self.repo_before["head"])
        check.equal("repository branch unchanged", repo_after["branch"], self.repo_before["branch"])
        check.equal("repository porcelain unchanged", repo_after["porcelain"], self.repo_before["porcelain"])
        self.counts["S8"] = count = self.submission_count()
        expected_posts = 0 if self.plumbing else 1
        check.check(
            "submission count is 1 (posts, S8)",
            count["ledger_submission_posts"] == expected_posts
            and count["log_message_process"] == expected_posts,
            count | {"expected_posts": expected_posts},
        )
        write_json(self.evidence / "repo-state.json", {"before": self.repo_before, "after": repo_after})
        children = self.mcp_children()
        check.check("no MCP child process survives", not children, children[:3])
        shutil.rmtree(self.ws, ignore_errors=True)
        check.check("disposable workspace removed", not self.ws.exists(), str(self.ws))
        write_json(self.evidence / "phase-S8.json", check.to_dict() | {"repo_before": self.repo_before, "repo_after": repo_after})
        return check

    def mcp_children(self) -> list[str]:
        """Python processes whose command line still names the disposable workspace."""
        try:
            probe = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
                    "Select-Object -ExpandProperty CommandLine",
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )
        except Exception:  # noqa: BLE001 - an unanswerable probe is recorded, not fatal
            return []
        return [line for line in probe.stdout.splitlines() if str(self.ws) in line]

    def delete_session(self, session_id: str) -> tuple[Any, Any]:
        result = self.http("DELETE", f"/session/{session_id}")
        if isinstance(result, tuple):
            return result
        return 200, result

    # -- oracle conformance ------------------------------------------------
    def conformance_entries(self) -> list[dict[str, Any]]:
        items = [item for phase in self.phases for item in phase.items]
        entries: list[dict[str, Any]] = []
        for rule, required in CONFORMANCE_RULES:
            criteria: list[dict[str, Any]] = []
            passed = True
            for label in required:
                hits = [item for item in items if label in item["label"]]
                if not hits:
                    passed = False
                    criteria.append({"label": label, "status": "missing"})
                    continue
                hit = hits[0]
                passed = passed and bool(hit["pass"])
                criteria.append({"label": hit["label"], "status": "pass" if hit["pass"] else "fail"})
            entries.append({"rule": rule, "pass": passed, "criteria": criteria})
        return entries

    def phase_conformance(self) -> Checker:
        check = Checker("R2 oracle conformance")
        entries = self.conformance_entries()
        for entry in entries:
            check.check(f"{entry['rule']} mapped to asserted criteria", entry["pass"], entry["criteria"])
        write_json(
            self.evidence / "oracle-conformance.json",
            {
                "oracle": str(ORACLE),
                "oracle_sha256": sha256_file(ORACLE),
                "driver": str(Path(__file__)),
                "driver_sha256": sha256_file(Path(__file__)),
                "rules": entries,
                "pass": all(entry["pass"] for entry in entries),
            },
        )
        return check

    # -- orchestration ----------------------------------------------------
    def plumbing_after_s1(self) -> Checker:
        """Pre-execution plumbing check: no model-bearing call is made."""
        check = Checker("PLUMBING get_run")
        envelopes = self.mcp_calls([("devrelay_get_run", {"run_id": self.run_id})])
        envelope = envelopes[0]["envelope"] or {}
        data = envelope.get("data") or {}
        check.check("get_run ok", envelopes[0]["isError"] is False and envelope.get("ok") is True, data.get("state"))
        check.equal("state READY_IMPLEMENTER", data.get("state"), "READY_IMPLEMENTER")
        check.equal("no in_flight_turn", data.get("in_flight"), False)
        check.check(
            "legal_next_actions advertises the implementer turn",
            "devrelay_run_implementer" in (data.get("legal_next_actions") or []),
            data.get("legal_next_actions"),
        )
        return check

    def run(self, *, plumbing: bool = False) -> int:
        self.setup()
        log_handle = (self.evidence / "driver.log").open("w", encoding="utf-8")
        original_out, original_err = sys.stdout, sys.stderr
        sys.stdout = Tee(original_out, log_handle)
        sys.stderr = Tee(original_err, log_handle)
        try:
            return self._run(plumbing=plumbing)
        finally:
            sys.stdout, sys.stderr = original_out, original_err
            log_handle.close()

    def _run(self, *, plumbing: bool = False) -> int:
        ok = True
        self.plumbing = plumbing
        verdict: dict[str, Any] = {
            "smoke": (
                "V0.3-E driver plumbing check (no model-bearing call)"
                if plumbing
                else "V0.3-E real crash-and-recovery smoke"
            ),
            "started_at": utcnow(),
            "workspace": str(self.ws),
            "evidence": str(self.evidence),
            "prompt_sha256": PROMPT_SHA256,
            "prompt_chars": len(PROMPT),
            "sentinel": SENTINEL,
            "routes": {"implementer": IMPL_ROUTE, "reviewer": REV_ROUTE},
            "oracle": str(ORACLE),
            "oracle_sha256": sha256_file(ORACLE),
            "driver_sha256": sha256_file(Path(__file__)),
            "python": sys.version.split()[0],
            "phases": [],
        }
        steps = [
            ("S0", self.phase_s0),
            ("S1", self.phase_s1),
        ]
        if plumbing:
            steps.append(("PLUMBING", self.plumbing_after_s1))
        else:
            steps.extend(
                [
                    ("S2", self.phase_s2),
                    ("S3", self.phase_s3),
                    ("S4", self.phase_s4),
                    ("S5", self.phase_s5),
                    ("S6", self.phase_s6),
                    ("S7", self.phase_s7),
                ]
            )
        steps.append(("S8", self.phase_s8))
        if not plumbing:
            steps.append(("CONFORMANCE", self.phase_conformance))
        try:
            for name, step in steps:
                print(f"\n=== {name} ===", flush=True)
                try:
                    check = step()
                except Exception as exc:  # noqa: BLE001 - a driver error is a FAIL, recorded
                    print(f"[FAIL] {name} raised {type(exc).__name__}: {exc}", flush=True)
                    traceback.print_exc()
                    check = Checker(f"{name} (driver error)")
                    check.check("phase did not abort the driver", False, f"{type(exc).__name__}: {exc}")
                    verdict["phases"].append(check.to_dict())
                    ok = False
                    break
                self.phases.append(check)
                verdict["phases"].append(check.to_dict())
                ok = ok and check.passed
                if not check.passed:
                    break
        finally:
            try:
                if self.server is not None and self.server.poll() is None:
                    self.stop_server()
            finally:
                if self.server_handle is not None:
                    self.server_handle.close()
        verdict["finished_at"] = utcnow()
        verdict["notes"] = self.notes
        verdict["ok"] = ok and all(phase.passed for phase in self.phases)
        verdict["verdict"] = (
            "PASS — V0.3-E REAL CRASH-AND-RECOVERY SMOKE (R2)"
            if verdict["ok"]
            else "FAIL — see the first failing criterion above"
        )
        failed = next(
            (
                {"phase": phase["phase"], "criterion": next(item for item in phase["criteria"] if not item["pass"])}
                for phase in verdict["phases"]
                if not phase["pass"]
            ),
            None,
        )
        verdict["first_failure"] = failed
        try:
            final_count: Any = self.submission_count()
        except Exception as exc:  # noqa: BLE001 - the disposable workspace may already be gone
            final_count = f"{type(exc).__name__}: {exc}"
        write_json(self.evidence / "submission-count.json", {"phases": self.counts, "final": final_count})
        try:
            write_json(self.evidence / "repo-state.json", {"before": self.repo_before, "after": self.repo_state()})
        except Exception as exc:  # noqa: BLE001 - recorded only
            write_json(self.evidence / "repo-state.json", {"error": f"{type(exc).__name__}: {exc}"})
        write_json(
            self.evidence / ("plumbing.json" if plumbing else "smoke.json"), verdict
        )
        print("\n=== VERDICT ===")
        print(verdict["verdict"])
        if failed:
            print("first failure:", json.dumps(failed, indent=2, default=str)[:2000])
        print("evidence:", self.evidence)
        return 0 if verdict["ok"] else 1


def tempfile_fallback() -> str:
    return str(Path.home() / "AppData" / "Local" / "Temp")


class Tee:
    """Write to the console and to the evidence log at once."""

    def __init__(self, *streams: Any) -> None:
        self.streams = streams

    def write(self, data: str) -> int:
        for stream in self.streams:
            stream.write(data)
        return len(data)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()

    def fileno(self) -> int:
        return self.streams[0].fileno()

    def isatty(self) -> bool:
        return False

    def writable(self) -> bool:
        return True

    @property
    def encoding(self) -> str:
        return "utf-8"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, default=str, ensure_ascii=False), encoding="utf-8")


def dump(check: Checker, label: str, payload: Any) -> None:
    check.check(label, True, json.dumps(payload, default=str)[:400])


def diff_manifest(before: dict[str, str], after: dict[str, str]) -> dict[str, Any]:
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    changed = sorted(name for name in set(before) & set(after) if before[name] != after[name])
    return {"added": added, "removed": removed, "changed": changed}


def verify_digest(evidence: dict[str, Any]) -> tuple[bool, Any]:
    """Recompute the evidence digest with the package's own canonicalization."""
    try:
        if str(SRC) not in sys.path:
            sys.path.insert(0, str(SRC))
        from devrelay.orchestration.models import RecoveryEvidence

        model = RecoveryEvidence.model_validate(evidence)
        recomputed = model.compute_digest()
        return recomputed == model.evidence_sha256, {
            "stored": model.evidence_sha256,
            "recomputed": recomputed,
        }
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    plumbing = "--plumbing" in sys.argv[1:]
    smoke = Smoke()
    try:
        return smoke.run(plumbing=plumbing)
    except Exception as exc:  # noqa: BLE001 - infrastructure failure, recorded
        print(f"driver error: {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        try:
            write_json(
                smoke.evidence / "smoke.json",
                {
                    "smoke": "V0.3-E real crash-and-recovery smoke",
                    "ok": False,
                    "verdict": "FAIL — the driver itself could not run",
                    "error": f"{type(exc).__name__}: {exc}",
                    "evidence": str(smoke.evidence),
                },
            )
        except Exception:  # noqa: BLE001
            pass
        return 2


if __name__ == "__main__":
    sys.exit(main())

