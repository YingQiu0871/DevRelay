# DevRelay 交接文档

最后更新：2026-10-28
仓库：`D:\DevRelay`
当前分支：`main`
审计快照 HEAD：`afad11a36d2fed5985ac44d3f6528346d2a74282`
（实际当前 HEAD 以 `git log -1` 为准；本文件提交后可能前进）
当前公开版本：**v0.4.0**（2026-10-22）
文档提交时 CI：https://github.com/YingQiu0871/DevRelay/actions/runs/40783416572 （8/8 success）
测试基线：**1,373 collected — 1,371 passed + 2 environment skips**

---

## 1. 一页结论

DevRelay 是本地、可审计的多模型编排层：CLI 任务状态机 + OpenCode-first 执行 +
ChatGPT/MCP 工具面 + v0.4 Web 控制面。

当前状态：

- **v0.4.0 已发布**：PyPI、GitHub Release、wheel/sdist、portable Windows zip。
- `main` 上有**未发布**的 post-v0.4 hardening：
  - Node.js 24 action pins
  - 已发布版本 rerun 跳过 Windows 重建
  - CycloneDX SBOM + 五资产 release gate
  - Windows/Python 3.13 release-lock 双构建 PASS
  - manual prompt marker 持久化
  - advisory hold（Web + MCP）
  - session lease acquisition / pending-switch / explicit recovery
  - v3 run schema + switch evidence
  - `POST /api/runs/{run_id}/session/switch` endpoint
- **v0.3-E 平台 gate 仍 blocked**：
  - G0.4/P4：authoritative FAIL / UNPROVEN
  - G0.5/P6、G1、G2：NOT RUN
  - `adopt_completed_turn` 保持 disabled
- 未发布改动**不要**描述成 v0.4.0 已发布能力；没有新 tag。

---

## 2. 已发布内容（v0.4.0）

Release commit：`c3a54162547cb810e454c498ee05f8eac33c99ae`
Tag：`v0.4.0`（annotated；peeled `c3a5416`）

| 资产 | 说明 |
| --- | --- |
| `devrelay-0.4.0-py3-none-any.whl` | PyPI / GitHub Release |
| `devrelay-0.4.0.tar.gz` | PyPI / GitHub Release |
| `DevRelay-Portable-Windows-x64.zip` | 未签名 portable，Windows x64 |
| `SHA256SUMS` | 四资产 checksums；v0.4.0 当时尚无 SBOM |

关键能力：

- v0.3 编排核心、OpenCode bridge、MCP 工具面、角色路由、有界编排、
  fail-closed recovery core（adoption disabled）。
- v0.4-A：loopback HTTP API、header session、Host/Origin、配置写保护。
- v0.4-B：静态 WebUI、配置/wiring 视图。
- v0.4-C1/C2a：run/task 只读 dashboard。
- v0.4-C2b：decision + role-scoped interrupt。
- v0.4-C2c：bounded manual prompt + normalized message polling。
- v0.4-D1：注册项目切换（进程内）+ run-recorded session inventory。
- v0.4-E1：portable Windows 构建 + release workflow。

证据：

- `docs/RELEASE_CHECKLIST.md` § v0.4.0
- `docs/v0.4/RELEASE_NOTES_v0.4.0.md`
- `docs/v0.4/V04E_ACCEPTANCE.md`
- https://pypi.org/project/devrelay/0.4.0/
- https://github.com/YingQiu0871/DevRelay/releases/tag/v0.4.0

---

## 3. `main` 上未发布改动（post-v0.4）

这些改动已合并/测试，但**不在 v0.4.0 资产中**：

