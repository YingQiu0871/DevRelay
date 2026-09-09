"""CommandRunner tests: real subprocess behavior, timeout, shell safety."""

import sys
import time

from devrelay.workspace.runner import CommandRunner


def test_successful_command_captures_output(tmp_path):
    runner = CommandRunner()
    result = runner.run(
        [sys.executable, "-c", "import sys; print('hello-out'); print('err', file=sys.stderr)"],
        cwd=tmp_path,
        timeout_seconds=30,
    )
    assert result.success
    assert result.exit_code == 0
    assert "hello-out" in result.stdout
    assert "err" in result.stderr
    assert result.error is None
    assert result.duration_seconds >= 0


def test_input_streamed_on_stdin():
    runner = CommandRunner()
    result = runner.run(
        [sys.executable, "-c", "import sys; data = sys.stdin.read(); print(len(data))"],
        input_text="12345",
        timeout_seconds=30,
    )
    assert result.success
    assert result.stdout.strip() == "5"


def test_timeout_is_reported_not_raised(tmp_path):
    runner = CommandRunner()
    started = time.monotonic()
    result = runner.run(
        [sys.executable, "-c", "import time; time.sleep(5)"],
        cwd=tmp_path,
        timeout_seconds=1,
    )
    assert result.timed_out
    assert result.error is not None
    assert "timed out" in result.error
    assert result.exit_code != 0
    assert time.monotonic() - started < 4


def test_missing_executable_is_a_result_not_crash():
    runner = CommandRunner()
    result = runner.run(["definitely-not-a-real-binary-xyz123"], timeout_seconds=10)
    assert result.exit_code is None
    assert result.error is not None
    assert not result.success


def test_shell_metacharacters_never_executed(tmp_path):
    """argv items are passed literally: no shell, no command injection."""
    runner = CommandRunner()
    marker = tmp_path / "pwned.txt"
    payload = f"x; echo PWNED > {marker}"
    result = runner.run(
        [sys.executable, "-c", "import sys; print(sys.argv[1])", payload],
        cwd=tmp_path,
        timeout_seconds=30,
    )
    assert result.success
    assert payload in result.stdout          # passed as a literal argument
    assert not marker.exists()               # nothing was executed by a shell
