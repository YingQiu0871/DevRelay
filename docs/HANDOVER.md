# DevRelay 交接文档

最后更新：2026-10-29（v0.5.0 发布 + G0.4 重跑）
仓库：`D:\DevRelay`
当前分支：`main`
当前公开版本：**v0.5.0**（2026-10-29；tag 剥离到 `36af6af`）
发布证据：`docs/RELEASE_CHECKLIST.md` § v0.5.0（test.yml 40798227385、release.yml 40799180664）
测试基线：**1,387 collected — 1,385 passed + 2 environment skips**（main，含 lease re-attach；v0.5.0 发布时为 1,381）
（实际当前 HEAD 以 `git log -1` 为准）

---

## 1. 一页结论

DevRelay 是本地、可审计的多模型编排层：CLI 任务状态机 + OpenCode-first 执行 +
ChatGPT/MCP 工具面 + v0.4 Web 控制面 + v0.5 hardening。

当前状态：

- **v0.5.0 已发布（2026-10-29）**：PyPI、GitHub Release 五资产（wheel、sdist、
  portable zip、CycloneDX SBOM、SHA256SUMS）。包含 SBOM/五资产 gate、持久 prompt
  marker、advisory hold、session lease、v3 session switch（API + WebUI + run 级 resolve）。
- **v0.3-E 平台 gate**：
  - G0.4/P4：**authoritative FAIL / P4 UNPROVEN**。2026-10-29 用独立评审过的
    revision 4 composite 重跑一次：目标绑定成功、1 次 `GET /doc`，结论
    `EVIDENCE_INSUFFICIENT`（v1 messageID + parentID 语义未定义）。见
    `docs/v0.3/V03E_G0_4_RERUN_PROOF_2026-10-29.md` 与 `..._REVIEW_2026-10-29.md`。
  - G0.5/P6、G1、G2：NOT RUN（G1/G2 尚无 oracle）。
  - `adopt_completed_turn` 保持 disabled。
