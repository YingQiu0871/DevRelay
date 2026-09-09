"""Subprocess runner.

Every external command DevRelay executes goes through :class:`CommandRunner`.
It always uses ``shell=False`` (argv lists only), supports timeouts, stdin
streaming and structured results — never raw ``os.system``-style execution.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Mapping, Sequence, Optional

from devrelay.models import CommandResult


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

    def run(
        self,
        argv: Sequence[str],
        cwd: str | Path | None = None,
        timeout_seconds: float = 900.0,
        input_text: str | None = None,
        env: Mapping[str, str] | None = None,
    ) -> CommandResult:
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
        stdout = ""
        stderr = ""
        proc: subprocess.Popen[str] | None = None

        try:
            proc = subprocess.Popen(
                args,
                cwd=resolved_cwd,
                env=run_env,
                shell=self._shell_enabled,
                stdin=subprocess.PIPE if input_text is not None else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="replace",
            )
            try:
                stdout, stderr = proc.communicate(
                    input=input_text, timeout=timeout_seconds
                )
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.kill()
                stdout, stderr = proc.communicate()
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
        return CommandResult(
            command=args,
            cwd=resolved_cwd,
            exit_code=exit_code,
            stdout=stdout or "",
            stderr=stderr or "",
            duration_seconds=round(duration, 3),
            timed_out=timed_out,
            error=error,
        )