| 领域 | 状态 | 关键文件 |
| --- | --- | --- |
| Actions Node 24 + SHA pins | 完成 | `.github/workflows/test.yml`, `release.yml` |
| published-version rerun 跳过重建 | 完成 | `.github/workflows/release.yml` |
| CycloneDX SBOM | 完成 | `scripts/build_sbom.py`, portable zip |
| py3.13 release lock 双构建 proof | 完成 | `requirements/portable-win-py313.lock`, `reproducibility.yml` |
| manual prompt marker 持久化 | 完成 | `src/devrelay/web/prompt_markers.py` |
| advisory hold | 完成（Web+MCP） | `run_holds.py`, `mcp/tools.py` |
| session lease acquisition | 完成 | `session_leases.py`, `mcp/tools.py` |
| pending-switch lease primitive | 完成 | `session_leases.py` |
| explicit lease recovery | 完成 | `POST /api/sessions/{id}/lease/recover` |
| v3 run schema + switch evidence | 完成 | `orchestration/models.py`, `invariants.py` |
| switch endpoint | 完成（API only） | `POST /api/runs/{id}/session/switch` |
| switch UI | **未实现** | — |
| `.exe` installer / signing | **未实现** | — |
| v0.3-E platform gates | **blocked** | `docs/v0.3/V03E_GATE_READINESS_2026-10-27.md` |

### 最近提交

```text
afad11a docs: record v03e gate readiness as blocked
2602f14 feat(web): add session switch endpoint with v3 evidence
d8f7d7f feat(orchestration): add v3 run schema and switch evidence
0da624c feat(leases): add pending switch lease primitive
3e74091 docs: approve switch schema conditions and add gate runbook
0e35327 feat(web): add explicit session lease recovery
fb505eb feat(orchestration): acquire session leases on start
45b15a4 docs: record py313 release-lock double-build proof
```

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

期望：**1,373 collected — 1,371 passed + 2 environment skips**。

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
     source 仍 active；prompt 被 `switch_pending` 阻止，需要显式 lease recovery。
   - 进程在两步之间崩溃也会留下 pending/uncertain。
3. **没有 switch UI**：只有 API；不要声称 WebUI 已有 switch。

### 已知限制

- `.exe` installer、代码签名、winget/scoop、auto-update：未实现。
- Portable 未签名；release-lock 双构建已 PASS，但没有 hash-pinned wheelhouse/跨
  runner 通用保证。
- v1/v2 run 文档只读，不能携带 switch history；没有自动迁移。
- Active project 选择仅进程内，重启回 CLI workspace。
- Manual prompt marker 是 metadata-only；CLI 仍可启动 turn。
- Advisory hold 不是 provider pause；interrupt 仍是 abort。
- v0.4.0 已发布资产**不包含** post-v0.4 的 SBOM/lease/switch 改动。

---

## 7. 接手后优先动作

### A. 如果要继续产品能力

1. 给 switch endpoint 加 WebUI 确认面板。
2. 设计/实现 switch 的跨存储恢复（run+lease）或明确 manual runbook。
3. 视需要实现 installer/signing。

### B. 如果要发布下一版

1. 决定版本号（如 0.4.1/0.5.0）并更新 `pyproject.toml`、fallback、测试。
2. 更新 CHANGELOG/release notes/README。
3. 全量测试 + release workflow 静态检查。
4. 构建、双构建 proof、tag、draft、dispatch。
5. 检查五资产 gate（wheel/sdist/SHA256SUMS/portable/SBOM）。

### C. 如果要关闭 v0.3-E gates

先读：

- `docs/v0.3/V03E_GATE_PREP.md`
- `docs/v0.3/V03E_GATE_RUNBOOK.md`
- `docs/v0.3/V03E_GATE_READINESS_2026-10-27.md`

需要 owner 提供真实 endpoint/authorization/reviewer；不要用离线测试替代。

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
HEAD:        afad11a36d2fed5985ac44d3f6528346d2a74282
Version:     0.4.0
Release:     v0.4.0 (published 2026-10-22)
Tests:       1,373 collected / 1,371 passed / 2 environment skips
CI:          40596216885 (8/8 success)
Adoption:    disabled
Gate:        blocked
```
