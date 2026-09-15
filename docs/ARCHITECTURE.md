# DevRelay Architecture / DevRelay 架构设计

## 1. Product boundary / 产品边界

DevRelay is an orchestration and control layer for multi-model software development. It is not intended to replace a coding-agent execution environment.

DevRelay 是多模型软件开发的编排与控制层，不以替代 coding agent 执行环境为目标。

The target architecture is:

```text
Human / 用户
   │
   ▼
ChatGPT
Planner / Arbiter
规划 / 裁决
   │
   ▼
DevRelay
Orchestration / Policy / State / Audit
编排 / 策略 / 状态 / 审计
   │
   ▼
OpenCode
Execution Environment
执行环境
   ├── Implementer: DeepSeek
   ├── Reviewer: GLM
   ├── tools
   ├── shell/files
   ├── MCP
   └── workspace/session context
```

## 2. Responsibility split / 职责划分

### ChatGPT — Planner / Arbiter

Responsibilities / 职责：

- define task goals and scope
- convert user intent into bounded implementation instructions
- interpret implementation and review evidence
- decide whether another fix cycle is justified
- surface unresolved product decisions to the user
- determine acceptance only when the configured policy allows it

Not responsible for / 不负责：

- directly editing files inside OpenCode's workspace
- silently approving implementer output without evidence
- unlimited autonomous retries

### DevRelay — Orchestrator / Control Plane

Responsibilities / 职责：

- connect planner, implementer, and reviewer
- own durable workflow state
- route one bounded action at a time
- enforce workspace/session identity
- enforce maximum loop/call limits
- normalize provider/session output
- persist audit evidence
- surface test/diff/review results
- stop on uncertainty, drift, or configured policy violation

DevRelay should make control decisions from explicit policy and structured state, not from loose natural-language optimism.

DevRelay 的控制决定应来自明确策略与结构化状态，而不是来自自然语言中的“看起来应该没问题”。

### OpenCode — Execution Engine

Responsibilities / 职责：

- coding-agent sessions
- model/provider access
- workspace context
- tool execution
- shell and file operations
- MCP integration
- per-agent runtime behavior

DevRelay should integrate with these capabilities instead of reimplementing them.

### Implementer — e.g. DeepSeek

Responsibilities / 职责：

- modify code within the assigned scope
- run or request relevant tests
- report changed files, tests, unresolved items, and risks
- fix reviewer findings when instructed

The implementer must not decide that its own result is accepted.

实现者不能自行决定其结果已经验收通过。

### Reviewer — e.g. GLM

Responsibilities / 职责：

- independently inspect the implementation delta and evidence
- report findings using agreed severity/category semantics
- distinguish blocking findings from non-blocking observations
- avoid modifying production code during read-only review unless explicitly configured otherwise

## 3. OpenCode-first execution / OpenCode-first 执行模式

OpenCode is intended to be the primary execution environment because it already owns the low-level coding-agent runtime.

OpenCode 被定位为主要执行环境，因为它已经提供低层 coding-agent runtime。

DevRelay v0.3-A introduces a narrow bridge with capabilities conceptually equivalent to:

```text
health()
list_sessions()
get_session(session_id)
read_messages(session_id, cursor)
send_prompt(session_id, prompt, role/model selection)
wait_idle(session_id, timeout)
interrupt(session_id)
```

Exact implementation details may differ, but the rest of DevRelay should consume normalized DevRelay-owned models rather than unstable OpenCode wire objects.

具体函数命名可以变化，但 DevRelay 其他模块应消费 DevRelay 自己定义的标准化模型，而不是直接依赖不稳定的 OpenCode wire object。

## 4. Session and workspace ownership / Session 与工作区归属

Every orchestration action must be scoped to:

- one registered project/workspace;
- one explicitly configured OpenCode endpoint;
- one selected OpenCode session;
- one intended role/action.

每次编排操作都必须明确绑定：

- 一个已注册项目/工作区；
- 一个明确配置的 OpenCode endpoint；
- 一个选定的 OpenCode session；
- 一个预期角色/动作。

Cross-workspace session reuse should fail closed unless explicitly and safely re-registered.

跨工作区复用 session 默认应 fail closed，除非经过显式且安全的重新注册。

## 5. Target orchestration lifecycle / 目标编排生命周期

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

The loop must be bounded by policy, for example:

- maximum repair rounds
- maximum external calls
- maximum wall-clock time where appropriate
- blocking severity threshold
- explicit stop on workspace/control-plane drift

循环必须由策略限制，例如最大修复轮数、最大外部调用数、必要时的最长运行时间、阻塞严重度阈值，以及工作区/控制面漂移时强制停止。

