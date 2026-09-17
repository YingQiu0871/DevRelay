# DevRelay v0.3-E — G0.1 / P7 platform proof (local ledger persistence under hard kill)

Status: **G0.1 CANDIDATE PASS — REQUIRES INDEPENDENT REVIEW** (self-approval is
forbidden; mandatory-core implementation remains **BLOCKED / NOT AUTHORIZED** until
an independent reviewer approves this proof).

This document records the execution of the single pre-implementation proof step
**G0.1 / P7** from the frozen v0.3-E design (`V03E_SPEC.md` §9, §25, §28).  It is
evidence for the **local persistence/ledger assumptions** the future mandatory-core
recovery reader is allowed to rely on — it is **not** a proof of the future
implementation, not a power-loss/`fsync` proof, and not a proof of any remote
identity.

## 1. Identity

| Item | Value |
| --- | --- |
| Proof executed at repository HEAD | `5bdc21d43484cf00a68cc4fe7705f487f0ec9047` (branch `v0.3-e-recovery-reconciliation`; parent `9f4a018…` lineage) |
| Frozen semantic design candidate | `9f4a01804b9affe8938a272553df345b5a60aeed` |
| v0.3-E status during the proof | DESIGN FROZEN / NOT IMPLEMENTED / NOT ACCEPTED / UNRELEASED |
| G0.1 status before this execution | PROOF REQUIRED / NOT RUN |
| Package version / public tags | `0.1.0` / `v0.1.0` only (unchanged) |
| Runtime/test/version changes by this proof | **none** (`git diff 5bdc21d -- src/devrelay tests pyproject.toml` is empty) |
| Real provider/model inference calls | **0** |

## 2. Production persistence path inspected (read-only)

| Aspect | Finding | Source |
| --- | --- | --- |
| Record location | `<workspace>/.devrelay/opencode/calls/OC-NNNN.json` | `src/devrelay/opencode/accounting.py::FilesystemOpenCodeLedger` (`root`, `calls_dir`) |
| Identity allocation | durable monotonic `OC-NNNN`; `sequence.json` (`{"next_call_sequence": N}`) written via a fixed-name temp file `.{name}.tmp` + `Path.replace`.  **Absent vs corrupt differ** (corrected after independent review, P3-1): a **missing** sequence file is recovered from the existing ledger as `max(existing ids)+1`; a **corrupt/unreadable** sequence file does **not** fall back — `_read_sequence` raises `OpenCodeLedgerError` and the allocator **fails closed**, precisely so numbering can never be reused.  Identity reuse is additionally refused by the create-new `begin()` write | `allocate_call_id`, `_existing_ids`, `_read_sequence` (`accounting.py`) |
| ISSUED write path | `begin(record)`: `open(target, "xb")` **create-new, direct write, no temp file, no `fsync`**; refuses to reuse an existing identity (`FileExistsError` → `OpenCodeLedgerError`) | `accounting.py::begin` (lines ~140-170) |
| Settlement write path | `finish(record)` → `_write(record)`: fixed-name temp file `.{target.name}.tmp` written complete, then `tmp.replace(target)` (atomic publication of the *final* artifact — the settle **replaces** the same artifact, it does not append a new one) | `accounting.py::finish`, `accounting.py::_write` |
| Temp-file naming | fixed name (`.OC-0001.json.tmp`), i.e. a hard kill can leave an inert temp artifact | `_write` |
| Flush / fsync | none anywhere in the ledger (`fsync` is never called); durability is "write + close + replace" only | `accounting.py` (whole file) |
| Tolerant accounting reader | `read_records()` iterates `calls/OC-*.json` and **silently `continue`s** on `OSError`/`JSONDecodeError`/`ValueError`, i.e. malformed artifacts vanish from its view | `accounting.py::read_records` (lines ~176-200) |
| Fields for ISSUED↔settled correlation | `call_id`, `operation`, `state` (`ISSUED`/`COMPLETED`/`TIMED_OUT`/`PROVIDER_UNAVAILABLE`/`MALFORMED_RESPONSE`), `method`, `path`, `session_id`, `issued`, `external_request_count`, `http_status`, `error_type`, `started_at`, `completed_at`, `duration_ms`, `submission_uncertain`, `response_media_type`, `prompt_sha256`, `prompt_chars`, `agent`, `model` | `src/devrelay/opencode/models.py::OpenCodeCallRecord` |
| Bridge call order (the production sequence proven here) | `allocate_call_id()` → `begin(ISSUED record)` → transport request → `finish(settled record)` | `src/devrelay/opencode/bridge.py::_request` (lines ~1212, ~1229, ~1280) |

