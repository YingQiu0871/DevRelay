# DevRelay

> **让一个模型负责规划，让 OpenCode 中的模型负责实现与审阅，并由 DevRelay 自动完成中间交接。**  
> **Plan with one model, build and review in OpenCode, and let DevRelay automate the handoffs.**

DevRelay is a local, auditable orchestration layer for multi-model software development. Its long-term goal is to remove the repetitive copy-paste loop between a planner, an implementer, and a reviewer while keeping the human in control of scope, policy, and final decisions.

DevRelay 是一个本地运行、可审计的多模型软件开发编排层。它的长期目标，是消除“规划模型 → 编程模型 → 审阅模型”之间反复复制粘贴的机械工作，同时把范围控制、策略和最终决定保留在人手中。

## Project status / 项目状态

| Item / 项目 | Status / 状态 |
| --- | --- |
| Public release / 当前公开版本 | **v0.4.0** (2026-10-22) |
| `main` branch / 主分支 | v0.4.0 release line / v0.4.0 发布线 |
| v0.2-A / v0.2-B / v0.2-C | Included in 0.3.0; independent acceptance not complete; offline / fake-provider evidence only / 已随 0.3.0 发布；独立验收尚未完成，仅有离线/假 provider 证据 |
| v0.3-A OpenCode Session Bridge | Accepted / closed / shipped in 0.3.0 / 已验收、关闭并随 0.3.0 发布 |
| v0.3-B ChatGPT/MCP Tool Surface | Accepted / closed / shipped in 0.3.0 / 已验收、关闭并随 0.3.0 发布 |
| v0.3-C Agent Role Routing | Accepted / closed / shipped in 0.3.0 / 已验收、关闭并随 0.3.0 发布 |
| v0.3-D Bounded Orchestration Loop | Accepted / closed / shipped in 0.3.0 / 已验收、关闭并随 0.3.0 发布 |
| v0.3-E Recovery & Hardening | Mandatory fail-closed core accepted (P0=0, P1=0, P2=2; 2026-10-17) / adoption disabled / platform gates open / shipped in 0.3.0 / 强制 fail-closed 核心已验收（P0=0、P1=0、P2=2；2026-10-17）；adoption 仍关闭；平台门未闭合；已随 0.3.0 发布 |
| OpenCode-first orchestration | Shipped in 0.3.0 / 已随 0.3.0 发布 |
| ChatGPT/MCP integration | Local stdio MCP surface shipped (19 tools); product-native ChatGPT distribution not released / 本地 stdio MCP 面已发布（19 个工具）；产品级 ChatGPT 分发尚未发布 |
| localhost WebUI | Accepted / closed; shipped in 0.4.0 / 已验收、关闭并随 0.4.0 发布 |
| v0.4-A/B/C/D1/E1 | Accepted / closed; shipped in 0.4.0 / 已验收、关闭并随 0.4.0 发布 |
| v0.4 portable Windows zip | E1 accepted; shipped unsigned / E1 已验收；已发布，未签名 |

