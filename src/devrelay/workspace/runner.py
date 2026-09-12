"""Subprocess runner.

Every external command DevRelay executes goes through :class:`CommandRunner`.
It always uses ``shell=False`` (argv lists only), supports timeouts, stdin
streaming and structured results.

Two explicit I/O paths exist:

* :meth:`CommandRunner.run_bytes` - **byte-exact** binary I/O.  stdout/stderr
  are returned as raw ``bytes`` and stdin is written as raw ``bytes``.  No
  universal-newline translation and no implicit encode/decode happens, so this
  is the only path allowed for git binary-sensitive transport
  (``git diff --binary`` output, ``git apply --cached --binary -`` input).
* :meth:`CommandRunner.run` - the text convenience path, implemented ON TOP of
  the binary path (explicit decode, ``errors="replace"``).  Because decoding is
  explicit and newlines are never translated, captured text keeps the original
  bytes' line endings (LF stays LF, a bare CR stays a CR).
"""

from __future__ import annotations

import os
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Mapping, Sequence

from devrelay.models import BinaryCommandResult, CommandResult

# Grace period between terminate() and kill() after a timeout (v0.2-C).
_TERMINATE_GRACE_SECONDS = 5.0
_TRUNCATION_MARKER = b"\n[devrelay: output truncated]\n"


class _CappedStream:
    """Thread-safe head+tail accumulator with a hard byte cap.

    Readers always drain their pipe to EOF (so the child can never block on a
    full pipe) while only ``cap`` bytes are retained.
    """

    def __init__(self, cap: int) -> None:
        self.cap = max(0, int(cap))
        self._head_limit = self.cap // 2
        self._tail_limit = self.cap - self._head_limit
        self._head = bytearray()
        self._tail = bytearray()
        self.total = 0
        self._lock = threading.Lock()

    def feed(self, data: bytes) -> None:
        if not data:
            return
        with self._lock:
            self.total += len(data)
            room = self._head_limit - len(self._head)
            if room > 0:
                self._head.extend(data[:room])
                data = data[room:]
            if not data:
                return
            if len(data) >= self._tail_limit:
                self._tail = bytearray(data[-self._tail_limit:])
                return
            self._tail.extend(data)
            if len(self._tail) > self._tail_limit:
                del self._tail[: len(self._tail) - self._tail_limit]

    @property
    def truncated(self) -> bool:
        return self.total > self.cap

    def value(self) -> bytes:
        with self._lock:
            head = bytes(self._head)
            tail = bytes(self._tail)
            total = self.total
        if total <= self.cap:
            return head + tail
        return head + _TRUNCATION_MARKER + tail


def _reader_thread(stream, sink: _CappedStream) -> threading.Thread:
    def pump() -> None:
        try:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    break
                sink.feed(chunk)
        except (OSError, ValueError):  # pipe closed under us
            return
        finally:
            try:
                stream.close()
            except (OSError, ValueError):
                pass

    thread = threading.Thread(target=pump, daemon=True)
    thread.start()
    return thread


def _writer_thread(stream, data: bytes) -> threading.Thread:
    def pump() -> None:
        try:
            stream.write(data)
            stream.flush()
        except (OSError, ValueError, BrokenPipeError):
            pass
        finally:
            try:
                stream.close()
            except (OSError, ValueError):
                pass

    thread = threading.Thread(target=pump, daemon=True)
    thread.start()
    return thread


