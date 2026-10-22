(() => {
  "use strict";

  const SESSION_HEADER = "X-DevRelay-Session";
  const STORAGE_KEY = "devrelay.session";
  const loginView = document.getElementById("login-view");
  const appView = document.getElementById("app-view");
  const loginForm = document.getElementById("login-form");
  const loginError = document.getElementById("login-error");
  const alertBox = document.getElementById("alert");
  const resultBox = document.getElementById("config-result");
  const form = document.getElementById("config-form");
  let sessionToken = readStoredSession();
  let memoryToken = null;
  const state = {
    status: null,
    projects: [],
    config: null,
    wiring: null,
    runs: null,
    runDetail: null,
    selectedRunId: "",
    autoTimer: null,
    runDetailRequest: 0,
    refreshInFlight: false,
  };

  class ApiError extends Error {
    constructor(message, status, code) {
      super(message);
      this.name = "ApiError";
      this.status = status;
      this.code = code || "";
    }
  }

  function $(id) {
    return document.getElementById(id);
  }

  function readStoredSession() {
    try {
      return sessionStorage.getItem(STORAGE_KEY) || "";
    } catch (_) {
      return "";
    }
  }

  function storeSession(token) {
    memoryToken = token;
    try {
      if (token) sessionStorage.setItem(STORAGE_KEY, token);
      else sessionStorage.removeItem(STORAGE_KEY);
    } catch (_) {
      /* sessionStorage can be unavailable; memory keeps this tab working. */
    }
  }

  function clearSession() {
    sessionToken = "";
    memoryToken = null;
    storeSession("");
    if (state.autoTimer) {
      clearInterval(state.autoTimer);
      state.autoTimer = null;
    }
    const autoRefresh = document.getElementById("auto-refresh");
    if (autoRefresh) autoRefresh.checked = false;
    state.selectedRunId = "";
    state.runDetail = null;
    state.runDetailRequest += 1;
    const detail = document.getElementById("run-detail");
    if (detail) detail.hidden = true;
    const tokenField = document.getElementById("token");
    if (tokenField) tokenField.value = "";
  }

  function activeToken() {
    return sessionToken || memoryToken || "";
  }

  async function api(path, options = {}) {
    const headers = new Headers(options.headers || {});
    const token = activeToken();
    if (token) headers.set(SESSION_HEADER, token);
    let body = options.body;
    if (body !== undefined && typeof body !== "string") {
      headers.set("Content-Type", "application/json");
      body = JSON.stringify(body);
    }
    const response = await fetch(path, {
      method: options.method || "GET",
      headers,
      body,
      credentials: "same-origin",
      cache: "no-store",
    });
    let payload = null;
    try {
      payload = await response.json();
    } catch (_) {
      payload = null;
    }
    if (!response.ok || !payload || payload.ok === false) {
      const error = payload && payload.error ? payload.error : {};
      throw new ApiError(
        error.message || `request failed (HTTP ${response.status})`,
        response.status,
        error.code,
      );
    }
    return payload.data;
  }

  function showLogin(message = "") {
    loginView.hidden = false;
    appView.hidden = true;
    $("logout").hidden = true;
    setConnection("offline", "status-muted");
    loginError.textContent = message;
    $("token").focus();
  }

  function showApp() {
    loginView.hidden = true;
    appView.hidden = false;
    $("logout").hidden = false;
    setConnection("authenticated", "status-good");
  }

  function setConnection(text, className) {
    const node = $("connection");
    node.textContent = text;
    node.className = `status ${className}`;
  }

  function showAlert(message) {
    alertBox.textContent = message;
    alertBox.hidden = !message;
  }

  function setResult(message) {
    resultBox.textContent = message;
  }

  function shortSha(value) {
    return value ? `${value.slice(0, 12)}...` : "unavailable";
  }

  function fillField(name, value) {
    const field = form.querySelector(`[name="${name}"]`);
    if (!field) return;
    if (field.type === "checkbox") field.checked = Boolean(value);
    else field.value = value === undefined || value === null ? "" : String(value);
  }

  function fieldValue(name, fallback = "") {
    const field = form.querySelector(`[name="${name}"]`);
    return field ? field.value : fallback;
  }

  function fieldNumber(name, fallback) {
    const raw = fieldValue(name).trim();
    if (!raw) return fallback;
    const value = Number(raw);
    return Number.isFinite(value) ? value : fallback;
  }

  function getPath(object, path, fallback) {
    let current = object;
    for (const part of path.split(".")) {
      if (current === null || current === undefined || typeof current !== "object") {
        return fallback;
      }
      current = current[part];
    }
    return current === undefined ? fallback : current;
  }

  function renderSummary() {
    const projectList = state.projects.projects || [];
    const active = projectList.find((project) => project.active) || projectList[0];
    const status = state.status || {};
    const config = state.config || {};
    $("project-name").textContent = active ? (active.label || active.root) : "no active project";
    $("project-id").textContent = active ? active.project_id : "unregistered";
    $("package-version").textContent = status.package_version || "unknown";
    $("config-digest").textContent = shortSha(config.config_sha256);
    $("restart-note").textContent = config.restart_required
      ? "restart required to load this file"
      : "matches the running process";
    const runData = state.runs || {};
    $("run-count").textContent = `${runData.total || 0} total`;
  }

  function renderWiring() {
    const config = state.config || {};
    const opencode = config.opencode || {};
    const codex = config.codex || {};
    const rows = [
      ["Review provider", config.review_provider || "manual"],
      ["OpenCode configured", opencode.configured ? "yes" : "no"],
      ["OpenCode endpoint", opencode.base_url || "(not set)"],
      ["OpenCode workspace", opencode.workspace_override ? "override configured (path hidden)" : "repository root"],
      ["Codex executable", codex.executable || "(not set)"],
      ["Config write scope", config.write_scope || "workspace configuration patch"],
      ["Profiles / argv / test commands", "not editable through this API"],
    ];
    const list = $("wiring-view");
    list.replaceChildren();
    for (const [label, value] of rows) {
      const dt = document.createElement("dt");
      dt.textContent = label;
      const dd = document.createElement("dd");
      dd.textContent = value;
      list.append(dt, dd);
    }
  }

  function renderConfig() {
    const editable = (state.config && state.config.editable_config) || {};
    fillField("pipeline.max_fix_iterations", getPath(editable, "pipeline.max_fix_iterations", 3));
    fillField("pipeline.auto_fix_tests", getPath(editable, "pipeline.auto_fix_tests", false));
    fillField("pipeline.max_same_finding_cycles", getPath(editable, "pipeline.max_same_finding_cycles", 0));
    fillField("budget.max_implementer_calls", getPath(editable, "budget.max_implementer_calls", 4));
    fillField("budget.max_reviewer_calls", getPath(editable, "budget.max_reviewer_calls", 4));
    fillField("budget.max_total_provider_calls", getPath(editable, "budget.max_total_provider_calls", 8));
    fillField("review.retries", getPath(editable, "review.retries", 1));
    fillField("review.transport_retries", getPath(editable, "review.transport_retries", 0));
    fillField("review.timeout_seconds", getPath(editable, "review.timeout_seconds", 120));
    fillField("review.max_response_chars", getPath(editable, "review.max_response_chars", 200000));
    fillField("review.max_diff_bytes", getPath(editable, "review.max_diff_bytes", 300000));
    fillField("roles.implementer.model", getPath(editable, "roles.implementer.model", ""));
    fillField("roles.implementer.agent", getPath(editable, "roles.implementer.agent", ""));
    fillField("roles.reviewer.model", getPath(editable, "roles.reviewer.model", ""));
    fillField("roles.reviewer.agent", getPath(editable, "roles.reviewer.agent", ""));
    fillField("tests.full_regression", getPath(editable, "tests.full_regression", "release_only"));
    fillField("tests.timeout_seconds", getPath(editable, "tests.timeout_seconds", 900));
    fillField("codex.timeout_seconds", getPath(editable, "codex.timeout_seconds", 1800));
    fillField("opencode.timeout_seconds", getPath(editable, "opencode.timeout_seconds", 30));
    fillField("opencode.idle_timeout_seconds", getPath(editable, "opencode.idle_timeout_seconds", 300));
    fillField("opencode.poll_interval_seconds", getPath(editable, "opencode.poll_interval_seconds", 1));
    fillField("opencode.max_messages", getPath(editable, "opencode.max_messages", 50));
    const severities = new Set(getPath(editable, "review.blocking_severities", ["P0", "P1", "P2"]));
    for (const checkbox of form.querySelectorAll('input[name="review.blocking_severities"]')) {
      checkbox.checked = severities.has(checkbox.value);
    }
    const writable = Boolean(state.config && state.config.write_supported);
    $("write-scope").textContent = writable ? "allowlisted patch" : "write unavailable";
    const submit = form.querySelector('button[type="submit"]');
    const validateButton = $("validate");
    submit.disabled = !writable;
    validateButton.disabled = !writable;
    state.configBaseline = readFormPatch(false);
    renderWiring();
    renderWiringPanel();
  }

  function renderWiringPanel() {
    const wiring = state.wiring || {};
    const opencode = wiring.opencode || {};
    const credentials = wiring.credentials || {};
    const token = credentials.opencode_token || {};
    const mcp = wiring.mcp || {};
    $("opencode-base-url").value = opencode.base_url || "";
    $("wiring-save").disabled = !wiring.write_supported;

    const rows = [
      ["Endpoint locality", opencode.base_url_is_loopback === false
        ? "remote (manual config only)"
        : "loopback / not set"],
      ["Allow unknown workspace", opencode.allow_unknown_workspace ? "true" : "false (fixed)"],
      ["Workspace override", opencode.workspace_override ? "configured (path hidden)" : "registered root"],
      ["OpenCode token", `${token.env || "DEVRELAY_OPENCODE_TOKEN"}: ${token.configured ? "set in environment" : "not set"}`],
      ["Write scope", wiring.write_scope || "OpenCode endpoint wiring only"],
      ["Config digest", shortSha(wiring.config_sha256)],
      ["Restart", wiring.restart_required ? "required" : "not required"],
    ];
    const list = $("wiring-details");
    list.replaceChildren();
    for (const [label, value] of rows) {
      const dt = document.createElement("dt");
      dt.textContent = label;
      const dd = document.createElement("dd");
      dd.textContent = value;
      list.append(dt, dd);
    }

    const mcpRows = [
      ["Transport", mcp.transport || "stdio"],
      ["Command", mcp.command || "devrelay mcp serve --workspace <registered workspace>"],
      ["Credentials", mcp.credentials || "client-side / environment only"],
    ];
    const mcpList = $("mcp-view");
    mcpList.replaceChildren();
    for (const [label, value] of mcpRows) {
      const dt = document.createElement("dt");
      dt.textContent = label;
      const dd = document.createElement("dd");
      dd.textContent = value;
      mcpList.append(dt, dd);
    }
  }

  function renderStatus() {
    const status = state.status || {};
    const rows = [
      ["Workspace", status.workspace || "-"],
      ["Package version", status.package_version || "-"],
      ["OpenCode", status.opencode && status.opencode.configured ? "configured" : "not configured"],
      ["Roles", status.roles && status.roles.configured ? "configured" : "unconfigured"],
      ["Orchestration", status.orchestration && status.orchestration.enabled ? "enabled" : "disabled"],
      ["Ledger", (status.ledger && status.ledger.directory) || "-"],
      ["Recovery adoption", status.orchestration && status.orchestration.recovery
        ? (status.orchestration.recovery.adoption_enabled ? "enabled" : "disabled")
        : "-"],
    ];
    const list = $("status-view");
    list.replaceChildren();
    for (const [label, value] of rows) {
      const dt = document.createElement("dt");
      dt.textContent = label;
      const dd = document.createElement("dd");
      dd.textContent = value;
      list.append(dt, dd);
    }

    const runList = $("runs-view");
    runList.replaceChildren();
    const runs = (state.runs && state.runs.runs) || [];
    if (!runs.length) {
      const empty = document.createElement("li");
      empty.textContent = "No runs yet.";
      runList.append(empty);
      return;
    }
    for (const run of runs) {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "run-row";
      const left = document.createElement("span");
      left.className = "mono";
      left.textContent = run.run_id || "run";
      const right = document.createElement("span");
      right.className = "muted";
      right.textContent = `${run.state || "unknown"} · cycle ${run.current_cycle ?? 0}`;
      button.append(left, right);
      button.addEventListener("click", () => loadRunDetail(run.run_id));
      item.append(button);
      runList.append(item);
    }
  }

  function appendDetailRow(list, label, value) {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value === undefined || value === null || value === "" ? "-" : String(value);
    list.append(dt, dd);
  }

  function renderTurns(target, turns) {
    target.replaceChildren();
    if (!turns || !turns.length) {
      const empty = document.createElement("li");
      empty.textContent = "No turns recorded.";
      target.append(empty);
      return;
    }
    for (const turn of turns) {
      const item = document.createElement("li");
      const left = document.createElement("span");
      left.className = "mono";
      left.textContent = `cycle ${turn.cycle ?? "?"} · ${turn.outcome || "unknown"}`;
      const right = document.createElement("span");
      right.className = "muted";
      const status = turn.submission_status ?? "-";
      const calls = Array.isArray(turn.call_ids) && turn.call_ids.length
        ? turn.call_ids.join(", ")
        : "no call ids";
      const flags = [];
      if (turn.submission_uncertain) flags.push("submission uncertain");
      if (turn.reply_pending) flags.push("reply pending");
      if (turn.retry_safe) flags.push("retry-safe");
      const suffix = flags.length ? ` · ${flags.join(", ")}` : "";
      right.textContent = `${turn.resolved_model || "-"} · HTTP ${status}${suffix} · ${calls}`;
      item.append(left, right);
      target.append(item);
    }
  }

  function renderRunDetail(detail) {
    $("run-detail").hidden = false;
    $("run-detail-title").textContent = detail.run_id || "Run";
    const metrics = $("run-detail-metrics");
    metrics.replaceChildren();
    appendDetailRow(metrics, "State", detail.state);
    appendDetailRow(metrics, "Cycle", `${detail.cycle ?? "?"} / ${detail.max_cycles ?? "?"}`);
    appendDetailRow(metrics, "Completed cycles", detail.completed_cycles);
    appendDetailRow(metrics, "Model turns", `${detail.model_turns_used ?? 0} / ${detail.model_turn_budget ?? 0}`);
    appendDetailRow(metrics, "Turn attempts", detail.turn_attempts);
    appendDetailRow(metrics, "In flight", detail.in_flight ? "yes" : "no");
    appendDetailRow(metrics, "Updated", detail.updated_at);
    const routes = detail.route_snapshot || {};
    appendDetailRow(
      metrics,
      "Implementer route",
      routes.implementer ? `${routes.implementer.model || "-"} / ${routes.implementer.agent || "-"}` : "-",
    );
    appendDetailRow(
      metrics,
      "Reviewer route",
      routes.reviewer ? `${routes.reviewer.model || "-"} / ${routes.reviewer.agent || "-"}` : "-",
    );
    renderTurns($("run-impl-turns"), detail.implementer_turns);
    renderTurns($("run-rev-turns"), detail.reviewer_turns);

    const decisions = $("run-decisions");
    decisions.replaceChildren();
    const history = detail.decision_history || [];
    if (!history.length) {
      const empty = document.createElement("li");
      empty.textContent = "No decisions recorded.";
      decisions.append(empty);
    } else {
      for (const decision of history) {
        const item = document.createElement("li");
        const left = document.createElement("span");
        left.textContent = decision.decision || "decision";
        const right = document.createElement("span");
        right.className = "muted";
        right.textContent = `${decision.previous_state || "-"} → ${decision.next_state || "-"}`;
        item.append(left, right);
        decisions.append(item);
      }
    }
    const reasons = [];
    if (detail.blocked_reason) reasons.push(`Blocked: ${detail.blocked_reason}`);
    if (detail.recovery_reason) reasons.push(`Recovery: ${detail.recovery_reason}`);
    $("run-reasons").textContent = reasons.join("\n");
  }

  async function loadRunDetail(runId) {
    if (!runId) return;
    const request = ++state.runDetailRequest;
    try {
      const detail = await api(`/api/runs/${encodeURIComponent(runId)}`);
      if (request !== state.runDetailRequest) return;
      state.selectedRunId = runId;
      state.runDetail = detail;
      showAlert("");
      renderRunDetail(detail);
    } catch (error) {
      if (request !== state.runDetailRequest) return;
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else {
        state.selectedRunId = "";
        state.runDetail = null;
        $("run-detail").hidden = true;
        showAlert(`${error.code ? `${error.code}: ` : ""}${error.message}`);
      }
    }
  }

  async function refreshRuns() {
    if (state.refreshInFlight) return;
    state.refreshInFlight = true;
    try {
      const runs = await api("/api/runs?limit=8");
      state.runs = runs;
      $("run-count").textContent = `${runs.total || 0} total`;
      showAlert("");
      renderStatus();
      if (state.selectedRunId) await loadRunDetail(state.selectedRunId);
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else {
        showAlert(`${error.code ? `${error.code}: ` : ""}${error.message}`);
      }
    } finally {
      state.refreshInFlight = false;
    }
  }

  function setAutoRefresh(enabled) {
    if (state.autoTimer) {
      clearInterval(state.autoTimer);
      state.autoTimer = null;
    }
    if (enabled) {
      state.autoTimer = setInterval(refreshRuns, 5000);
    }
  }

  function readFormPatch(requireSeverity = true) {
    const checked = [...form.querySelectorAll('input[name="review.blocking_severities"]:checked')]
      .map((input) => input.value);
    if (requireSeverity && !checked.length) {
      throw new Error("Select at least one blocking severity.");
    }
    return {
      pipeline: {
        max_fix_iterations: fieldNumber("pipeline.max_fix_iterations", 3),
        auto_fix_tests: form.querySelector('[name="pipeline.auto_fix_tests"]').checked,
        max_same_finding_cycles: fieldNumber("pipeline.max_same_finding_cycles", 0),
      },
      budget: {
        max_implementer_calls: fieldNumber("budget.max_implementer_calls", 4),
        max_reviewer_calls: fieldNumber("budget.max_reviewer_calls", 4),
        max_total_provider_calls: fieldNumber("budget.max_total_provider_calls", 8),
      },
      review: {
        blocking_severities: checked,
        retries: fieldNumber("review.retries", 1),
        transport_retries: fieldNumber("review.transport_retries", 0),
        timeout_seconds: fieldNumber("review.timeout_seconds", 120),
        max_response_chars: fieldNumber("review.max_response_chars", 200000),
        max_diff_bytes: fieldNumber("review.max_diff_bytes", 300000),
      },
      roles: {
        implementer: {
          model: fieldValue("roles.implementer.model").trim(),
          agent: fieldValue("roles.implementer.agent").trim(),
        },
        reviewer: {
          model: fieldValue("roles.reviewer.model").trim(),
          agent: fieldValue("roles.reviewer.agent").trim(),
        },
      },
      tests: {
        full_regression: fieldValue("tests.full_regression", "release_only"),
        timeout_seconds: fieldNumber("tests.timeout_seconds", 900),
      },
      codex: { timeout_seconds: fieldNumber("codex.timeout_seconds", 1800) },
      opencode: {
        timeout_seconds: fieldNumber("opencode.timeout_seconds", 30),
        idle_timeout_seconds: fieldNumber("opencode.idle_timeout_seconds", 300),
        poll_interval_seconds: fieldNumber("opencode.poll_interval_seconds", 1),
        max_messages: fieldNumber("opencode.max_messages", 50),
      },
    };
  }

  function pruneUnchanged(patch, baseline) {
    const out = {};
    for (const [key, value] of Object.entries(patch)) {
      const base = baseline ? baseline[key] : undefined;
      if (value && typeof value === "object" && !Array.isArray(value)) {
        const nested = pruneUnchanged(
          value,
          base && typeof base === "object" ? base : {},
        );
        if (Object.keys(nested).length) out[key] = nested;
      } else if (JSON.stringify(value) !== JSON.stringify(base)) {
        out[key] = value;
      }
    }
    return out;
  }

  function buildPatch() {
    const full = readFormPatch(true);
    if (!state.configBaseline) return full;
    return pruneUnchanged(full, state.configBaseline);
  }

  async function validatePatch(patch) {
    return api("/api/config/validate", { method: "POST", body: { config: patch } });
  }

  function formatValidation(data) {
    if (data.valid) return "Patch is valid.";
    const errors = data.errors || [];
    if (!errors.length) return "Patch is invalid.";
    return errors
      .slice(0, 8)
      .map((error) => {
        const where = (error.loc || []).join(".");
        return `${where ? `${where}: ` : ""}${error.msg || error.type || "invalid"}`;
      })
      .join("\n");
  }

  async function runValidation(patch) {
    setResult("");
    try {
      const data = await validatePatch(patch || buildPatch());
      setResult(formatValidation(data));
      return data.valid;
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
        return false;
      }
      setResult(error.message);
      return false;
    }
  }

  async function applyPatch(event) {
    event.preventDefault();
    setResult("");
    showAlert("");
    let patch;
    try {
      patch = buildPatch();
    } catch (error) {
      setResult(error.message);
      return;
    }
    if (!Object.keys(patch).length) {
      setResult("No changes to apply.");
      return;
    }
    const valid = await runValidation(patch);
    if (!valid) return;
    if (JSON.stringify(buildPatch()) !== JSON.stringify(patch)) {
      setResult("The form changed during validation; validate again.");
      return;
    }
    const digest = state.config && state.config.config_sha256;
    if (!digest) {
      setResult("The current config digest is unavailable; reload before applying.");
      return;
    }
    if (!window.confirm("Apply this workspace configuration patch now? A backup is created first.")) {
      return;
    }
    const submit = form.querySelector('button[type="submit"]');
    submit.disabled = true;
    try {
      const data = await api("/api/config", {
        method: "PUT",
        headers: { "X-DevRelay-Confirm": "apply" },
        body: {
          expected_sha256: digest,
          config: patch,
          confirm: "apply",
        },
      });
      let message;
      if (data.applied) {
        message = `Applied. New digest ${shortSha(data.new_sha256)}. ` +
          (data.restart_required ? "Restart `devrelay web serve` to load it." : "No restart needed.");
      } else {
        message = "No change; the submitted patch matches the current file.";
      }
      try {
        await loadAll();
        setResult(message);
      } catch (reloadError) {
        if (reloadError.status === 401) {
          clearSession();
          showLogin("Session expired. The change may have been applied.");
        } else {
          setResult(`${message}\nReload failed: ${reloadError.message}`);
        }
      }
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else if (error.code === "config_changed") {
        setResult("The config changed on disk. Reloading the latest view; try again.");
        try {
          await loadAll();
        } catch (reloadError) {
          setResult(`The config changed and reload failed: ${reloadError.message}`);
        }
      } else {
        setResult(`${error.code ? `${error.code}: ` : ""}${error.message}`);
      }
    } finally {
      submit.disabled = false;
    }
  }

  async function saveWiring(event) {
    event.preventDefault();
    const result = $("wiring-result");
    result.textContent = "";
    const baseUrl = $("opencode-base-url").value.trim();
    if (baseUrl) {
      let parsed;
      try {
        parsed = new URL(baseUrl);
      } catch (_) {
        result.textContent = "Base URL must be a valid http:// or https:// URL.";
        return;
      }
      if (!["http:", "https:"].includes(parsed.protocol)) {
        result.textContent = "Base URL must start with http:// or https://.";
        return;
      }
      const host = parsed.hostname.replace(/^\[|\]$/g, "");
      if (!["127.0.0.1", "localhost", "::1"].includes(host)) {
        result.textContent = "B2 accepts loopback OpenCode endpoints only; edit a remote endpoint manually.";
        return;
      }
    }
    const wiring = state.wiring || {};
    if (!wiring.config_sha256) {
      result.textContent = "The config digest is unavailable; reload before saving.";
      return;
    }
    const target = baseUrl || "(disabled)";
    if (!window.confirm(`Set the OpenCode endpoint to ${target}? A config backup is created first.`)) {
      return;
    }
    const button = $("wiring-save");
    button.disabled = true;
    try {
      const data = await api("/api/wiring", {
        method: "PUT",
        headers: { "X-DevRelay-Confirm": "apply" },
        body: {
          expected_sha256: wiring.config_sha256,
          wiring: { opencode: { base_url: baseUrl } },
          confirm: "apply",
        },
      });
      const message = data.applied
        ? `Endpoint saved. Restart required: ${data.restart_required ? "yes" : "no"}.`
        : "No change; the endpoint is already current.";
      try {
        await loadAll();
        result.textContent = message;
      } catch (reloadError) {
        if (reloadError.status === 401) {
          clearSession();
          showLogin("Session expired. The endpoint may have been saved.");
        } else {
          result.textContent = `${message}\nReload failed: ${reloadError.message}`;
        }
      }
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else if (error.code === "config_changed") {
        result.textContent = "The config changed on disk; reloading the latest view. Try again.";
        try {
          await loadAll();
        } catch (reloadError) {
          result.textContent = `The config changed and reload failed: ${reloadError.message}`;
        }
      } else {
        result.textContent = `${error.code ? `${error.code}: ` : ""}${error.message}`;
      }
    } finally {
      button.disabled = false;
    }
  }

  async function loadAll() {
    const [status, projects, config, wiring, runs] = await Promise.all([
      api("/api/status"),
      api("/api/projects"),
      api("/api/config"),
      api("/api/wiring"),
      api("/api/runs?limit=8"),
    ]);
    state.status = status;
    state.projects = projects;
    state.config = config;
    state.wiring = wiring;
    state.runs = runs;
    renderSummary();
    renderConfig();
    renderWiringPanel();
    renderStatus();
  }

  async function enterApp() {
    showApp();
    setConnection("loading", "status-muted");
    try {
      await loadAll();
      setConnection("authenticated", "status-good");
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else {
        setConnection("degraded", "status-warn");
        showAlert(error.message);
      }
    }
  }

  async function connect(token) {
    loginError.textContent = "";
    try {
      const data = await api("/api/session", { method: "POST", body: { token } });
      sessionToken = data.session_token;
      storeSession(sessionToken);
      $("token").value = "";
      await enterApp();
    } catch (error) {
      clearSession();
      showLogin(error.status === 401 ? "That token was not accepted." : error.message);
    }
  }

  async function logout() {
    try {
      await api("/api/session", { method: "DELETE" });
    } catch (_) {
      /* local logout must still clear the tab */
    }
    clearSession();
    showLogin("");
  }

  function switchTab(name) {
    for (const button of document.querySelectorAll(".tab")) {
      button.classList.toggle("is-active", button.dataset.tab === name);
    }
    for (const panel of document.querySelectorAll(".tab-panel")) {
      panel.hidden = panel.id !== `tab-${name}`;
    }
  }

  function consumeFragmentToken() {
    if (!location.hash.startsWith("#token=")) return "";
    let token = "";
    try {
      token = decodeURIComponent(location.hash.slice("#token=".length));
    } catch (_) {
      token = "";
    } finally {
      history.replaceState(null, "", location.pathname + location.search);
    }
    return token;
  }

  loginForm.addEventListener("submit", (event) => {
    event.preventDefault();
    const token = $("token").value.trim();
    if (token) connect(token);
  });

  $("logout").addEventListener("click", logout);
  $("validate").addEventListener("click", () => runValidation());
  form.addEventListener("submit", applyPatch);
  $("wiring-form").addEventListener("submit", saveWiring);
  $("refresh-runs").addEventListener("click", refreshRuns);
  $("auto-refresh").addEventListener("change", (event) => {
    setAutoRefresh(event.target.checked);
  });
  $("run-detail-close").addEventListener("click", () => {
    state.selectedRunId = "";
    state.runDetail = null;
    state.runDetailRequest += 1;
    $("run-detail").hidden = true;
  });
  for (const button of document.querySelectorAll(".tab")) {
    button.addEventListener("click", () => switchTab(button.dataset.tab));
  }

  async function boot() {
    const fragmentToken = consumeFragmentToken();
    if (fragmentToken) {
      await connect(fragmentToken);
      return;
    }
    if (!activeToken()) {
      showLogin("");
      return;
    }
    try {
      await api("/api/session");
      await enterApp();
    } catch (_) {
      clearSession();
      showLogin("Enter the token printed by `devrelay web serve`.");
    }
  }

  boot();
})();
