"""Strong process containment for the structured Codex runtime (v0.2-C).

The structured runtime's POST control-plane verification is only meaningful if
*everything the Codex child can spawn* is dead by the time the manifest is
compared.  A plain ``terminate()``/``kill()`` of the direct child cannot promise
that: a child may spawn a detached descendant that outlives it and mutates the
workspace after the guard has passed.

This module provides the abstraction the runner uses:

* :func:`containment_support` - is strong descendant containment available here?
* :class:`ProcessContainment` - ``spawn_contained`` / ``wait_contained`` /
  ``terminate_contained`` / ``kill_contained`` / ``all_contained_processes_dead``.

Windows is implemented with a Job Object:

* the job is created with ``JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`` so closing the
  handle terminates every contained process;
* containment is established **before Codex is allowed to run**, using the
  broker pattern: the parent starts a tiny launcher, assigns the launcher to the
  job, and only then signals it to spawn the real Codex argv.  The launcher
  executes no user/model work before that signal, so there is no window in which
  Codex could spawn an uncontained descendant (the naive "spawn Codex then assign
  it to the job" order is racy and is deliberately not used);
* ``DETACHED_PROCESS`` / new process groups do **not** remove a process from its
  job, so a detached descendant stays contained and is killed when the contained
  window ends;
* breakaway is not granted, so a contained process cannot create a process
  outside the job.

Any other platform has no equivalent mechanism wired up (a POSIX process group
does not contain a ``setsid``/double-fork descendant), so
:func:`containment_support` reports it as unsupported and the structured runtime
fails pre-flight with ``codex_process_containment_unsupported`` (zero provider
calls) instead of pretending containment exists.  Explicit ``text`` mode remains
the documented compatibility escape.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Mapping, Protocol, Sequence

_IS_WINDOWS = sys.platform == "win32"

_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
_JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION = 1
_PROCESS_SET_QUOTA = 0x0100
_PROCESS_TERMINATE = 0x0001
_PROCESS_QUERY_INFORMATION = 0x0400

_DEAD_POLL_INTERVAL = 0.05
_DEAD_DEADLINE_SECONDS = 30.0

_BROKER_SOURCE = r'''
import json, os, subprocess, sys, time
spec = json.loads(open(sys.argv[1], encoding="utf-8").read())
while not os.path.exists(spec["go"]):
    time.sleep(0.005)
sys.exit(subprocess.call(spec["argv"]))
'''


class ContainmentError(RuntimeError):
    """Strong containment could not be established or verified."""


class ContainmentUnsupportedError(ContainmentError):
    """This platform has no strong descendant containment for the runtime."""


class ContainedProcess(Protocol):  # pragma: no cover - typing only
    pid: int

    def wait(self, timeout: float | None = None) -> int: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...


class ProcessContainment(Protocol):  # pragma: no cover - typing only
    name: str

    def spawn_contained(
        self,
        argv: Sequence[str],
        *,
        cwd: str | Path | None,
        env: Mapping[str, str],
        stdin_pipe: bool,
        stdout_pipe: bool,
        stderr_pipe: bool,
        input_bytes: bytes | None,
    ) -> ContainedProcess: ...

    def wait_contained(self, proc: ContainedProcess, timeout: float) -> bool: ...

    def terminate_contained(self) -> None: ...

    def kill_contained(self) -> None: ...

    def all_contained_processes_dead(self, timeout: float) -> bool: ...

    def close(self) -> None: ...


def containment_support() -> tuple[bool, str]:
    """(supported, diagnostic) for strong descendant containment on this host."""
    if _IS_WINDOWS:
        try:
            import ctypes  # noqa: F401
        except Exception as exc:  # pragma: no cover - defensive
            return False, f"ctypes unavailable: {exc}"
        return True, "windows Job Object (KILL_ON_JOB_CLOSE, broker hand-off)"
    return (
        False,
        "no strong descendant containment is implemented for this platform "
        "(a POSIX process group cannot contain a setsid/double-fork descendant)",
    )


class _WindowsJobContainment:
    """Job-object containment with a race-free broker hand-off."""

    name = "windows-job-object"

    def __init__(self) -> None:
        import ctypes
        from ctypes import wintypes

        self._ctypes = ctypes
        self._wintypes = wintypes

        class _BasicLimit(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class _IoInfo(ctypes.Structure):
            _fields_ = [
                ("ReadOperationCount", ctypes.c_uint64),
                ("WriteOperationCount", ctypes.c_uint64),
                ("OtherOperationCount", ctypes.c_uint64),
                ("ReadTransferCount", ctypes.c_uint64),
                ("WriteTransferCount", ctypes.c_uint64),
                ("OtherTransferCount", ctypes.c_uint64),
            ]

        class _ExtendedLimit(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", _BasicLimit),
                ("IoInfo", _IoInfo),
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        class _BasicAccounting(ctypes.Structure):
            _fields_ = [
                ("TotalUserTime", ctypes.c_int64),
                ("TotalKernelTime", ctypes.c_int64),
                ("ThisPeriodTotalUserTime", ctypes.c_int64),
                ("ThisPeriodTotalKernelTime", ctypes.c_int64),
                ("TotalPageFaultCount", wintypes.DWORD),
                ("TotalProcesses", wintypes.DWORD),
                ("ActiveProcesses", wintypes.DWORD),
                ("TotalTerminatedProcesses", wintypes.DWORD),
            ]

        self._BasicAccounting = _BasicAccounting
        self._ExtendedLimit = _ExtendedLimit

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32 = kernel32
        kernel32.CreateJobObjectW.restype = wintypes.HANDLE
        kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        kernel32.SetInformationJobObject.restype = wintypes.BOOL
        kernel32.SetInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        kernel32.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.TerminateJobObject.restype = wintypes.BOOL
        kernel32.TerminateJobObject.argtypes = [wintypes.HANDLE, wintypes.UINT]
        kernel32.QueryInformationJobObject.restype = wintypes.BOOL
        kernel32.QueryInformationJobObject.argtypes = [
            wintypes.HANDLE,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
            ctypes.c_void_p,
        ]
        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            raise ContainmentError(
                f"CreateJobObjectW failed (error {ctypes.get_last_error()})"
            )
        self._job = job
        self._active = True
        self._workdirs: list[Path] = []
        info = _ExtendedLimit()
        info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not kernel32.SetInformationJobObject(
            job,
            _JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(info),
            ctypes.sizeof(info),
        ):
            self.close()
            raise ContainmentError(
                "SetInformationJobObject(KILL_ON_JOB_CLOSE) failed "
                f"(error {ctypes.get_last_error()})"
            )

    def spawn_contained(
        self,
        argv: Sequence[str],
        *,
        cwd: str | Path | None,
        env: Mapping[str, str],
        stdin_pipe: bool,
        stdout_pipe: bool,
        stderr_pipe: bool,
        input_bytes: bytes | None,
    ) -> subprocess.Popen:
        """Start *argv* inside the job, before it can execute any user work."""
        import json
        import tempfile

        workdir = Path(tempfile.mkdtemp(prefix="devrelay-contained-"))
        spec_path = workdir / "spec.json"
        go_path = workdir / "go"
        spec_path.write_text(
            json.dumps({"argv": [str(a) for a in argv], "go": str(go_path)}),
            encoding="utf-8",
        )
        proc = subprocess.Popen(
            [sys.executable, "-c", _BROKER_SOURCE, str(spec_path)],
            cwd=str(cwd) if cwd is not None else None,
            env=dict(env),
            shell=False,
            stdin=subprocess.PIPE if stdin_pipe else None,
            stdout=subprocess.PIPE if stdout_pipe else None,
            stderr=subprocess.PIPE if stderr_pipe else None,
        )
        self._workdirs.append(workdir)
        handle = self._kernel32.OpenProcess(
            _PROCESS_SET_QUOTA | _PROCESS_TERMINATE | _PROCESS_QUERY_INFORMATION,
            False,
            proc.pid,
        )
        if not handle:
            self._abort_spawn(
                proc,
                f"OpenProcess failed (error {self._ctypes.get_last_error()})",
            )
        try:
            if not self._kernel32.AssignProcessToJobObject(self._job, handle):
                self._abort_spawn(
                    proc,
                    "AssignProcessToJobObject failed "
                    f"(error {self._ctypes.get_last_error()})",
                )
        finally:
            self._kernel32.CloseHandle(handle)
        # Containment is active; release the broker so it spawns Codex inside it.
        go_path.write_text("go", encoding="utf-8")
        return proc

    def _abort_spawn(self, proc: subprocess.Popen, message: str) -> None:
        try:
            proc.kill()
        except Exception:  # pragma: no cover - defensive
            pass
        try:
            proc.wait(timeout=10)
        except Exception:  # pragma: no cover - defensive
            pass
        raise ContainmentError(message)

    def wait_contained(self, proc: ContainedProcess, timeout: float) -> bool:
        try:
            proc.wait(timeout=timeout)
            return True
        except subprocess.TimeoutExpired:
            return False
        except Exception:  # pragma: no cover - defensive
            return False

    def active_processes(self) -> int:
        info = self._BasicAccounting()
        ok = self._kernel32.QueryInformationJobObject(
            self._job,
            _JOB_OBJECT_BASIC_ACCOUNTING_INFORMATION,
            self._ctypes.byref(info),
            self._ctypes.sizeof(info),
            None,
        )
        if not ok:
            return -1
        return int(info.ActiveProcesses)

    def terminate_contained(self) -> None:
        try:
            self._kernel32.TerminateJobObject(self._job, 0)
        except Exception:  # pragma: no cover - defensive
            pass

    def kill_contained(self) -> None:
        self.terminate_contained()

    def all_contained_processes_dead(
        self, timeout: float = _DEAD_DEADLINE_SECONDS
    ) -> bool:
        deadline = time.monotonic() + max(0.0, float(timeout))
        while True:
            if self.active_processes() == 0:
                return True
            if time.monotonic() >= deadline:
                return self.active_processes() == 0
            time.sleep(_DEAD_POLL_INTERVAL)

    def close(self) -> None:
        if getattr(self, "_active", False) and getattr(self, "_job", None):
            # KILL_ON_JOB_CLOSE is the last-resort backstop.
            self._kernel32.CloseHandle(self._job)
            self._job = None
            self._active = False
        for workdir in getattr(self, "_workdirs", []):
            shutil.rmtree(workdir, ignore_errors=True)
        self._workdirs = []


def create_containment() -> ProcessContainment:
    """Create a containment for one structured runtime invocation."""
    supported, diagnostic = containment_support()
    if not supported:
        raise ContainmentUnsupportedError(diagnostic)
    if _IS_WINDOWS:
        return _WindowsJobContainment()
    raise ContainmentUnsupportedError(diagnostic)  # pragma: no cover - unreachable