class CommandRunner:
    """Runs argv-based commands with a timeout, capturing output."""

    def __init__(
        self,
        env_overrides: Mapping[str, str] | None = None,
        shell_enabled: bool = False,
    ) -> None:
        self._env_overrides = dict(env_overrides or {})
        self._shell_enabled = shell_enabled  # must stay False in production

    @property
    def shell_enabled(self) -> bool:
        return self._shell_enabled

    def which(self, executable: str) -> str | None:
        return shutil.which(executable)

    # ------------------------------------------------------------------
    # byte-exact path (canonical implementation)
    # ------------------------------------------------------------------
    def run_bytes(
        self,
        argv: Sequence[str],
        cwd: str | Path | None = None,
        timeout_seconds: float = 900.0,
        input_bytes: bytes | None = None,
        env: Mapping[str, str] | None = None,
        env_remove: Sequence[str] | None = None,
        max_capture_bytes: int | None = None,
    ) -> BinaryCommandResult:
        """Run a command with byte-exact stdin/stdout (no newline translation).

        ``env_remove`` deletes the named variables from the child environment
        (case-insensitively on Windows); values are never read or logged.

        ``max_capture_bytes`` opts into bounded capture: both pipes are always
        drained by reader threads while only that many bytes (head + tail) are
        retained, so a runaway child can neither deadlock on a full pipe nor
        exhaust parent memory.
        """
        args = [str(item) for item in argv]
        if not args:
            raise ValueError("refusing to run an empty command")

        resolved_cwd = str(cwd) if cwd is not None else None
        run_env = os.environ.copy()
        run_env.update(self._env_overrides)
        if env:
            run_env.update({str(k): str(v) for k, v in env.items()})
        for name in env_remove or ():
            key = str(name)
            if key in run_env:
                del run_env[key]
            else:
                for existing in [k for k in run_env if k.lower() == key.lower()]:
                    del run_env[existing]

        started = time.monotonic()
        timed_out = False
        error: str | None = None
        exit_code: int | None = None
        stdout_bytes = b""
        stderr_bytes = b""
        stdout_total = 0
        stderr_total = 0
        stdout_truncated = False
        stderr_truncated = False

        try:
            proc = subprocess.Popen(
                args,
                cwd=resolved_cwd,
                env=run_env,
                shell=self._shell_enabled,
                stdin=subprocess.PIPE if input_bytes is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if max_capture_bytes is None:
                try:
                    stdout_bytes, stderr_bytes = proc.communicate(
                        input=input_bytes, timeout=timeout_seconds
                    )
                except subprocess.TimeoutExpired:
                    timed_out = True
                    self._terminate_then_kill(proc)
                    stdout_bytes, stderr_bytes = proc.communicate()
                    error = (
                        f"command timed out after {timeout_seconds:g}s: "
                        + " ".join(args[:4])
                    )
                stdout_total = len(stdout_bytes or b"")
                stderr_total = len(stderr_bytes or b"")
            else:
                # Bounded capture: always drain, retain head+tail only.
                cap = max(1024, int(max_capture_bytes))
                out_sink = _CappedStream(cap)
                err_sink = _CappedStream(cap)
                out_reader = _reader_thread(proc.stdout, out_sink)
                err_reader = _reader_thread(proc.stderr, err_sink)
                writer = (
                    _writer_thread(proc.stdin, input_bytes)
                    if input_bytes is not None and proc.stdin is not None
                    else None
                )
                try:
                    proc.wait(timeout=timeout_seconds)
                except subprocess.TimeoutExpired:
                    timed_out = True
                    self._terminate_then_kill(proc)
                    proc.wait()
                    error = (
                        f"command timed out after {timeout_seconds:g}s: "
                        + " ".join(args[:4])
                    )
                out_reader.join(timeout=30.0)
                err_reader.join(timeout=30.0)
                if writer is not None:
                    writer.join(timeout=30.0)
                stdout_bytes = out_sink.value()
                stderr_bytes = err_sink.value()
                stdout_total = out_sink.total
                stderr_total = err_sink.total
                stdout_truncated = out_sink.truncated
                stderr_truncated = err_sink.truncated
            exit_code = proc.returncode
        except FileNotFoundError as exc:
            error = f"executable not found: {exc.filename or args[0]}"
            exit_code = None
        except OSError as exc:
            error = f"failed to start command: {exc}"
            exit_code = None

        duration = time.monotonic() - started
        return BinaryCommandResult(
            command=args,
            cwd=resolved_cwd,
            exit_code=exit_code,
            stdout=stdout_bytes or b"",
            stderr=stderr_bytes or b"",
            duration_seconds=round(duration, 3),
            timed_out=timed_out,
            error=error,
            stdout_bytes_total=stdout_total,
            stderr_bytes_total=stderr_total,
            stdout_truncated=stdout_truncated,
            stderr_truncated=stderr_truncated,
        )

    @staticmethod
    def _terminate_then_kill(proc: subprocess.Popen) -> None:
        """Graceful terminate, then kill after a short grace period.

        Windows has no SIGTERM for console processes, so terminate() is already
        TerminateProcess there; the grace period only matters on POSIX.
        """
        try:
            proc.terminate()
        except (OSError, ValueError):
            pass
        try:
            proc.wait(timeout=_TERMINATE_GRACE_SECONDS)
            return
        except (subprocess.TimeoutExpired, OSError):
            pass
        try:
            proc.kill()
        except (OSError, ValueError):
            pass

    # ------------------------------------------------------------------
    # text convenience path (explicit decode of the binary path)
    # ------------------------------------------------------------------
    def run(
        self,
        argv: Sequence[str],
        cwd: str | Path | None = None,
        timeout_seconds: float = 900.0,
        input_text: str | None = None,
        env: Mapping[str, str] | None = None,
        env_remove: Sequence[str] | None = None,
        max_capture_bytes: int | None = None,
    ) -> CommandResult:
        binary = self.run_bytes(
            argv,
            cwd=cwd,
            timeout_seconds=timeout_seconds,
            input_bytes=input_text.encode("utf-8") if input_text is not None else None,
            env=env,
            env_remove=env_remove,
            max_capture_bytes=max_capture_bytes,
        )
        return CommandResult(
            command=binary.command,
            cwd=binary.cwd,
            exit_code=binary.exit_code,
            stdout=binary.stdout.decode("utf-8", errors="replace"),
            stderr=binary.stderr.decode("utf-8", errors="replace"),
            duration_seconds=binary.duration_seconds,
            timed_out=binary.timed_out,
            error=binary.error,
            stdout_bytes_total=binary.stdout_bytes_total,
            stderr_bytes_total=binary.stderr_bytes_total,
            stdout_truncated=binary.stdout_truncated,
            stderr_truncated=binary.stderr_truncated,
        )