The ordinary tolerant reader is **not** authoritative for G0.1; the proof therefore
scans the raw on-disk artifacts corruption-strictly (§5).

## 3. Proof environment (disposable, no user/production state)

* All proof state lived under one disposable directory in the OS temp area
  (`…/dsh-g01-proof/run/<case>/devrelay/opencode/…`); **no** real DevRelay run state,
  workspace, ledger or user configuration was read or written.
* The child processes used the **real accepted production classes** for persistence:
  `FilesystemOpenCodeLedger`, `OpenCodeCallRecord`, `OpenCodeCallState`
  (imported from `D:\DevRelay\src`, unmodified).
* The orchestrator/provider side was a **local no-op** (no transport object, no
  HTTP client, no OpenCode, no network, no provider): the proof exercises the
  persistence sequence, not model traffic.
* Proof harness code (`strict_scanner.py`, `child.py`, `driver.py`) lives **only**
  in the disposable temp directory; it is deliberately **not** committed into
  `src/` or `tests/`.  This document is the committed evidence.

## 4. Hard-kill mechanism

* Each case ran in a **separate child process** (`C:\Python314\python.exe child.py …`)
  that entered the production persistence path and then reached a **deterministic
  synchronization barrier** (a sentinel file under `barrier/<case>.ready` whose
  content records the barrier name, PID and timestamp).
* The parent driver waited (bounded, 20 s) for the barrier, then terminated the
  child externally with `subprocess.Popen.kill()` → **TerminateProcess** on Windows.
  No `finally`/cleanup code in the child could run, so no clean result could be
  manufactured after the kill.
* Only the harness's own child processes were killed; no unrelated process was
  touched (verified by command-line inspection before and after: the user's
  pre-existing `open-webui` processes were untouched, and the one leftover
  *harness* child from an invalid debug run was terminated by PID).
* Recorded per case: child PID, barrier reached, kill action, child exit code, and
  the raw artifact state after death (§6).

## 5. Strict proof scanner (harness-only, corruption-strict)

Rules implemented (`strict_scanner.py`):

* full recursive enumeration of the disposable ledger directory, **including
  dotfiles** (temp residue is evidence, not noise);
* every artifact is read and parsed; unreadable/malformed/truncated artifacts are
  **reported, never `continue`d over**;
* no newest-20/newest-200 (or any) truncation window;
* the relevant file/sequence interval is established by that full enumeration and
  recorded as an explicit interval statement.  **Recorded construction (P3-4
  clarification, documentary only):** the executed scanner's interval statement is
  the verbatim full-enumeration form recorded in the per-case evidence —
  `full recursive enumeration of <ledger dir> (N file(s)); no pagination/window
  applied` — i.e. the "proven interval" is the complete set of artifacts present in
  the disposable ledger directory at scan time.  It is **not** a sequence-arithmetic
  floor/ceiling proof, and absence is therefore only ever reported as the scoped,
  report-only `NO_RECORD_IN_PROVEN_INTERVAL`; no stronger interval claim is made or
  reconstructed after the fact;
* duplicate identities and temp/inert artifacts are detected separately;
* classifications: `VALID_ISSUED`, `VALID_SETTLED`, `EVIDENCE_GAP`, `CORRUPTION`,
  `MULTIPLE_MATCHES`, plus `TEMP_RESIDUE` and the report-only
  `NO_RECORD_IN_PROVEN_INTERVAL`;
* the scanner **never** emits a "never submitted" conclusion: absence is reported
  only as the scoped, report-only "no valid artifact in the fully enumerated
  interval";
* no model text is read, and no prompt/response/reasoning/credential is persisted.
* For contrast, each case also ran the production tolerant reader
  (`FilesystemOpenCodeLedger.read_records`).