- gate 证据原件在仓库外：`D:\DevRelay-gate\G0.4-2026-10-29\`。

---

## 2. 已发布内容（v0.5.0）

Release commit：`36af6afdb1fb48d1376873aa5605d2f925bb2384`
Tag：`v0.5.0`（annotated `c3c306d`；peeled `36af6af`）

| 资产 | 说明 |
| --- | --- |
| `devrelay-0.5.0-py3-none-any.whl` | PyPI / GitHub Release |
| `devrelay-0.5.0.tar.gz` | PyPI / GitHub Release |
| `DevRelay-Portable-Windows-x64.zip` | 未签名 portable，Windows x64 |
| `DevRelay-SBOM.cdx.json` | CycloneDX 1.5 runtime SBOM（23 components） |
| `SHA256SUMS` | 四个文件的 checksums |

v0.5.0 在 v0.4.0（A/B/C/D1/E1 Web 控制面）之上新增：

| 领域 | 关键文件 |
| --- | --- |
| Actions Node 24 + SHA pins；已发布版本 rerun 跳过重建 | `.github/workflows/*.yml` |
| CycloneDX SBOM + 五资产 release gate | `scripts/build_sbom.py`, `release.yml` |
| py3.13 release lock 双构建 proof | `requirements/portable-win-py313.lock`, `reproducibility.yml` |
| manual prompt marker 持久化 + recover | `web/prompt_markers.py` |
| advisory hold（Web + MCP） | `web/run_holds.py`, `mcp/tools.py` |
| session lease acquisition / explicit recovery | `web/session_leases.py`, `POST /api/sessions/{id}/lease/recover` |
| v3 run schema + switch evidence | `orchestration/models.py`, `invariants.py` |
| switch endpoint + WebUI 面板 | `POST /api/runs/{id}/session/switch`, `web/static/app.js` |
| switch run 级 resolve（API + UI） | `POST /api/runs/{id}/session/switch/recover` |

证据：`docs/RELEASE_CHECKLIST.md` § v0.5.0、`docs/v0.5/RELEASE_NOTES_v0.5.0.md`、
https://pypi.org/project/devrelay/0.5.0/ 、
https://github.com/YingQiu0871/DevRelay/releases/tag/v0.5.0 。

---

## 3. `main` 上 v0.5.0 之后的改动

- docs：G0.4 重跑的 provisioning addendum、harness、proof 与 review 记录，发布后状态更新。
- **未发布代码**：lease re-attach（`POST /api/runs/{id}/session/lease/reattach` + WebUI），
  见 CHANGELOG `Unreleased`。

| 领域 | 状态 |
| --- | --- |
| `.exe` installer / signing | **未实现** |
| v0.3-E platform gates | G0.4 = authoritative FAIL（已重跑确认）；G0.5/G1/G2 NOT RUN |

---

## 4. 架构与目录

### 核心层次

```text
CLI (devrelay)
  └── pipeline state machine / task store
  └── OpenCode bridge (single-writer, no retry)
  └── MCP stdio surface (19 tools)
  └── bounded orchestration (v0.3-D/E)
  └── Web control plane (v0.4)
        ├── Starlette/uvicorn, loopback only
        ├── header session auth, no cookies/CSRF
        ├── config/wiring guarded writes
        ├── run/task read dashboards
        ├── bounded run controls
        └── project/session/lease views
```

### 关键路径

```text
src/devrelay/                 核心 CLI/流水线/错误/配置
src/devrelay/opencode/        OpenCode bridge、ledger、normalization
src/devrelay/orchestration/   run model、state machine、store、invariants
src/devrelay/mcp/             MCP server/tools/envelopes
src/devrelay/web/             HTTP API、service、auth、static UI、lease/hold
scripts/                      portable/SBOM/reproducibility helpers
.github/workflows/            test/release/reproducibility
docs/                         specs、review、acceptance、status、runbook
tests/                        offline suite
```

### 安全边界

- Web 只绑定 loopback；Host/Origin 校验；body cap。
- 认证：bearer 或 `X-DevRelay-Session`；无 cookie/CSRF。
- 写操作需 `X-DevRelay-Confirm: apply`（适用端点另有 body confirm）。
- 不接受任意 workspace/path/session；session 来自 run 或经 bridge 验证。
- 不记录 prompt/reply/token；只保留 bounded/redacted evidence。
- 单 Web writer / 单 MCP surface 是当前支持边界；多进程 writer unsupported。

---

## 5. 本地开发与验证

建议 Python 3.11–3.14；当前本地验证为 Python 3.14.6。

```powershell
cd D:\DevRelay
python -m pip install -e ".[dev]"
python -m pytest -q
```

如果本机共享 `%TEMP%` 有残留，使用隔离 TEMP：

```powershell
$tempRoot = Join-Path $env:TEMP ('devrelay-temp-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
$env:TEMP = $tempRoot; $env:TMP = $tempRoot; $env:TMPDIR = $tempRoot
python -m pytest -q
```

期望：**1,387 collected — 1,385 passed + 2 environment skips**。

Web：

```powershell
devrelay web serve --workspace <initialized workspace>
```

详细发布流程：

- `docs/PYPI_PUBLISHING.md`
- `docs/RELEASE_CHECKLIST.md`

---

## 6. 当前未实现/风险清单

### P0/P1 级（不阻塞当前使用，但不要误报）

1. **v0.3-E gates 未关闭**：不得启用 `adopt_completed_turn`，不得声称 P4/P6/G1/G2
   已满足。需要真实 OpenCode endpoint、冻结 oracle、owner 一次性授权、独立
   reviewer、干净 workspace。
2. **Switch lease commit 不是跨存储事务**：
   - 顺序是 v3 run 写入 → lease commit。
   - lease commit 失败时返回 `503 switch_lease_uncertain`，target 变 uncertain，
     source 仍 active；prompt 被 `switch_pending` 阻止。
   - 进程在两步之间崩溃也会留下 pending/uncertain。
   - **恢复入口（v0.5.0）**：`POST /api/runs/{id}/session/switch/recover`
     以 run 文档为准：run 已记录该 switch → 补完 commit（target active、source
     released）；run 仍指向 source → 释放 target；不一致 → `409
     switch_state_inconsistent`，不写任何东西。WebUI 有 “Resolve pending switch”。
   - 残留已修（v0.5.0 之后，未发布）：通用 `/lease/recover` 释放过 target 的 run，
     用 `POST /api/runs/{id}/session/lease/reattach`（WebUI “Re-attach lease”）给当前
     session 重新挂 lease，同时释放孤儿 source lease，之后可以再 switch。
3. **Switch UI（v0.5.0）**：run detail 面板 + Resolve pending
   switch；Sessions 中仅对非 switch 的 `uncertain` lease 提供 Recover。`active`
   lease 恢复仍只走 API。

### 已知限制

- `.exe` installer、代码签名、winget/scoop、auto-update：未实现。
- Portable 未签名；release-lock 双构建已 PASS，但没有 hash-pinned wheelhouse/跨
  runner 通用保证。
- v1/v2 run 文档只读，不能携带 switch history；没有自动迁移。
- Active project 选择仅进程内，重启回 CLI workspace。
- Manual prompt marker 是 metadata-only；CLI 仍可启动 turn。
- Advisory hold 不是 provider pause；interrupt 仍是 abort。
- v0.4.0 资产不含 SBOM/lease/switch；这些从 v0.5.0 起才有。

---

## 7. 接手后优先动作

### A. 如果要继续产品能力

1. ~~给 switch endpoint 加 WebUI 确认面板。~~ 已完成（2026-10-29）。
2. ~~switch 的跨存储恢复（run+lease）~~ 已完成（run 级 resolve + lease re-attach）。
3. 视需要实现 installer/signing。

### B. 如果要发布下一版

按 `docs/RELEASE_CHECKLIST.md` § v0.5.0 的步骤：改版本号（`pyproject.toml`、
`__init__.py` fallback、`tests/test_version.py`、`release.yml` 默认 tag 与其测试）→
CHANGELOG/release notes → 全量测试 + 构建 + `twine check` → 合入 main 等 CI →
annotated tag → draft Release → dispatch `release.yml`（`confirm=PUBLISH`）→ 核验五资产、
PyPI、全新 venv → 记录证据并把 README/状态改为已发布。需要 owner 明确授权。

### C. 如果要继续 v0.3-E gates

- G0.4：已重跑，结论 `EVIDENCE_INSUFFICIENT`。若要再试，必须先有一份新的、经独立
  评审的定义来解决 v1 `messageID`/`parentID` 语义问题（或评估 v2 durable admission），
  不能复用已花掉的授权。
- G0.5/P6：先读 `V03E_G0_5_PRE_SESSION_INCARNATION_FINDING.md`；历史结论是可能
  `NO SOUND PROVENANCE ANCHOR`。
- G1/G2：目前没有 oracle，需先起草并独立评审。
- 流程模板：`V03E_G0_4_RERUN_PROVISIONING_ADDENDUM.md` + `V03E_G0_4_RERUN_HARNESS.ps1`
  （冻结定义 → owner 授权 → 执行一次 → 独立评审 proof）。不要用离线测试替代。

---

## 8. 重要文档索引

| 文档 | 用途 |
| --- | --- |
| `README.md` | 对外能力/安装 |
| `docs/PROJECT_STATUS.md` | 当前发布与能力矩阵 |
| `docs/ROADMAP.md` | 阶段状态 |
| `docs/HARDENING_v0.4.md` | hardening 记录 |
| `docs/HARDENING_BACKLOG_v0.4.md` | 残余风险/后续项 |
| `docs/PYPI_PUBLISHING.md` | 发布流程 |
| `docs/RELEASE_CHECKLIST.md` | 发布证据 |
| `docs/v0.4/` | A/B/C/D/E specs/reviews/acceptances |
| `docs/v0.5/PAUSE_DESIGN.md` | advisory hold / pause |
| `docs/v0.5/LEASE_ACQUISITION_DESIGN.md` | lease acquisition |
| `docs/v0.5/SWITCH_ENDPOINT_DESIGN.md` | switch endpoint |
| `docs/v0.5/SWITCH_SCHEMA_REVIEW.md` | v3 schema review |
| `docs/v0.3/V03E_GATE_RUNBOOK.md` | platform gate runbook |
| `docs/v0.3/V03E_G0_4_RERUN_*` | G0.4 重跑：addendum、harness、proof、review |
| `docs/v0.5/RELEASE_NOTES_v0.5.0.md` | v0.5.0 release notes |
| `docs/REPRODUCIBILITY_PROOF_2026-10-24.md` | py3.13 double-build evidence |

---

## 9. 操作约定（重要）

- 不要 `git add -A`；不要提交 `.audit-tmp/` 或 `PROJECT_REVIEW_2026-10-17.md`。
- 不要伪造 gate proof、release、switch 成功或 provider 状态。
- 不要在没有 owner 授权时 tag/release/PyPI。
- 不要自动重试 uncertain submission、interrupt 或 switch。
- 任何“已发布”表述必须能指向 PyPI/GitHub Release/evidence。
- 当前工作树唯一未跟踪项：`.audit-tmp/`、`PROJECT_REVIEW_2026-10-17.md`。

---

## 10. 当前验证快照

```text
Version:     0.5.0 (published 2026-10-29; tag v0.5.0 -> 36af6af)
Tests:       1,381 collected / 1,379 passed / 2 environment skips
CI:          40798227385 (8/8 success, release commit)
Release run: 40799180664 (portable + PyPI OIDC success)
Adoption:    disabled
G0.4/P4:     authoritative FAIL / P4 UNPROVEN (rerun 2026-10-29, EVIDENCE_INSUFFICIENT)
G0.5/G1/G2:  NOT RUN
```

更早的接手复核（2026-10-29，v0.4.0 时）：

```text
HEAD:        f69f33f6ce52dec0eac7a47b6244cbb4727242f2 (= main = origin/main; 自 afad11a 起仅 docs)
Tests:       1,371 passed / 2 skipped (fsync 目录、symlink 权限；Windows 本地)
CI:          40784486176 (8/8 success)
Release:     gh release v0.4.0 = 4 assets, non-draft, tag peeled c3a5416
MCP tools:   19 (src/devrelay/mcp/server.py)
```
