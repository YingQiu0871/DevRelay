# DevRelay

> **让一个模型负责规划，让 OpenCode 中的模型负责实现与审阅，并由 DevRelay 自动完成中间交接。**  
> **Plan with one model, build and review in OpenCode, and let DevRelay automate the handoffs.**

DevRelay is a local, auditable orchestration layer for multi-model software development. Its long-term goal is to remove the repetitive copy-paste loop between a planner, an implementer, and a reviewer while keeping the human in control of scope, policy, and final decisions.

DevRelay 是一个本地运行、可审计的多模型软件开发编排层。它的长期目标，是消除“规划模型 → 编程模型 → 审阅模型”之间反复复制粘贴的机械工作，同时把范围控制、策略和最终决定保留在人手中。

## Project status / 项目状态

| Item / 项目 | Status / 状态 |
| --- | --- |
| Public release / 当前公开版本 | **v0.1.0** |
| `main` branch / 主分支 | v0.1.x public codebase |
| v0.2-C structured runtime | Implemented and offline-verified in local development; one replacement real Codex smoke remains pending because the provider is currently unavailable / 已在本地开发中实现并完成离线验证；因 Codex 当前不可用，尚缺一次真实 replacement smoke |
| v0.3-A OpenCode Session Bridge | **In progress / 开发中** |
| OpenCode-first orchestration | Planned, not yet released / 已确定方向，尚未发布 |
| ChatGPT/MCP integration | Planned / 计划中 |
| localhost WebUI | Planned / 计划中 |

**Important / 重要：** the development milestones above are not all present on `main` yet. The public, supported release remains v0.1.0 until later work is reviewed, merged, and released. / 上述开发里程碑并不都已经进入 `main`。在后续版本完成复审、合并并正式发布前，当前公开支持版本仍为 v0.1.0。

## Vision / 产品愿景

Today a typical multi-model coding workflow looks like this:

目前常见的多模型开发流程通常是：

```text
ChatGPT plans
    ↓ copy/paste
Coding agent implements
    ↓ copy/paste
Reviewer model reviews
    ↓ copy/paste
Coding agent fixes
    ↓ repeat
```

DevRelay is being built to turn that into:

DevRelay 的目标是把它变成：

```text
                    ┌──────────────────────────┐
                    │ ChatGPT                  │
                    │ Planner / Arbiter        │
                    │ 规划 / 判断 / 验收        │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ DevRelay                 │
                    │ Orchestration / Control  │
                    │ 编排 / 状态 / 策略 / 审计  │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │ OpenCode                 │
                    │ Execution Environment    │
                    ├──────────────────────────┤
                    │ Implementer: DeepSeek    │
                    │ Reviewer:    GLM         │
                    │ tools / MCP / workspace  │
                    └─────────────┬────────────┘
                                  │
                                  ▼
                    result / diff / tests / review
                                  │
                                  └──────────────→ DevRelay → ChatGPT
```

The intended responsibility split is deliberate:

这一职责划分是刻意设计的：

- **ChatGPT — Planner / Arbiter（规划与裁决）**: defines tasks, interprets review results, decides whether work should continue, stop, or require user input.
- **DevRelay — Orchestrator / Control Plane（编排与控制面）**: transports instructions and results, owns workflow state, limits loops, records evidence, and enforces local policy.
- **OpenCode — Execution Engine（执行引擎）**: provides coding-agent sessions, tools, workspace context, MCP integrations, model/provider access, and file/shell execution.
- **DeepSeek — Implementer（实现者）**: writes and fixes code.
- **GLM — Reviewer（审阅者）**: independently reviews implementation and evidence.
- **Human — Owner（最终负责人）**: controls project goals, risky actions, exceptions, release decisions, and any decision DevRelay is not authorized to make.

## Why OpenCode-first? / 为什么以 OpenCode 为第一等执行引擎？

DevRelay should orchestrate coding agents, not rebuild an entire coding-agent runtime.

DevRelay 应该负责“编排开发代理”，而不是重新实现一套完整 coding agent。

