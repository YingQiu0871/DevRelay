# Contributing to DevRelay

Thanks for taking a look. This project is small on purpose; contributions should
stay within the scope described in `README.md`.

## Requirements

- Python >= 3.11
- Git (DevRelay operates inside git workspaces)
- Optional: the official Codex CLI, only needed when you want to run real
  implementation passes

## Setup

```bash
git clone <your-fork-url>
cd devrelay
python -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

## Tests

```bash
python -m pytest
```

The test suite runs fully offline: Codex and HTTP reviewers are mocked or
faked, and the Git tests use temporary repositories. **No real Codex
invocation is required (or wanted) for unit tests** - please do not add tests
that call a model.

## Expectations

- Keep the core boundaries intact: `providers/`, `workspace/`, `baseline/`,
  `artifacts/` and `pipeline/` are deliberately separate; do not collapse them
  into the engine.
- DevRelay must never mutate a user's real Git index, commit, push, tag or
  reset on its own. Changes that touch these areas need tests proving the
  boundary still holds.
- Security-sensitive changes (subprocess I/O, redaction, policy guards,
  baseline/recovery paths) require regression tests, including the failure
  paths (corruption, conflicts, exceptions, interruption).
- Do not weaken or delete existing regression assertions to make a change pass.
- Documentation (`README.md`, `CHANGELOG.md`) must describe what the code
  actually does - no aspirational security claims.

## Reporting issues

Include: the DevRelay version (`devrelay version`), OS, git version, the
command you ran, the task state (`devrelay status`), and the relevant
`.devrelay/tasks/<TASK_ID>/` artifacts. Redact any secrets before pasting.
