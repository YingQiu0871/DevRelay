# DevRelay Roadmap / DevRelay 实现路线图

This roadmap separates **released**, **implemented but unreleased**, **in progress**, and **planned** work. Items move forward only after review, evidence, and release gates are satisfied.

本路线图区分 **已发布**、**已实现但未发布**、**开发中** 与 **计划中**。只有在复审、证据和发布门槛满足后，功能才进入下一个状态。

## Status legend / 状态说明

- ✅ **Released / 已发布**
- ✅ **Released (in 0.3.0) / 已随 0.3.0 发布**
- 🧪 **Implemented, unreleased / 已实现未发布**
- 🚧 **In progress / 开发中**
- 📋 **Planned / 计划中**
- ⏸ **Externally blocked / 外部条件阻塞**

## v0.1 — Reliable local orchestration foundation / 可靠本地编排基础

Status: ✅ Released as v0.1.0

目标：建立可恢复、可审计、对 dirty workspace 友好的本地编排器基础。

Implemented / 已实现：

- persistent workflow state machine / 持久化流程状态机
- dirty-workspace task baseline / dirty workspace 任务基线
- task-relative diff / 任务相对差异
- bounded review/fix loop / 有上限的审阅修复循环
- Codex CLI implementer integration / Codex CLI 实现者集成
- manual planner/reviewer handoff / 手动规划与审阅交接
- repository mutation guards / 仓库变更保护
- interruption recovery and fail-closed behavior / 中断恢复与 fail-closed
- auditable task artifacts / 可审计任务证据

## v0.2 — Structured runtime and stronger control-plane safety / 结构化运行时与控制面强化

### v0.2-A / v0.2-B

Status: ✅ Shipped in 0.3.0; independent acceptance not complete; not separately released. / 已随 0.3.0 发布；独立验收尚未完成；不是单独的 v0.2 发布。

方向：强化自动 review、控制状态、迁移与调用记账等基础能力。

### v0.2-C — Structured Codex Runtime

Status: ✅ Shipped in 0.3.0; independent acceptance not complete; E2E closure pending (⏸ externally blocked). / 已随 0.3.0 发布；独立验收尚未完成；E2E 闭环待完成（⏸ 外部条件阻塞）。

Implemented development evidence includes:

- structured result contract
- strict output schema
- transient result staging
- bounded process capture
- control-plane PRE/POST guard
- durable completion milestones
- completion replay
- implementation/test reconciliation
- explicit external-call accounting
- offline regression suite passing

A single authorized replacement real Codex smoke was executed against candidate `4790ca3`. The real endpoint accepted the reviewed annotation-free schema and did **not** return `invalid_json_schema`, directly verifying that the previous schema regression is fixed.

一次授权的 replacement real Codex smoke 已针对候选版本 `4790ca3` 执行。真实端点接受了复审后的 annotation-free schema，且未返回 `invalid_json_schema`，因此原 schema 回归问题已经被真实端点直接证明修复。

However, the provider usage limit was reached before `--output-last-message` produced the structured result file. Therefore the following remain pending:

- end-to-end real structured-result delivery;
- real staging/persistence/reconciliation on a successful turn;
- `COMPLETION_APPLIED` on the real provider path.

因此 v0.2-C 尚未完全闭环。此次失败不再归因于 schema，但完整真实 E2E 路径仍未得到证明。

The smoke also surfaced a separate Windows-host P2: Codex shell `exec_command` was rejected by policy around the WindowsApps `pwsh.exe` alias. This should be investigated **offline first**, without spending another real provider call. A later real E2E smoke should only be attempted after quota is available and the Windows compatibility issue is understood.

Smoke 还暴露了一个独立 Windows P2：Codex shell `exec_command` 因 WindowsApps 的 `pwsh.exe` alias 相关 policy 被拒绝。应先进行**离线调查**，不要消耗新的真实 provider 调用；只有额度恢复且 Windows 兼容性问题得到理解后，才安排下一次真实 E2E smoke。

## v0.3 — OpenCode orchestration foundation / OpenCode 编排基础

Goal / 目标：把 DevRelay 从 Codex-centric CLI 演进为 OpenCode-first orchestration layer。

### v0.3-A — OpenCode Session Bridge

Status: ✅ Released in 0.3.0

Target / 目标：

- explicitly configured OpenCode endpoint
- session discovery and selection
- session/workspace identity validation
- read normalized session output
- send one prompt
- bounded wait for idle/terminal state
- interrupt/cancel when supported
- fail-closed malformed/unavailable handling
- deterministic offline fake/stub tests

Non-goals / 本阶段不做：

- autonomous multi-agent loops
- ChatGPT/MCP exposure
- role routing
- approval decisions inside DevRelay

### v0.3-B — ChatGPT/MCP Tool Surface

Status: ✅ Released in 0.3.0 (19 tools, local stdio)

