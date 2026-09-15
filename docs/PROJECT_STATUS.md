# DevRelay Project Status / DevRelay 项目状态

This document is the status ledger for DevRelay. It intentionally distinguishes released code from local/unreleased development evidence.

本文档是 DevRelay 的状态台账，刻意区分已经发布的代码与仍处于本地/未发布状态的开发证据。

## Current public release / 当前公开版本

**v0.1.0** on `main`.

The public repository currently supports the v0.1 CLI-centric workflow. Later milestones described below must not be presented as released capability until reviewed, merged, tagged, and published.

当前公开仓库支持 v0.1 的 CLI 工作流。下述后续里程碑只有在完成复审、合并、打 tag 并正式发布后，才可以作为“已发布能力”对外描述。

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
| Structured Codex runtime / 结构化 Codex runtime | ❌ | 🧪 Implemented offline | v0.2-C candidate |
| Strict structured schema / 严格结构化 schema | ❌ | ✅ Real endpoint acceptance verified | Replacement smoke confirmed no `invalid_json_schema`; full E2E delivery still pending |
| Completion replay / Completion replay | ❌ | 🧪 Implemented offline | v0.2-C candidate |
| Control-plane PRE/POST guard / 控制面 PRE/POST guard | ❌ | 🧪 Implemented offline | v0.2-C candidate |
| OpenCode session bridge / OpenCode session bridge | ❌ | 🚧 In progress | v0.3-A |
| ChatGPT/MCP tool surface / ChatGPT/MCP 工具面 | ❌ | 📋 Planned | v0.3-B |
| Explicit DeepSeek implementer routing / DeepSeek 实现者路由 | ❌ | 📋 Planned | v0.3-C |
| Explicit GLM reviewer routing / GLM 审阅者路由 | ❌ | 📋 Planned | v0.3-C |
| Automated bounded orchestration / 自动有界编排 | ❌ | 📋 Planned | v0.3-D |
| localhost WebUI / localhost WebUI | ❌ | 📋 Planned | v0.4 |
| GitHub packaged Windows installer / GitHub Windows 安装包 | ❌ | 📋 Planned | v0.4-E |
| Direct API execution mode / Direct API 执行模式 | ❌ | 📋 Optional future | v0.5+ |

## v0.2-C status / v0.2-C 状态

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

## v0.3-A status / v0.3-A 状态

**In progress / 开发中**

Scope is deliberately narrow:

- explicit OpenCode endpoint
- list/select/read one OpenCode session
- normalized message/output model
- send exactly one prompt operation
- bounded wait
- interrupt when supported
- capability/error normalization
- workspace/session ownership validation
- offline deterministic fake/stub coverage

Deliberately excluded from v0.3-A:

- ChatGPT/MCP connector exposure
- DeepSeek/GLM automatic role routing
- autonomous review/fix loops
- acceptance decisions inside DevRelay
- GUI/WebUI

This narrowness is intentional: first prove a reliable read/write bridge to OpenCode, then build orchestration above it.

这一阶段刻意保持狭窄：先证明 DevRelay 能可靠地读写 OpenCode，再在其上构建自动编排。

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

只有生产代码存在、相关离线测试通过、文档真实描述行为与限制、无已知 P0/P1 阻塞，并且所需真实 provider smoke 已通过或明确标记为外部待办时，才可以标记为“已实现”。只有在合并至发布分支、完成版本化/tag 并正式发布后，才能标记为“已发布”。

## Next gates / 下一步门槛

1. Resume and complete v0.3-A implementation report.
2. Independently review v0.3-A before v0.3-B begins.
3. Investigate the Windows Codex shell-policy P2 offline; do not spend another real Codex call on diagnosis.
4. Keep v0.2-C E2E closure pending until provider quota returns and a later authorized smoke can reach structured-result delivery.
5. Only after v0.3-A is accepted, design the ChatGPT/MCP tool surface.
6. Only after v0.3-B is accepted, add explicit implementer/reviewer role routing.
