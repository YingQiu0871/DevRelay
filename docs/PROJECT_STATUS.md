# DevRelay Project Status / DevRelay 项目状态

This document is the status ledger for DevRelay. It intentionally distinguishes released code from local/unreleased development evidence.

本文档是 DevRelay 的状态台账，刻意区分已经发布的代码与仍处于本地/未发布状态的开发证据。

## Current public release / 当前公开版本

**v0.3.0** on `main` (2026-10-21), published to
[PyPI](https://pypi.org/project/devrelay/0.3.0/) and
[GitHub Releases](https://github.com/YingQiu0871/DevRelay/releases/tag/v0.3.0).

The public repository supports the v0.3 orchestration line: the v0.1 CLI workflow plus the v0.3 OpenCode-first orchestration surface. Publication evidence is recorded in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md); later milestones described below must not be presented as released capability until reviewed, merged, tagged, and published.

**v0.4.0 release candidate:** the A/B/C/D1/E1 stages are accepted and prepared on `main` (version `0.4.0`), but **not yet published**.  See [release notes](v0.4/RELEASE_NOTES_v0.4.0.md) and the v0.4.0 checklist section; public installation remains `0.3.0` until the owner tags/drafts/dispatches.

当前公开仓库支持 v0.3 编排线：v0.1 的 CLI 工作流，加上 v0.3 的 OpenCode-first 编排能力。发布证据记录在 [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)；下述后续里程碑只有在完成复审、合并、打 tag 并正式发布后，才可以作为“已发布能力”对外描述。

## Capability matrix / 能力矩阵

| Capability / 能力 | Released / 已发布 | Development status / 开发状态 | Notes / 说明 |
| --- | --- | --- | --- |
| Persistent task state machine / 持久化任务状态机 | ✅ | Stable | v0.1 |
| Dirty workspace baseline / Dirty workspace 基线 | ✅ | Stable | v0.1 |
| Task-relative diff / 任务相对差异 | ✅ | Stable | v0.1 |
| Repository policy guards / 仓库策略保护 | ✅ | Stable | v0.1 |
| Bounded review/fix loop / 有上限的审阅修复循环 | ✅ | Stable | v0.1 |
| Codex CLI implementer / Codex CLI 实现者 | ✅ | Existing | Public path in v0.1 |
| Manual planner/reviewer import/export / 手动规划与审阅导入导出 | ✅ | Existing | v0.1 |
| OpenAI-compatible reviewer / OpenAI-compatible reviewer | ✅ | Existing | v0.1 |
| v0.2-A automatic review loop / 自动审阅循环 | ✅ | Candidate; independent acceptance incomplete | Shipped in 0.3.0; offline / fake-provider evidence only |
| v0.2-B project profiles and frozen policy / 项目 profile 与冻结策略 | ✅ | Candidate; independent acceptance incomplete | Shipped in 0.3.0; offline / fake-provider evidence only |
| Structured Codex runtime / 结构化 Codex runtime | ✅ | 🧪 Candidate; E2E closure pending | v0.2-C, shipped in 0.3.0 |
| Strict structured schema / 严格结构化 schema | ✅ | 🧪 Candidate; E2E closure pending | v0.2-C, shipped in 0.3.0; real endpoint acceptance verified |
| Completion replay / Completion replay | ✅ | 🧪 Candidate; E2E closure pending | v0.2-C, shipped in 0.3.0 |
| Control-plane PRE/POST guard / 控制面 PRE/POST guard | ✅ | 🧪 Candidate; E2E closure pending | v0.2-C, shipped in 0.3.0 |
| OpenCode session bridge / OpenCode session bridge | ✅ | Stable | v0.3-A, shipped in 0.3.0 |
| ChatGPT/MCP tool surface / ChatGPT/MCP 工具面 | ✅ | Stable | v0.3-B, shipped in 0.3.0 (19 tools, local stdio) |
| Explicit DeepSeek implementer routing / DeepSeek 实现者路由 | ✅ | Stable | v0.3-C, shipped in 0.3.0 |
| Explicit GLM reviewer routing / GLM 审阅者路由 | ✅ | Stable | v0.3-C, shipped in 0.3.0 |
| Automated bounded orchestration / 自动有界编排 | ✅ | Stable | v0.3-D, shipped in 0.3.0 |
| Recovery and hardening (fail-closed core) / 恢复与加固（fail-closed 核心） | ✅ | Released with constraints | v0.3-E, shipped in 0.3.0; adoption disabled; platform gates open |
| localhost WebUI / localhost WebUI | 🧪 v0.4.0 candidate | Accepted; publication pending | A/B/C/D1 |
| Run/task dashboards, decision/interrupt, manual prompt/polling | 🧪 v0.4.0 candidate | Accepted; publication pending | C1/C2a/C2b/C2c |
| Project activation + session inventory | 🧪 v0.4.0 candidate | Accepted; in-memory selection | D1 |
| Windows portable zip / Windows portable zip | 🧪 v0.4.0 candidate | E1 accepted; unsigned | v0.4-E1 |
| GitHub packaged Windows installer / GitHub Windows 安装包 | ❌ | 📋 Deferred (signing/Inno Setup) | v0.4-E2 |
| Direct API execution mode / Direct API 执行模式 | ❌ | 📋 Optional future | v0.5+ |

## v0.2-C status / v0.2-C 状态

**Later status (2026-10-21):** v0.2-C shipped as a candidate inside 0.3.0; the E2E closure items below remain open. / 后续状态（2026-10-21）：v0.2-C 已作为候选随 0.3.0 发布；下文 E2E 闭环项仍未完成。

The replacement real Codex smoke was executed once against candidate `4790ca3` with the reviewed schema SHA-256 `1a28d999f4b50003315fe6c9d292dee45d52a6eb59673df00ffe8442b72d18bf`.

一次 replacement real Codex smoke 已针对候选版本 `4790ca3` 执行，使用的 schema SHA-256 与复审值一致：`1a28d999f4b50003315fe6c9d292dee45d52a6eb59673df00ffe8442b72d18bf`。

What is now proven / 当前已证明：

- exactly one real Codex call was issued;
- the reviewed annotation-free schema was accepted by the real endpoint;
- the previous `invalid_json_schema` regression is fixed;
- no real reviewer API call occurred;
- control-plane PRE/POST comparison remained clean;
- no hidden retry or repair call occurred.

What remains unproven / 尚未证明：

- full end-to-end structured-result delivery through `--output-last-message`;
- result staging, persistence and reconciliation against a successful real turn;
- real completion reaching `COMPLETION_APPLIED`.

The real turn ended with provider usage-limit failure before the structured result file was produced. Therefore v0.2-C is **not fully closed**, but the schema defect itself is no longer an open blocker.

真实调用在结构化结果文件写出前因 provider 使用额度耗尽而失败。因此 v0.2-C **尚未完全闭环**，但原有 schema 缺陷已经被真实端点证明修复。

### New Windows runtime P2 / 新增 Windows runtime P2

The smoke also surfaced a separate Windows-host issue: Codex shell `exec_command` operations were rejected by policy when resolving the WindowsApps `pwsh.exe` alias. This was not authorized for repair during the smoke and remains an investigation item.

本次 smoke 还暴露了一个独立的 Windows 主机问题：Codex 的 shell `exec_command` 在解析 WindowsApps 的 `pwsh.exe` alias 时被 policy 拒绝。Smoke 阶段未授权修改，因此该问题作为独立调查项保留。

Current classification / 当前分类：

- P0: none attributable to DevRelay
- P1: real end-to-end structured delivery remains unproven
- P2: Windows shell policy / `pwsh.exe` execution compatibility requires offline investigation before the next real implementation smoke
- P3: model-quality artifact observed during smoke, not treated as a DevRelay defect

No additional real Codex call should be attempted until quota is available and the Windows P2 has first been investigated offline.

在额度恢复且 Windows P2 先完成离线调查之前，不应再次进行真实 Codex 调用。

## v0.3 release scope / v0.3 发布范围

**Released in 0.3.0 (2026-10-21). / 已随 0.3.0 发布（2026-10-21）。**

- **v0.3-A — OpenCode Session Bridge**: an explicit OpenCode endpoint, session list/read, exactly one prompt, bounded wait, interruption, workspace/session ownership validation, and deterministic offline fake/stub coverage. / 显式 OpenCode endpoint、session 列出/读取、只发送一条 prompt、有界等待、interrupt、工作区/session 归属校验，以及确定性的离线 fake/stub 覆盖。
- **v0.3-B — ChatGPT/MCP Tool Surface**: `devrelay mcp serve --workspace <project>` over local stdio with 19 tools (eleven `devrelay_*`, eight `opencode_*`); HTTP/SSE and product-native ChatGPT distribution are not released. / 通过本地 stdio 提供 `devrelay mcp serve --workspace <project>`，共 19 个工具（11 个 `devrelay_*`、8 个 `opencode_*`）；HTTP/SSE 与产品级 ChatGPT 分发尚未发布。
- **v0.3-C — Agent Role Routing**: semantic implementer/reviewer roles with no fallback and no silent override; DeepSeek and GLM bindings are explicit and auditable. / 语义化 implementer/reviewer 角色，无 fallback、无静默覆盖；DeepSeek 与 GLM 绑定显式且可审计。
- **v0.3-D — Bounded Orchestration Loop**: durable run state, `max_cycles` 1–3, at most `2 × max_cycles` model turns, `AWAITING_DECISION`, and no automatic acceptance. / 持久化 run 状态、`max_cycles` 1–3、最多 `2 × max_cycles` 个模型轮次、`AWAITING_DECISION`，且不自动接受。
- **v0.3-E — Recovery & Hardening**: the mandatory fail-closed core only — read-only reconcile plus a one-shot `mark_unrecoverable`; `adopt_completed_turn` stays disabled, there is no automatic resume, remote correlation was not exercised, and the platform proof gate remains partially executed (G0.1/P7, G0.2, G0.3/P5 PASS; G0.4/P4 authoritative FAIL / P4 UNPROVEN; G0.5/P6 NOT RUN; G1/G2 not run). / 仅强制 fail-closed 核心：只读 reconcile 与一次性 `mark_unrecoverable`；`adopt_completed_turn` 仍禁用，没有自动 resume，远端关联未演练，平台证明门仍为部分执行（G0.1/P7、G0.2、G0.3/P5 PASS；G0.4/P4 authoritative FAIL / P4 UNPROVEN；G0.5/P6 NOT RUN；G1/G2 未运行）。

## Product decisions already made / 已确定的产品决策

### 1. OpenCode is the primary execution engine / OpenCode 是主要执行引擎

DevRelay will not try to rebuild shell/file/MCP/session/provider functionality that OpenCode already provides.

DevRelay 不重新实现 OpenCode 已经提供的 shell、文件操作、MCP、session 和 provider runtime。

### 2. ChatGPT is the planner/arbiter / ChatGPT 是规划与裁决层

The target workflow keeps high-level planning and acceptance judgment outside the implementer.

目标流程把高层规划与验收判断置于实现者之外。

### 3. Implementer and reviewer remain separate / 实现者与审阅者保持隔离

A typical target configuration is:

```text
Planner     = ChatGPT
Implementer = DeepSeek in OpenCode
Reviewer    = GLM in OpenCode
```

The implementer must not approve its own work.

### 4. WebUI is a control plane, not the coding engine / WebUI 是控制面，不是编程引擎

The planned localhost WebUI is for configuration, monitoring, usage, logs, and intervention. Day-to-day planning should still be possible from ChatGPT.

计划中的 localhost WebUI 用于配置、监控、调用量、日志和人工干预；日常规划与推进应仍可主要通过 ChatGPT 完成。

### 5. Automation must be bounded / 自动化必须有界

DevRelay should never silently become an infinite autonomous loop.

Planned gates include:

- maximum repair rounds
- maximum external calls
- explicit stop severities
- `BLOCKED`
- `NEEDS_USER_DECISION`
- crash/replay safeguards

## Definition of "implemented" / “已实现”的定义

A feature should be marked **implemented** only when:

1. production code exists;
2. relevant offline tests pass;
3. documentation describes the real behavior and limitations;
4. no known P0/P1 blocker remains for that feature;
5. any required real-provider smoke is either passed or explicitly marked as an external pending gate.

A feature should be marked **released** only after it is merged into the release branch, versioned/tagged, and published.

v0.3.0 meets that bar through the annotated `v0.3.0` tag and the publication record in [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md).

只有生产代码存在、相关离线测试通过、文档真实描述行为与限制、无已知 P0/P1 阻塞，并且所需真实 provider smoke 已通过或明确标记为外部待办时，才可以标记为“已实现”。只有在合并至发布分支、完成版本化/tag 并正式发布后，才能标记为“已发布”。v0.3.0 通过 annotated `v0.3.0` tag 与 [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md) 中的发布记录满足该门槛。

## Next gates / 下一步门槛

1. Prepare the **v0.4.0 release**: bump the version, freeze release docs, run
   the full suite and release-workflow checks, then the owner tags/publishes.
   E1 is accepted; the portable zip will be built for the first time on the
   real release tag.
2. The **hardening pass** is recorded in
   [HARDENING_v0.4.md](HARDENING_v0.4.md); remaining items are explicit
   residuals, not hidden assumptions.
2. Close the remaining v0.3-E platform gates (G0.4/P4, G0.5/P6, G1, G2) and decide whether recovery adoption may be enabled; `adopt_completed_turn` stays disabled until then.
3. Complete independent acceptance for v0.2-A/B/C, and close the v0.2-C E2E when provider quota returns.
4. Investigate the Windows Codex shell-policy P2 offline; do not spend another real Codex call on diagnosis.