Goal: expose a narrow, explicit DevRelay tool surface so ChatGPT can inspect state, read evidence, and issue the next bounded action.

计划能力：

- read project/task/session status
- read normalized implementer/reviewer output
- inspect diff/test/review evidence
- issue one bounded next action
- interrupt/pause
- return `NEEDS_USER_DECISION` when human input is required

### v0.3-C — Agent Role Routing

Status: ✅ Released in 0.3.0

Goal: make agent roles explicit and configurable.

Example target mapping / 目标示例：

```text
Planner     → ChatGPT
Implementer → OpenCode / DeepSeek
Reviewer    → OpenCode / GLM
```

Required properties / 约束：

- implementer and reviewer identities remain distinct
- no implementer self-approval
- model/provider changes are explicit and auditable
- session/workspace ownership is validated

### v0.3-D — Bounded Orchestration Loop

Status: ✅ Released in 0.3.0

Goal: automate the repetitive loop without creating an unlimited autonomous agent.

```text
PLAN
  ↓
IMPLEMENT
  ↓
TEST
  ↓
REVIEW
  ├─ PASS ─────────────→ ACCEPT
  ├─ REQUEST_CHANGES ──→ FIX → TEST → REVIEW
  ├─ BLOCKED ──────────→ STOP
  └─ USER_DECISION ────→ HUMAN
```

Planned controls / 计划控制：

- maximum repair rounds
- maximum external calls
- stop on configured severity
- stop on workspace/control-plane drift
- no hidden retries
- explicit review disagreement handling
- user escalation gate

### v0.3-E — Recovery, Replay & Security Hardening

Status: ✅ Released in 0.3.0 (mandatory fail-closed core; adoption disabled; platform gates open)

Targets / 目标：

- crash-safe orchestration state
- duplicate-action prevention
- idempotent replay where provable
- OpenCode interruption recovery
- explicit call accounting across all agents
- provider capability negotiation
- transcript/data minimization
- tighter localhost/control-plane security boundaries

## v0.4 — Local Web Control Plane / 本地 Web 控制面

Goal: configuration, monitoring, and emergency intervention through a localhost WebUI.

目标：使用 localhost WebUI 完成配置、监控与紧急人工干预。

### v0.4-A — Local HTTP Control API

Status: ✅ **ACCEPTED / CLOSED by the owner on 2026-10-22** — stage acceptance,
not a v0.4 release.  See [V04A_SPEC.md](v0.4/V04A_SPEC.md) and
[V04A_ACCEPTANCE.md](v0.4/V04A_ACCEPTANCE.md).  A1 is the read-only transport
foundation; A2 adds the allowlisted backend-owned configuration patch.  The A1
localhost cookie-scope P2 was resolved by the header-borne session before A2;
its history is in [BACKLOG.md](BACKLOG.md) §12.

- bind localhost by default — implemented in A1
- authenticated local session — implemented in A1
- origin validation + header-session protection — implemented in A1
- validated project/workspace registry — implemented in A1
- no arbitrary filesystem browsing — enforced in A1
- backend-owned config mutation — implemented in A2 and accepted

### v0.4-B — WebUI Configuration

Status: ✅ **B1 + B2 ACCEPTED / CLOSED by the owner on 2026-10-22.**  See
[V04B_SPEC.md](v0.4/V04B_SPEC.md), [V04B_REVIEW.md](v0.4/V04B_REVIEW.md),
[V04B_ACCEPTANCE.md](v0.4/V04B_ACCEPTANCE.md), [V04B2_SPEC.md](v0.4/V04B2_SPEC.md),
[V04B2_REVIEW.md](v0.4/V04B2_REVIEW.md) and [V04B2_ACCEPTANCE.md](v0.4/V04B2_ACCEPTANCE.md).
B2 is the separate wiring API for the loopback OpenCode endpoint plus read-only
MCP/credential references.
The static UI is served at `/` by
`devrelay web serve`; it uses fragment-token login, header sessions and only the
A2 allowlisted configuration patch.

Implemented in B1:

- project/workspace context (active project read-only)
- implementer/reviewer role assignment
- model identifiers per role
- workflow/budget/review limits
- bounded runtime limits
- ChatGPT/MCP connection and provider wiring shown read-only
- provider credentials by environment reference, never written

Not in B1: editing OpenCode endpoint/workspace, profiles, arbitrary argv or
test shell commands (needs a separate wiring API); project switching (D); live
runs (C).

### v0.4-C — Dashboard & Live Runs