## 6. Cases and raw evidence

All artifact sizes are bytes; hashes are SHA-256 of the artifact **after** the kill
(or after the controlled corruption, case E).  `sequence.json` is identical
(31 B, `568b7c62bb414868adbe0943b19c08e9d947cf29cb41ecb93c7aa060919ef86b`) in every
case; it is listed here once per case for completeness.

### G0.1-A1 — before the durable ISSUED record is committed

* boundary reached: `A1_pre_begin` (barrier signalled before `begin()` was called);
  child PID 44264; kill: `Popen.kill()` (TerminateProcess); exit code 1.
* artifacts: `sequence.json` (31 B, `568b7c62…`) only — **no `calls/OC-*.json`**,
  no temp file.
* strict classification: `NO_RECORD_IN_PROVEN_INTERVAL` (report-only; no valid
  ISSUED artifact, no residue, nothing interpretable as a settled operation).
* tolerant reader: 0 records.
* predefined criterion: no valid ISSUED record; no artifact interpretable as
  completed/settled; residue visible/classifiable → **MET**.

### G0.1-A2 — during the durable ISSUED write (created-new, not yet committed)

* boundary reached: `A2_mid_issued_write`; child PID 2144; kill: `Popen.kill()`
  (TerminateProcess); exit code 1.
* **disclosure nuance (P3-2, stated after independent review):** the partial
  artifact was produced by a **fault-injected short write inside the real
  production create-new ISSUED path** (`begin()`'s production payload, truncated to
  half its bytes by the harness wrapper), then flushed, and the child was killed
  while idling.  It was therefore *not* literally a process kill interrupting an
  otherwise normal full-length write at an arbitrary CPU instruction; the
  interrupted-write state itself is harness-injected, while the write path, payload
  and persistence code are production.  The resulting 318-byte artifact is a real
  malformed production-path artifact.
* artifacts: `calls/OC-0001.json` 318 B
  `0d83469f6992ede5fc7f59aea46dcb3c47e56ec598b1fac743e8c18acc53a60b` (truncated
  JSON: `invalid JSON at byte 318`), `sequence.json` 31 B.
* strict classification: `CORRUPTION` — the partial artifact is **visible and
  classified**, never treated as a valid ISSUED record.
* tolerant reader: **0 records** (it silently skipped the malformed artifact) — the
  concrete demonstration that the tolerant reader must not be used as recovery
  proof.
* predefined criterion: no valid ISSUED record; partial residue visible and
  classifiable as corruption/gap → **MET**.  The excluded invalid harness attempt
  that produced a 0-byte pre-boundary artifact (below) is **not** counted as safety
  evidence; both that 0-byte state and the 318-byte truncated state belong to the
  same fail-closed corruption class for the narrow claim made here, and only the
  318-byte run is the recorded A2 result.

### G0.1-B — after ISSUED is durable, before settlement

* boundary reached: `B_after_issued_before_settle` (`begin()` returned; settlement
  not started); child PID 50272; kill: `Popen.kill()`; exit code 1.
* artifacts: `calls/OC-0001.json` 635 B
  `fd5d8c2df3cec554b1003b67a1f592003b03423ad35758db533999245f85869f`
  (complete `state = ISSUED`), `sequence.json` 31 B.
* strict classification: `VALID_ISSUED`; no settlement artifact, no temp residue,
  no duplicates.
* tolerant reader: 1 record (`ISSUED`).
* predefined criterion: strict scan finds exactly the complete ISSUED evidence, and
  never reports an authoritative completed settlement → **MET**.

### G0.1-C — during the settlement write (publication not yet performed)

* boundary reached: `C_during_settle_publication` (the settlement temp file was
  complete on disk; `os.replace` was intercepted so publication had **not**
  happened); child PID 2528; kill: `Popen.kill()`; exit code 1.
* artifacts: `calls/.OC-0001.json.tmp` 701 B
  `977c360e681ab3c73facf1a6b42c8b153082b1f831310c0e5696d5335a1a6d24` (complete new
  settle payload, unpublished), `calls/OC-0001.json` 635 B
  `93a4c53b0102a5ef1461663af407261ff9fe5a04001ed00a5753317dbc169a4c` (the old
  complete ISSUED state), `sequence.json` 31 B.
