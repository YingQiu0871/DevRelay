"""OpenCode call accounting (v0.3-A).

One issued HTTP request = one :class:`OpenCodeCallRecord`, with a durable,
monotonic, never-reused id (``OC-0001``) allocated *before* the request leaves
the machine.  Records are settled in place under
``.devrelay/opencode/calls/<call-id>.json`` and never contain prompt text,
transcripts, environment values or credentials (only a prompt hash and counts).

There are deliberately **no** retries anywhere in v0.3-A: a failed request is a
failed call and stays visible as such.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from devrelay.opencode.models import OpenCodeCallRecord
from devrelay.redact import sanitize


class OpenCodeLedger(Protocol):
    """Minimal accounting sink used by the bridge."""

    def allocate_call_id(self) -> str: ...

    def begin(self, record: OpenCodeCallRecord) -> None: ...

    def finish(self, record: OpenCodeCallRecord) -> None: ...

    def records(self) -> list[OpenCodeCallRecord]: ...


class NullOpenCodeLedger:
    """In-memory ledger (tests, tooling): allocation + record keeping only."""

    def __init__(self) -> None:
        self._sequence = 0
        self._records: list[OpenCodeCallRecord] = []

    def allocate_call_id(self) -> str:
        self._sequence += 1
        return f"OC-{self._sequence:04d}"

    def begin(self, record: OpenCodeCallRecord) -> None:
        self._records.append(record)

    def finish(self, record: OpenCodeCallRecord) -> None:
        for index, existing in enumerate(self._records):
            if existing.call_id == record.call_id:
                self._records[index] = record
                return
        self._records.append(record)

    def records(self) -> list[OpenCodeCallRecord]:
        return list(self._records)


class FilesystemOpenCodeLedger:
    """Durable ledger under ``.devrelay/opencode`` (workspace scoped)."""

    def __init__(self, devrelay_dir: Path) -> None:
        self.root = Path(devrelay_dir) / "opencode"
        self.calls_dir = self.root / "calls"
        self.sequence_path = self.root / "sequence.json"
        self._records: list[OpenCodeCallRecord] = []

    # ------------------------------------------------------------------
    def _read_sequence(self) -> int:
        if not self.sequence_path.is_file():
            return 0
        try:
            payload: Any = json.loads(self.sequence_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return 0
        value = payload.get("next_call_sequence") if isinstance(payload, dict) else None
        return int(value) if isinstance(value, int) and value > 0 else 0

    def allocate_call_id(self) -> str:
        """Durable, monotonic, never-reused call identity."""
        sequence = max(1, self._read_sequence())
        self.root.mkdir(parents=True, exist_ok=True)
        self.sequence_path.write_text(
            json.dumps({"next_call_sequence": sequence + 1}, indent=2),
            encoding="utf-8",
        )
        return f"OC-{sequence:04d}"

    # ------------------------------------------------------------------
    def _path(self, call_id: str) -> Path:
        return self.calls_dir / f"{call_id}.json"

    def _write(self, record: OpenCodeCallRecord) -> None:
        self.calls_dir.mkdir(parents=True, exist_ok=True)
        target = self._path(record.call_id)
        tmp = target.with_name(f".{target.name}.tmp")
        tmp.write_text(
            json.dumps(record.model_dump(mode="json"), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        tmp.replace(target)

    def begin(self, record: OpenCodeCallRecord) -> None:
        record = record.model_copy(
            update={"error": sanitize(record.error)[:500] if record.error else ""}
        )
        self._records.append(record)
        self._write(record)

    def finish(self, record: OpenCodeCallRecord) -> None:
        record = record.model_copy(
            update={"error": sanitize(record.error)[:500] if record.error else ""}
        )
        for index, existing in enumerate(self._records):
            if existing.call_id == record.call_id:
                self._records[index] = record
                break
        else:  # pragma: no cover - defensive
            self._records.append(record)
        self._write(record)

    def records(self) -> list[OpenCodeCallRecord]:
        return list(self._records)

    def read_records(self) -> list[OpenCodeCallRecord]:
        """Read every persisted record (newest allocation order by call id)."""
        if not self.calls_dir.is_dir():
            return []
        out: list[OpenCodeCallRecord] = []
        for path in sorted(self.calls_dir.glob("OC-*.json")):
            try:
                out.append(
                    OpenCodeCallRecord.model_validate(
                        json.loads(path.read_text(encoding="utf-8"))
                    )
                )
            except (OSError, json.JSONDecodeError, ValueError):
                continue
        return out