OpenCode already provides the execution environment needed by coding agents: sessions, workspace context, tools, shell/file operations, model providers, agents, and MCP. DevRelay can therefore focus on the higher-level workflow: **who works next, what evidence is required, when review happens, when a fix is requested, and when the human must be consulted.**

OpenCode 已经提供 session、工作区上下文、工具、文件与 shell 操作、模型 provider、agent 和 MCP 等执行能力。因此 DevRelay 可以专注于更高层的问题：**下一步由谁执行、需要什么证据、什么时候进入审阅、审阅不通过后如何回修，以及什么时候必须交还用户决定。**

A future **Direct API** execution mode may also be supported as an optional provider, but it is not intended to replace OpenCode as the primary interactive coding environment.

未来可增加可选的 **Direct API** 模式，但它不会取代 OpenCode 作为主要交互式代码执行环境的定位。

## What v0.1.0 already provides / v0.1.0 已实现能力

The current public release is a local CLI orchestrator with a real persisted state machine:

当前公开版本已经是一个具备持久化状态机的本地 CLI 编排器：

```text
PLAN → IMPLEMENT → TEST → REVIEW → FIX(loop) → FINAL_GATE → DONE
```

Key capabilities / 主要能力：

- Persistent task state and restart-safe workflow / 持久化任务状态与可恢复流程
- Dirty-workspace task baselines / 支持已有未提交改动的工作区基线
- Task-relative diffs instead of blindly comparing with `HEAD` / 基于任务起点而非简单 `HEAD` 的增量差异
- Repository policy guards for branch, HEAD, refs and index state / Git 分支、HEAD、引用和索引保护
- Bounded review/fix loops / 有上限的审阅与修复循环
- Official Codex CLI implementer path / 官方 Codex CLI 实现者路径
- Manual planner/reviewer handoff / 手动规划与审阅导入导出
- OpenAI-compatible reviewer provider / OpenAI-compatible reviewer provider
- Human-readable and machine-readable task evidence / 人类可读与机器可读的任务证据
- Fail-closed handling for uncertain or interrupted provider runs / 对不确定或中断执行采用 fail-closed 策略

For release details, see [CHANGELOG.md](CHANGELOG.md).

版本细节见 [CHANGELOG.md](CHANGELOG.md)。

## Development direction / 当前开发方向

The next development line moves DevRelay from a Codex-centric CLI toward an OpenCode-first orchestration platform.

下一阶段会把 DevRelay 从“以 Codex 为中心的 CLI”逐步升级为“以 OpenCode 为第一等执行环境的编排平台”。

### v0.3 — OpenCode orchestration foundation / OpenCode 编排基础

- **v0.3-A — OpenCode Session Bridge**: connect to an explicitly configured OpenCode instance, read sessions/output, send one prompt, wait with a bounded timeout, and interrupt safely.
- **v0.3-B — ChatGPT/MCP Tool Surface**: expose a narrow DevRelay control surface so ChatGPT can read state and issue the next bounded action.
- **v0.3-C — Agent Role Routing**: explicitly bind planner / implementer / reviewer roles, e.g. ChatGPT / DeepSeek / GLM.
- **v0.3-D — Bounded Orchestration Loop**: automate IMPLEMENT → REVIEW → FIX cycles without allowing an unbounded autonomous loop.
- **v0.3-E — Recovery & Hardening**: replay safety, crash recovery, duplicate-action prevention, call accounting, and security hardening.

### v0.4 — Local Web Control Plane / 本地 Web 控制面

The planned GUI is a **localhost WebUI**, not a heavy desktop application.

计划中的 GUI 是 **localhost WebUI**，而不是笨重的传统桌面客户端。

Planned surfaces / 计划页面：

- Dashboard / 总览
- Projects & workspaces / 项目与工作区
- OpenCode connection & sessions / OpenCode 连接与 session
- Agent roles & model selection / Agent 角色与模型选择
- Workflow gates & maximum repair rounds / 流程门槛与最大修复轮数
- ChatGPT/MCP connection / ChatGPT/MCP 连接状态
- Provider configuration / Provider 配置
- Usage & call accounting / 调用量与费用统计
- Logs & audit trail / 日志与审计轨迹
- Pause / interrupt / manual intervention / 暂停、中断与人工干预