**Release status / 发布状态：** `v0.4.0` supersedes `v0.3.0` and is published on [PyPI](https://pypi.org/project/devrelay/0.4.0/) and [GitHub Releases](https://github.com/YingQiu0871/DevRelay/releases/tag/v0.4.0); the tag-driven workflow and recorded evidence are in [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md). v0.2-A/B/C ship inside 0.3.0/0.4.0 but are not separately released v0.2 stages; their independent acceptance is not complete. / `v0.4.0` 取代 `v0.3.0`，已发布至 [PyPI](https://pypi.org/project/devrelay/0.4.0/) 与 [GitHub Release](https://github.com/YingQiu0871/DevRelay/releases/tag/v0.4.0)；tag 驱动流程与记录见 [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md)。v0.2-A/B/C 随 0.3.0/0.4.0 一起交付，但不是单独的 v0.2 发布阶段；它们的独立验收尚未完成。

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

## What v0.3.0 provides / v0.3.0 已实现能力

v0.3.0 keeps the v0.1 orchestration loop and adds an explicit OpenCode-first execution path on top of it:

v0.3.0 保留了 v0.1 的编排循环，并在其上增加了明确的 OpenCode-first 执行路径：

```text
PLAN → IMPLEMENT → TEST → REVIEW → FIX(loop) → FINAL_GATE → DONE
```

Key capabilities / 主要能力：

- **v0.1 foundation**: persistent task state, dirty-workspace baselines, task-relative diffs, repository policy guards, bounded review/fix loops, the official Codex CLI implementer, human/machine-readable evidence, and fail-closed handling of uncertain runs. / **v0.1 基础**：持久化任务状态、dirty 工作区基线、任务相对 diff、仓库策略保护、有上限的审阅/修复循环、官方 Codex CLI 实现者、人类/机器可读证据，以及对不确定执行的 fail-closed 处理。
- **v0.2-A/B/C (candidates included in 0.3.0)**: automatic review loop, project profiles and frozen policy, and the structured Codex runtime. Their independent acceptance is not complete; the evidence is offline / fake-provider only. / **v0.2-A/B/C（作为候选随 0.3.0 发布）**：自动审阅循环、项目 profile 与冻结策略、结构化 Codex runtime；独立验收尚未完成，只有离线/假 provider 证据。
- **v0.3-A OpenCode session bridge**: an explicit OpenCode endpoint, list/read sessions, send one prompt, bounded wait, interrupt, and normalized output. / **v0.3-A OpenCode session bridge**：显式 OpenCode endpoint、列出/读取 session、发送一条 prompt、有界等待、interrupt，以及标准化输出。
- **v0.3-B ChatGPT/MCP tool surface**: `devrelay mcp serve --workspace <project>` exposes 19 tools over local stdio. / **v0.3-B ChatGPT/MCP 工具面**：`devrelay mcp serve --workspace <project>` 通过本地 stdio 暴露 19 个工具。
- **v0.3-C agent role routing**: semantic implementer/reviewer roles with no fallback and no silent override. / **v0.3-C Agent 角色路由**：implementer/reviewer 语义角色，无 fallback、无静默覆盖。
- **v0.3-D bounded orchestration loop**: durable run state, `max_cycles` 1–3, at most `2 × max_cycles` model turns, `AWAITING_DECISION`, and never automatic acceptance. / **v0.3-D 有界编排循环**：持久化 run 状态、`max_cycles` 1–3、最多 `2 × max_cycles` 个模型轮次、`AWAITING_DECISION`，且从不自动接受。
- **v0.3-E recovery and hardening**: read-only reconcile plus a one-shot `mark_unrecoverable`; adoption stays disabled and the platform gates stay open. / **v0.3-E 恢复与加固**：只读 reconcile 与一次性 `mark_unrecoverable`；adoption 仍关闭，平台门未闭合。

The offline suite runs 1,271 tests on Python 3.11–3.14, with Linux and Windows CI jobs; releases are created by a tag-driven workflow. / 离线测试套件在 Python 3.11–3.14 上运行 1,271 项测试，CI 覆盖 Linux 与 Windows；发布由 tag 驱动工作流完成。

`devrelay mcp serve --workspace <project>` exposes 19 tools over local stdio, including `devrelay_*` and `opencode_*`. HTTP/SSE, multi-workspace serving, and product-native ChatGPT distribution are not released.

`devrelay mcp serve --workspace <project>` 通过本地 stdio 暴露 19 个工具，包括 `devrelay_*` 与 `opencode_*`。HTTP/SSE、多工作区服务以及产品级 ChatGPT 分发尚未发布。

For release details, see [CHANGELOG.md](CHANGELOG.md).

版本细节见 [CHANGELOG.md](CHANGELOG.md)。

## Development direction / 当前开发方向

v0.3 shipped the OpenCode orchestration foundation. The next development line is v0.4, the local Web control plane.

v0.3 已交付 OpenCode 编排基础。下一阶段开发是 v0.4，即本地 Web 控制面。

### v0.3 — OpenCode orchestration foundation / OpenCode 编排基础

All five v0.3 stages shipped in 0.3.0:

五个 v0.3 阶段均已随 0.3.0 发布：

- **v0.3-A — OpenCode Session Bridge** (shipped in 0.3.0): connect to an explicitly configured OpenCode instance, read sessions/output, send one prompt, wait with a bounded timeout, and interrupt safely.
- **v0.3-B — ChatGPT/MCP Tool Surface** (shipped in 0.3.0): expose a narrow DevRelay control surface so ChatGPT can read state and issue the next bounded action.
- **v0.3-C — Agent Role Routing** (shipped in 0.3.0): explicitly bind planner / implementer / reviewer roles, e.g. ChatGPT / DeepSeek / GLM.
- **v0.3-D — Bounded Orchestration Loop** (shipped in 0.3.0): automate IMPLEMENT → REVIEW → FIX cycles without allowing an unbounded autonomous loop.
- **v0.3-E — Recovery & Hardening** (shipped in 0.3.0; mandatory core only; adoption disabled; platform gates open): replay safety, crash recovery, duplicate-action prevention, call accounting, and security hardening.

### v0.4 — Local Web Control Plane / 本地 Web 控制面

Status: planned; not started.

状态：计划中，尚未开始。

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

## Quick start — v0.4.0 / 快速开始 — v0.4.0

Requirements / 要求：Python >= 3.11, Git, and a repository with at least one commit.

```bash
# from this release tree
python -m pip install .

# or isolated
pipx install .

# from PyPI (published; evidence in docs/RELEASE_CHECKLIST.md)
python -m pip install devrelay==0.4.0
```

In your project / 在项目目录中：

```bash
devrelay init
devrelay start "Describe the task"
devrelay plan import ...
devrelay continue
devrelay status
devrelay usage
devrelay diff
devrelay logs
devrelay mcp serve --workspace .
```

Until the release workflow completes, `pip install devrelay` still resolves to v0.1.0; the actual results are recorded in [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md).

在发布工作流完成之前，`pip install devrelay` 仍会解析到 v0.1.0；实际结果以 [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) 为准。

## Current limitations / 当前限制

- v0.2-A/B/C are candidates included in 0.3.0; their independent acceptance is not complete, and the evidence is fake-provider / offline only. / v0.2-A/B/C 只是随 0.3.0 交付的候选特性；独立验收尚未完成，证据仅限假 provider / 离线测试。
- v0.3-E ships only the mandatory fail-closed recovery core: `adopt_completed_turn` remains disabled, there is no automatic resume, and remote correlation has not been exercised in practice. / v0.3-E 只发布了强制 fail-closed 恢复核心：`adopt_completed_turn` 仍处于禁用状态，没有自动 resume，远端关联（remote correlation）尚未实际演练。
- The orchestration store fsyncs only temporary files and POSIX parent directories; Windows has no directory fsync, the OpenCode ledger has no fsync, and there is a single writer. / 编排存储只对临时文件与 POSIX 父目录执行 fsync；Windows 没有目录 fsync，OpenCode ledger 没有 fsync，且只支持单 writer。
- Platform gates: G0.1/P7, G0.2, and G0.3/P5 PASS; G0.4/P4 is an authoritative FAIL / P4 UNPROVEN; G0.5/P6 NOT RUN; G1 and G2 were not run. / 平台门：G0.1/P7、G0.2、G0.3/P5 PASS；G0.4/P4 为 authoritative FAIL / P4 UNPROVEN；G0.5/P6 NOT RUN；G1、G2 未运行。
- MCP is stdio-only: no HTTP/SSE, no multi-workspace serving, and no product-native ChatGPT distribution. / MCP 仅支持 stdio：没有 HTTP/SSE，不支持多工作区服务，也没有产品级 ChatGPT 分发。
- One active task, one Codex implementer, no WebUI; push prevention and secret redaction are best-effort. / 同一时间只有一个活动任务、一个 Codex 实现者，没有 WebUI；push 防护与密钥脱敏都是 best-effort。

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

v0.4.0 ships a PyPI wheel/sdist, a GitHub Release and an unsigned portable
Windows zip.  A signed `.exe` installer remains deferred.

v0.4.0 已提供 PyPI wheel/sdist、GitHub Release 与**未签名**的 Windows portable
zip；带签名的 `.exe` 安装包仍延后。

Artifacts / 产物：

```text
DevRelay-Portable-Windows-x64.zip
DevRelay-SBOM.cdx.json          (next release)
devrelay-<version>-py3-none-any.whl
devrelay-<version>.tar.gz
SHA256SUMS
```

v0.4.0 shipped the wheel, sdist, portable zip and `SHA256SUMS`.  The next
release adds the CycloneDX SBOM and requires five assets before publication.
The portable build is unsigned; verify `SHA256SUMS`.  The `.exe` installer,
code signing and package-manager manifests remain future work.

v0.4.0 发布了 wheel、sdist、portable zip 与 `SHA256SUMS`。下一个版本增加
CycloneDX SBOM，并在发布前校验五个资产。portable 构建未签名，请校验
`SHA256SUMS`；`.exe` 安装包、代码签名与包管理器清单仍为后续工作。

## License / 许可证

See [LICENSE](LICENSE).