## 6. ChatGPT/MCP boundary / ChatGPT/MCP 边界

The planned ChatGPT/MCP interface should be intentionally narrow. It should expose bounded orchestration actions rather than arbitrary local execution.

计划中的 ChatGPT/MCP 接口应保持狭窄，提供有界编排动作，而不是任意本地执行能力。

Example future surface / 未来接口示例：

```text
project_status()
current_run()
read_latest_output()
read_review()
read_test_status()
read_diff_summary()
send_bounded_instruction()
start_review()
interrupt()
```

The interface should not silently permit arbitrary filesystem reads, arbitrary shell execution, or unconstrained provider switching.

接口不应静默允许任意文件系统读取、任意 shell 执行或无限制切换 provider。

## 7. Local Web Control Plane / 本地 Web 控制面

The planned GUI is a localhost WebUI backed by a DevRelay-owned local HTTP API.

计划中的 GUI 为 localhost WebUI，由 DevRelay 自己的本地 HTTP API 提供后端。

```text
Browser
  │
  ▼
127.0.0.1:<port>
DevRelay WebUI
  │
  ▼
Validated local API
  │
  ▼
DevRelay Core
```

The WebUI is primarily for:

- initial setup
- OpenCode connectivity
- project/workspace registration
- role/model assignment
- workflow limits
- usage/accounting
- logs and evidence
- pause/interruption/manual intervention

It is not intended to replace ChatGPT as the main high-level planning interface.

WebUI 主要用于配置、连接、监控与人工干预，不用于取代 ChatGPT 作为高层规划入口。

## 8. Security model for localhost UI / localhost UI 安全模型

Even a localhost application can hold powerful local privileges. Therefore planned safeguards include:

即使只监听 localhost，该服务仍可能拥有较高本地权限，因此计划中的保护包括：

- bind to loopback by default, never `0.0.0.0` by default
- authenticated local session/token
- origin and CSRF validation
- explicit registered-workspace list
- no arbitrary filesystem browsing from the browser
- backend-owned configuration validation and writes
- secrets never returned to the frontend after storage
- dangerous actions require explicit confirmation or policy gate

## 9. Secrets and credentials / 凭据与密钥

API keys and provider secrets should not be stored as ordinary plaintext project configuration.

API Key 与 provider 凭据不应以普通明文项目配置保存。

Target approach / 目标方案：

```text
WebUI input
   ↓
DevRelay backend
   ↓
OS credential storage
   ↓
config stores only credential reference
```

Possible platform backends:

- Windows Credential Manager
- macOS Keychain
- Linux Secret Service

Configuration may contain references such as:

```yaml
deepseek:
  credential: devrelay/deepseek/default
```

but not the plaintext secret.

## 10. Direct API mode / Direct API 模式

A future Direct API execution provider may exist as an optional alternative for lightweight or specialized tasks.

未来可增加 Direct API 执行 provider，作为轻量或特殊任务的可选方案。

However, Direct API mode should not force DevRelay to reinvent all of OpenCode's agent runtime responsibilities.

但是 Direct API 模式不应迫使 DevRelay 重新实现 OpenCode 已经提供的完整 agent runtime。

## 11. Distribution architecture / 分发架构

Long-term packaging target:

```text
GitHub Release
├── DevRelay-Setup-Windows-x64.exe
├── DevRelay-Portable-Windows-x64.zip
├── devrelay-<version>-py3-none-any.whl
└── SHA256SUMS.txt
```

The preferred user path is installation + browser-based setup. Developer/source installations remain supported but should not be mandatory for ordinary users.

首选普通用户路径应为安装后通过浏览器完成配置，而不是要求用户 clone 源码并手工编辑 YAML。

## 12. Architectural invariants / 架构不变量

These principles should remain true as DevRelay evolves:

1. **Human agency remains explicit. / 人的最终控制权始终明确。**
2. **Implementer and reviewer remain logically separate. / 实现与审阅保持逻辑隔离。**
3. **The implementer cannot self-approve. / 实现者不能自我批准。**
4. **Automation is bounded. / 自动化必须有界。**
5. **No hidden retries or hidden provider calls. / 不进行隐藏重试或隐藏调用。**
6. **Workspace/session ownership is explicit. / 工作区与 session 归属明确。**
7. **Uncertainty fails closed. / 不确定性默认 fail closed。**
8. **DevRelay orchestrates execution engines rather than needlessly rebuilding them. / DevRelay 负责编排执行引擎，而不是无必要地重造执行引擎。**
9. **Released capability is distinguished from unreleased development evidence. / 已发布能力必须与未发布开发证据清晰区分。**