* strict classification: `VALID_ISSUED` **plus `TEMP_RESIDUE`** — the incomplete
  settlement is visible and explicitly reported; the operation is **not** classified
  as settled and does **not** silently disappear.
* tolerant reader: 1 record (`ISSUED`) — consistent, and additionally unable to
  report the residue (contrast).
* predefined criterion (old complete ISSUED remains authoritative + visible
  temporary/incomplete settlement residue; no malformed settlement silently
  vanishing; no false settlement) → **MET**.

### G0.1-D — after settlement publication, before normal completion

* boundary reached: `D_after_settle_publication` (`finish()` returned; the child was
  killed before finishing normally); child PID 53040; kill: `Popen.kill()`; exit
  code 1.
* artifacts: `calls/OC-0001.json` 701 B
  `e8d746c322f881016edbc0b8c807d5b68db117381a0b9bc060709e12b157a284`
  (complete settled record), `sequence.json` 31 B.
* strict classification: `VALID_SETTLED`; no duplicate identity, no second
  authoritative artifact, no temp residue.
* tolerant reader: 1 record (`COMPLETED`).
* predefined criterion: strict scan identifies the complete settled state; no
  duplicate settlement; no ambiguous second authoritative record → **MET**.

### G0.1-E — corrupted-record control (scanner self-test)

* child ran to a **clean exit** (PID 52764, exit code 0, barrier
  `E_clean_write_complete`), then the parent deliberately truncated the settled
  artifact to half its bytes (controlled post-exit corruption; not a writer test).
* artifacts: `calls/OC-0001.json` 350 B
  `664bc6084b6365cfbe9dd7e2078b4f292c9a83d9a3bd34382fa89a118ad5f7be`
  (`invalid JSON at byte 337`), `sequence.json` 31 B.
* strict classification: `CORRUPTION` (must never be
  `NO_RECORD_IN_PROVEN_INTERVAL`).
* tolerant reader: **0 records** — the tolerant reader presents the corrupted
  operation as if it had never existed; the strict scanner does not.
* predefined criterion: scanner returns `evidence_gap`/corruption and must not
  return "nothing happened" → **MET**.

### Invalid harness attempts (excluded from safety evidence)

1. **A2 attempt #1** — the fault injector matched only *text-mode* create-new opens,
   so the production write completed normally and the target barrier was never
   reached (no kill point).  Excluded.
2. **A2 attempt #2** — the fault wrapper lacked the context-manager protocol, so the
   child raised before reaching the target boundary (0-byte artifact, barrier never
   reached).  Excluded.

Neither invalid attempt is counted as safety evidence; both are recorded here in
full, and no additional cases were probed to search for a passing outcome.

## 7. Predefined criteria and result

| Case | Boundary proven | Strict scanner classification | Tolerant reader | Criterion |
| --- | --- | --- | --- | --- |
| A1 | before durable ISSUED | `NO_RECORD_IN_PROVEN_INTERVAL` (report-only) | 0 records | MET |
| A2 | during durable ISSUED write | `CORRUPTION` (visible partial artifact) | 0 records (silently skipped) | MET |
| B | after ISSUED, before settle | `VALID_ISSUED` | 1 (`ISSUED`) | MET |
| C | during settle publication | `VALID_ISSUED` + `TEMP_RESIDUE` | 1 (`ISSUED`) | MET |
| D | after settle publication | `VALID_SETTLED` | 1 (`COMPLETED`) | MET |
| E | corrupted-record control | `CORRUPTION` | 0 records (silently skipped) | MET |

**Candidate result: G0.1 CANDIDATE PASS — REQUIRES INDEPENDENT REVIEW.**
Platform proof gate after this execution: **PARTIALLY EXECUTED / NOT COMPLETE**
(G0.1/P7 executed once; G0.2-G0.5, G1, G2 NOT RUN).  Mandatory-core implementation:
**NOT AUTHORIZED**.  `adopt_completed_turn`: **DISABLED**.  No step is an
authoritative PASS before independent approval, and the executing agent cannot
self-approve the gate.

