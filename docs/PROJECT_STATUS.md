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
| Strict structured schema / 严格结构化 schema | ❌ | 🧪 Offline verified | Real replacement smoke pending |
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

The latest development review reports the structured Codex runtime candidate as offline-clean and ready for one replacement real smoke. The schema hygiene review found no new P0/P1/P2 blockers and approved one real smoke.

最新开发复审报告认为 v0.2-C structured Codex runtime 候选版本离线验证通过，并允许进行一次 replacement real smoke。Schema hygiene 最终复审未发现新的 P0/P1/P2 阻塞项。

Current unresolved acceptance item / 当前唯一关键未闭环项：

- one replacement real Codex smoke against the real provider endpoint.

Because Codex is currently unavailable to the project owner, this item is **externally blocked**. It must stay explicitly pending; documentation must not silently convert it to PASS.

由于项目当前无法使用 Codex，该项处于 **外部条件阻塞** 状态。文档必须继续明确标记为待完成，不能把它静默改写成 PASS。

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

1. Complete v0.3-A implementation report.
2. Independently review v0.3-A before v0.3-B begins.
3. Keep v0.2-C real Codex smoke pending until provider access returns.
4. Only after v0.3-A is accepted, design the ChatGPT/MCP tool surface.
5. Only after v0.3-B is accepted, add explicit implementer/reviewer role routing.
