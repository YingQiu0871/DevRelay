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
import time
from pathlib import Path
from typing import Mapping, Sequence

from devrelay.models import BinaryCommandResult, CommandResult


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
    ) -> BinaryCommandResult:
        """Run a command with byte-exact stdin/stdout (no newline translation)."""
        args = [str(item) for item in argv]
        if not args:
            raise ValueError("refusing to run an empty command")

        resolved_cwd = str(cwd) if cwd is not None else None
        run_env = os.environ.copy()
        run_env.update(self._env_overrides)
        if env:
            run_env.update({str(k): str(v) for k, v in env.items()})

        started = time.monotonic()
        timed_out = False
        error: str | None = None
        exit_code: int | None = None
        stdout_bytes = b""
        stderr_bytes = b""

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
            try:
                stdout_bytes, stderr_bytes = proc.communicate(
                    input=input_bytes, timeout=timeout_seconds
                )
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.kill()
                stdout_bytes, stderr_bytes = proc.communicate()
                error = (
                    f"command timed out after {timeout_seconds:g}s: "
                    + " ".join(args[:4])
                )
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
        )

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
    ) -> CommandResult:
        binary = self.run_bytes(
            argv,
            cwd=cwd,
            timeout_seconds=timeout_seconds,
            input_bytes=input_text.encode("utf-8") if input_text is not None else None,
            env=env,
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
        )
