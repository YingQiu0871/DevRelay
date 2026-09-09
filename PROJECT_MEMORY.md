# 项目持久记忆 Project Memory

> 本文件由 dsh-memoir 插件维护：记录本项目历次会话的工作归纳、经验教训与行动指南，
> 作为未来 AGENTS 接手本项目时的行动指南；它是人类可读的投影，不是 system prompt 的完整注入内容。
> 新会话只注入有界的 Hot Memory，完整历史通过 memoir_read 按需检索。

## 备注 Notes

- [2026-09-10 00:33] [备注] 用户咨询：多模型开发编排插件调研（Evolune 工作流） — 用户在做 Evolune（Android Phone/Wear）长期迭代开发，用 ChatGPT Plus 的 Sol/Luna/DeepSeek 分工，想省 Codex/Work 额度并自动化「规划→实现→独立审核→闸门」流程。已联网核实现成方案全部在 Claude Code/本地 CLI 生态，不在 ChatGPT 商店：GodModeSkill（/work 三模型家族每闸门投票）、magi-workflow（跨 CLI 加权投票）、claude-code-cross-review（Claude 写 Codex 只读复审循环）、claude-codex-bridge、millstone。关键提醒：Sol/Luna 是订阅档位名非 API model id；DeepSeek 当 reviewer 需自有 API key；真正省额度的核心是「仓库即权威状态」（state.json + agent-runs 落盘、已批准 scope 默认关闭、只审 delta、full regression 仅发布闸门）。已给用户 A 装现成插件 / B 先落地状态层 / C 帮他搭骨架 三个选项，等待其选择执行环境。工作目录 D:\DevRelay 为空，无 Evolune 仓库。