The WebUI will be the primary configuration and monitoring interface. Configuration files will remain available as a durable storage and advanced-user surface, but ordinary users should not need to edit YAML by hand.

WebUI 将成为主要配置与监控入口。配置文件仍会作为持久化存储和高级用户接口保留，但普通用户不应被迫手工编辑 YAML。

## Configuration philosophy / 配置设计原则

Target user experience / 目标体验：

```text
Install DevRelay
      ↓
Open http://127.0.0.1:<port>
      ↓
Detect / connect OpenCode
      ↓
Select workspace
      ↓
Choose Implementer (e.g. DeepSeek)
      ↓
Choose Reviewer (e.g. GLM)
      ↓
Connect ChatGPT
      ↓
Test configuration
      ↓
Ready
```

Secrets such as API keys should not be stored in ordinary project configuration files. The planned WebUI should use OS credential storage where possible and expose only credential references to DevRelay configuration.

API Key 等敏感凭据不应以明文形式写入普通项目配置。计划中的 WebUI 应尽可能使用操作系统凭据存储，并只在 DevRelay 配置中保存凭据引用。

## Quick start — v0.1.0 / 快速开始 — v0.1.0

Requirements / 要求：Python >= 3.11, Git, and a repository with at least one commit.

```bash
# from a source checkout
python -m pip install .

cd your-project
devrelay init
devrelay doctor
devrelay start "Describe the task"
devrelay status
```

The current public release is still CLI-first. OpenCode bridge, ChatGPT control, and the WebUI are development roadmap items and should not be assumed to exist in v0.1.0.

当前公开版本仍以 CLI 为主。OpenCode Bridge、ChatGPT 控制以及 WebUI 都属于后续开发路线，不应被误认为已经存在于 v0.1.0。

## Documentation / 文档

- [Roadmap / 实现路线图](docs/ROADMAP.md)
- [Project Status / 已实现与未实现状态](docs/PROJECT_STATUS.md)
- [Architecture / 架构与职责边界](docs/ARCHITECTURE.md)
- [Changelog / 版本记录](CHANGELOG.md)
- [Contributing / 贡献指南](CONTRIBUTING.md)
- [Release Checklist / 发布检查](docs/RELEASE_CHECKLIST.md)
- [PyPI Publishing / PyPI 发布](docs/PYPI_PUBLISHING.md)

## Safety and control / 安全与控制原则

DevRelay is intentionally not designed as an unlimited autonomous coding loop.

DevRelay 不以“无限自主循环”为目标。

Core principles / 核心原则：

- explicit workspace and session ownership / 明确绑定工作区与 session
- bounded retries and repair rounds / 有上限的重试和修复轮数
- no hidden provider retries / 不进行隐藏的模型重试
- explicit call accounting / 明确记录外部调用
- fail closed when state or evidence is uncertain / 状态或证据不确定时 fail closed
- reviewer and implementer remain separate roles / 审阅者与实现者保持角色隔离
- the implementer cannot approve its own work / 实现者不能自行批准自己的结果
- high-risk or ambiguous decisions return to the user / 高风险或存在歧义的决定交还用户

## Distribution goal / 分发目标

The long-term distribution target is GitHub Releases with a low-friction Windows package, plus developer-oriented package formats.

长期分发目标是通过 GitHub Releases 提供低门槛 Windows 安装包，同时保留开发者安装方式。

Planned examples / 计划形式：

```text
DevRelay-Setup-Windows-x64.exe
DevRelay-Portable-Windows-x64.zip
devrelay-<version>-py3-none-any.whl
SHA256SUMS.txt
```

A future release pipeline should build, test, checksum, and publish these artifacts automatically from a version tag.

未来发布流水线应能够从版本 tag 自动完成测试、构建、校验和发布。

## License / 许可证

See [LICENSE](LICENSE).
