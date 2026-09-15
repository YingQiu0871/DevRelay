# DevRelay Roadmap / DevRelay 实现路线图

This roadmap separates **released**, **implemented but unreleased**, **in progress**, and **planned** work. Items move forward only after review, evidence, and release gates are satisfied.

本路线图区分 **已发布**、**已实现但未发布**、**开发中** 与 **计划中**。只有在复审、证据和发布门槛满足后，功能才进入下一个状态。

## Status legend / 状态说明

- ✅ **Released / 已发布**
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

Status: 🧪 Implemented in development history, not released on `main` as a public version.

方向：强化自动 review、控制状态、迁移与调用记账等基础能力。

### v0.2-C — Structured Codex Runtime

Status: 🧪 + ⏸

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

Status: 🚧 In progress

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

Status: 📋 Planned

Goal: expose a narrow, explicit DevRelay tool surface so ChatGPT can inspect state, read evidence, and issue the next bounded action.

计划能力：

- read project/task/session status
- read normalized implementer/reviewer output
- inspect diff/test/review evidence
- issue one bounded next action
- interrupt/pause
- return `NEEDS_USER_DECISION` when human input is required

### v0.3-C — Agent Role Routing

Status: 📋 Planned

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

Status: 📋 Planned

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

Status: 📋 Planned

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

Status: 📋 Planned

- bind localhost by default
- authenticated local session
- origin/CSRF protection
- validated project/workspace registry
- no arbitrary filesystem browsing
- backend-owned config mutation

### v0.4-B — WebUI Configuration

Status: 📋 Planned

Planned configuration surfaces:

- OpenCode endpoint and compatibility
- project/workspace selection
- implementer/reviewer role assignment
- model selection
- workflow limits
- ChatGPT/MCP connection
- provider credentials by reference, not plaintext config

### v0.4-C — Dashboard & Live Runs

Status: 📋 Planned

Dashboard targets:

- active project
- current stage
- implementer/reviewer state
- live normalized output
- git diff summary
- test status
- review findings
- call/token/cost accounting where available
- pause / interrupt / manual prompt

### v0.4-D — Project & Session Management

Status: 📋 Planned

- multiple registered projects
- explicit OpenCode session ownership
- session history
- safe session switching
- archived/completed runs

### v0.4-E — Packaging & GitHub Release Automation

Status: 📋 Planned

Target artifacts / 目标产物：

```text
DevRelay-Setup-Windows-x64.exe
DevRelay-Portable-Windows-x64.zip
devrelay-<version>-py3-none-any.whl
SHA256SUMS.txt
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

1. Resume and complete **v0.3-A OpenCode Session Bridge**.
2. Independently review v0.3-A before starting v0.3-B.
3. Investigate the v0.2-C Windows Codex shell-policy P2 offline in parallel, without another real Codex call.
4. When Codex quota becomes available again, authorize a later minimal E2E smoke only after the Windows issue is understood.
5. Keep the public release at v0.1.0 until unreleased milestones are reviewed and intentionally promoted.

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