Status: ✅ **C1 + C2a + C2b + C2c ACCEPTED / CLOSED by the owner on
2026-10-22.**  See [V04C_SPEC.md](v0.4/V04C_SPEC.md), [V04C_REVIEW.md](v0.4/V04C_REVIEW.md),
[V04C1_ACCEPTANCE.md](v0.4/V04C1_ACCEPTANCE.md), [V04C2A_SPEC.md](v0.4/V04C2A_SPEC.md),
[V04C2A_REVIEW.md](v0.4/V04C2A_REVIEW.md), [V04C2A_ACCEPTANCE.md](v0.4/V04C2A_ACCEPTANCE.md),
[V04C2B_SPEC.md](v0.4/V04C2B_SPEC.md), [V04C2B_REVIEW.md](v0.4/V04C2B_REVIEW.md),
[V04C2B_ACCEPTANCE.md](v0.4/V04C2B_ACCEPTANCE.md), [V04C2C_SPEC.md](v0.4/V04C2C_SPEC.md),
[V04C2C_REVIEW.md](v0.4/V04C2C_REVIEW.md) and [V04C2C_ACCEPTANCE.md](v0.4/V04C2C_ACCEPTANCE.md).
C2c adds manual prompt + normalized polling; pause remains unsupported/separate.

C1 read-only dashboard:

- run list and click-through detail
- state, cycle, budget, turn attempts, in-flight flag
- implementer/reviewer route and turn evidence
- decision history, blocked/recovery reasons
- manual refresh + optional 5s auto-refresh

Deferred to C2:

- live normalized output / WebSocket/SSE
- git diff summary, test status, review findings, token/cost accounting
- pause / interrupt / manual prompt / decide actions

### v0.4-D — Project & Session Management

Status: ✅ **D1 ACCEPTED / CLOSED by the owner on 2026-10-22.**  See
[V04D_SPEC.md](v0.4/V04D_SPEC.md), [V04D_REVIEW.md](v0.4/V04D_REVIEW.md) and
[V04D_ACCEPTANCE.md](v0.4/V04D_ACCEPTANCE.md).

Implemented in D1:

- multiple registered projects with explicit in-memory activation
- run-recorded session inventory (roles, run ids, latest state)
- completed/terminal runs remain visible in the bounded run list
- no arbitrary path/session id; activation is confirmation-gated

Deferred:

- persistent active-project selection
- OpenCode session switching/ownership transfer
- project add/remove over HTTP
- archived-run mutation

### v0.4-E — Packaging & GitHub Release Automation

Status: ✅ **E1 ACCEPTED / CLOSED and shipped in v0.4.0 (2026-10-22).**  The
`.exe` installer is explicitly deferred (no validated Inno Setup/code-signing
path).  See [V04E_SPEC.md](v0.4/V04E_SPEC.md), [V04E_REVIEW.md](v0.4/V04E_REVIEW.md),
[V04E_ACCEPTANCE.md](v0.4/V04E_ACCEPTANCE.md) and the v0.4.0 evidence in
[RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

Target artifacts / 目标产物：

```text
DevRelay-Portable-Windows-x64.zip   (E1, unsigned)
devrelay-<version>-py3-none-any.whl
devrelay-<version>.tar.gz
SHA256SUMS
DevRelay-Setup-Windows-x64.exe      (deferred; needs signing/Inno Setup)
```

Target release flow / 目标发布流程：

```text
tag
 ↓
CI tests
 ↓
build
 ↓
package
 ↓
checksums
 ↓
GitHub Release
```

## v0.5+ — Productization / 产品化阶段

Status: 📋 Planned

Potential directions / 潜在方向：

- Direct API execution provider as an optional alternative to OpenCode
- cross-platform packaging
- richer usage/cost dashboards
- plugin/provider ecosystem
- import/export of workflow profiles
- Windows Credential Manager / macOS Keychain / Linux Secret Service integration
- optional auto-update channel
- installation via package managers such as winget/scoop where practical

## Immediate next steps / 当前最近步骤

1. **v0.4.0 published (2026-10-22)** — tag/PyPI/GitHub Release and the portable
   asset are verified; evidence is in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).
2. Close the remaining v0.3-E platform gates (G0.4/P4, G0.5/P6, G1, G2) and decide whether recovery adoption may be enabled; `adopt_completed_turn` stays disabled until then.
3. Complete independent acceptance for v0.2-A/B/C, and close the v0.2-C E2E when Codex quota returns.
4. Address v0.4 hardening residuals: pause/session switching, persistent active
   project, prompt-marker durability, portable reproducibility/SBOM and an
   optional signed installer.  (Node.js 24 action bumps are done.)

## Long-term product goal / 长期产品目标

The intended user experience is:

目标用户体验是：

```text
Install DevRelay
      ↓
Open localhost WebUI
      ↓
Connect OpenCode
      ↓
Choose project
      ↓
Assign Implementer / Reviewer
      ↓
Connect ChatGPT
      ↓
Develop primarily from ChatGPT
      ↓
Use WebUI for configuration, monitoring and intervention
```

In short:

```text
ChatGPT = cockpit / 驾驶舱
DevRelay = orchestration & control plane / 编排与控制系统
WebUI = dashboard / 仪表盘
OpenCode = execution engine / 执行引擎
```