* No relevant malformed/torn artifact was silently treated as absence by the strict
  scanner; the tolerant reader demonstrably does treat A2/E corruption as absence
  (0 records), which is precisely why the frozen design requires a dedicated
  corruption-strict recovery reader.
* No hard-kill window produced an authoritative false settlement.
* No settled operation became indistinguishable from "no record".
* The strict scanner can fail closed on incomplete/corrupt persistence.
* The proof does not rely on the tolerant accounting reader.
* Real provider/model inference calls: **0**.

## 7.1 Independent proof review (recorded outcome)

The independent review of this proof returned **REQUEST_CHANGES** with **P0 = 0,
P1 = 0, P2 = 1** — the single P2 being a *status-bookkeeping wording* issue (an
active README line still said the proof gate had not run while the same surface
recorded the G0.1 execution), now corrected, plus the P3 notes handled below.  The
proof evidence itself was found **sufficient**, and the following independently
established conclusions are recorded here verbatim and are not weakened:

* harness fidelity: **acceptable**; hard-kill mechanism: **acceptable**;
* A1 **MET**; A2 **MET** (with the disclosure nuance recorded in §6); B **MET**;
  C **MET**; D **MET**; E **MET** (scanner control);
* the sequence-allocation window is **not** a missing safety-critical G0.1 probe;
* replace-success / pre-return state is covered by the D-equivalent persistent
  state;
* **no probe shopping**: confirmed;
* the future recovery path must **not** use the tolerant `read_records()` as
  authoritative recovery evidence;
* this process-kill proof does **not** claim power-loss / `fsync` durability.

Recorded P3 notes (non-blocking, no scope expansion):

* **P3-1** (corrected above): a missing `sequence.json` may be recovered as
  `max(existing)+1`, but a **corrupt** one fails closed with `OpenCodeLedgerError`;
  the earlier single-sentence summary conflated the two.
* **P3-2** (clarified above): A2's partial artifact is a fault-injected short write
  inside the real production create-new path, not an arbitrary-instruction
  interruption of a normal full write; the excluded invalid attempt (0-byte
  pre-boundary artifact) remains excluded.
* **P3-3** (auditability limitation, recorded only): the disposable harness and
  strict scanner were **not** committed into `src/` or `tests/`, and they are
  deliberately **not** reconstructed or re-run after the fact; a future proof round
  may choose to commit an equivalent harness under a reviewed location.
* **P3-4** (documentary clarification above): the interval construction is the
  recorded full-enumeration statement, not a sequence-arithmetic floor/ceiling
  proof; if a stronger interval proof is wanted, it must be designed and executed
  in a future (separately authorized) probe rather than invented now.

## 8. Limitations and non-claims

Even though all planned cases passed, this proof does **not** claim:

* that v0.3-E recovery is implemented (it is not; nothing was implemented);
* that the future strict reader exists or is tested (only a harness scanner was
  built for this proof);
* power-loss durability, `fsync` guarantees, sudden machine power loss coverage, or
  any storage-hardware guarantee (the ledger never calls `fsync`);
* remote submission identity, session exclusivity, prompt-text fidelity, or
  timestamp/order fidelity (P1/P2/P3/P8/P9 are untouched and remain PROOF REQUIRED);
* that adoption is enabled (`adopt_completed_turn` remains DISABLED);
* that mandatory-core implementation is authorized: **it is not**, and this
  self-report cannot authorize it — an independent reviewer must approve G0.1/P7
  first.  Until then the frozen hard gate stands: design frozen → G0.1/P7 PASS →
  implementation may be authorized; if the proof is rejected, implementation stays
  blocked (no degraded-implementation path);
* that any of G0.2, G0.3, G0.4, G0.5, G1 or G2 has been executed (they have not).

This is a **process hard-kill persistence proof only**.

## 9. Evidence retention

Raw harness output (per-case JSON: PIDs, barriers, exit codes, artifact listings
with sizes and SHA-256, strict classifications, tolerant-reader contrasts) was
captured under the disposable proof directory
(`…/dsh-g01-proof/evidence/{summary.json,summary.md,final_summary.json,A2_*.json}`).
The disposable ledger directories may be deleted; the metadata above is the
committed record.  No secret, prompt, response or credential is stored here.
