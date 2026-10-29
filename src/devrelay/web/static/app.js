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
    tasks: null,
    sessions: null,
    taskDetail: null,
    selectedTaskId: "",
    taskDetailRequest: 0,
    messages: [],
    messagesCursor: "",
    messagesRunId: "",
    messagesTimer: null,
    messagesInFlight: false,
    messagesQueued: false,
    messagesRequest: 0,
    workspaceEpoch: 0,
    switchingProject: false,
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
    if (state.messagesTimer) {
      clearInterval(state.messagesTimer);
      state.messagesTimer = null;
    }
    state.messages = [];
    state.messagesCursor = "";
    state.messagesRunId = "";
    state.messagesInFlight = false;
    state.messagesQueued = false;
    state.messagesRequest += 1;
    const messagesAuto = document.getElementById("messages-auto");
    if (messagesAuto) messagesAuto.checked = false;
    const autoRefresh = document.getElementById("auto-refresh");
    if (autoRefresh) autoRefresh.checked = false;
    state.selectedRunId = "";
    state.runDetail = null;
    state.runDetailRequest += 1;
    state.selectedTaskId = "";
    state.taskDetail = null;
    state.taskDetailRequest += 1;
    const detail = document.getElementById("run-detail");
    if (detail) detail.hidden = true;
    const taskDetail = document.getElementById("task-detail");
    if (taskDetail) taskDetail.hidden = true;
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
    const select = $("project-select");
    select.replaceChildren();
    for (const project of projectList) {
      const option = document.createElement("option");
      option.value = project.project_id;
      option.textContent = project.label || project.project_id;
      select.append(option);
    }
    if (active) select.value = active.project_id;
    $("project-activate").disabled = !active;
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

  function renderSessions() {
    const target = $("sessions-view");
    target.replaceChildren();
    const sessions = (state.sessions && state.sessions.sessions) || [];
    if (!sessions.length) {
      const empty = document.createElement("li");
      empty.textContent = "No run-recorded sessions.";
      target.append(empty);
      return;
    }
    for (const session of sessions) {
      const item = document.createElement("li");
      const left = document.createElement("span");
      left.className = "mono";
      left.textContent = session.session_id;
      const right = document.createElement("span");
      right.className = "muted";
      const lease = session.lease ? ` · lease:${session.lease.state}` : "";
      right.textContent = `${(session.roles || []).join("/")} · ${session.latest_state || "?"} · ${(session.run_ids || []).length} run(s)${lease}`;
      item.append(left, right);
      // Only an uncertain lease gets a UI recovery control; active leases stay
      // API-only, and a switch lease is resolved from its run (Resolve pending
      // switch) so the source lease is not orphaned.
      if (session.lease && session.lease.switch_id && ["pending_switch", "uncertain"].includes(session.lease.state)) {
        const hint = document.createElement("span");
        hint.className = "muted";
        hint.textContent = "resolve from run detail";
        item.append(hint);
      } else if (session.lease && session.lease.state === "uncertain") {
        const recover = document.createElement("button");
        recover.type = "button";
        recover.className = "button button-quiet lease-recover";
        recover.textContent = "Recover lease";
        recover.addEventListener("click", () => recoverSessionLease(session.session_id, recover));
        item.append(recover);
      }
      target.append(item);
    }
  }

  async function refreshSessions() {
    const epoch = state.workspaceEpoch;
    const sessions = await api("/api/sessions");
    if (epoch !== state.workspaceEpoch) return;
    state.sessions = sessions;
    renderSessions();
  }

  async function recoverSessionLease(sessionId, button) {
    if (!window.confirm(
      `Release the uncertain lease on ${sessionId}?\n\nVerify the session out of band first. This does not contact the provider, interrupt a turn or switch any run.`,
    )) {
      return;
    }
    button.disabled = true;
    try {
      await api(`/api/sessions/${encodeURIComponent(sessionId)}/lease/recover`, {
        method: "POST",
        headers: { "X-DevRelay-Confirm": "apply" },
        body: { confirm: "apply", expected_state: "uncertain" },
      });
      await refreshSessions();
      if (state.selectedRunId) await loadRunDetail(state.selectedRunId);
      showAlert(`Lease on ${sessionId} released by explicit recovery.`);
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else {
        button.disabled = false;
        showAlert(`${error.code ? `${error.code}: ` : ""}${error.message}`);
      }
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
    $("run-decide").disabled = detail.state !== "AWAITING_DECISION" || Boolean(detail.in_flight);
    $("run-interrupt").disabled = !detail.in_flight;
    $("run-prompt-send").disabled = Boolean(detail.terminal || detail.in_flight);
    const hold = detail.hold || null;
    $("run-hold").disabled = Boolean(detail.terminal || hold);
    $("run-hold-release").disabled = !hold;
    $("run-hold-status").textContent = hold
      ? `Held: ${hold.reason || "(no reason)"}`
      : detail.hold_error
        ? "Hold store unavailable."
        : "No advisory hold.";
    const schemaVersion = Number(detail.schema_version || 0);
    const pendingSwitch = detail.pending_switch || null;
    $("run-switch").disabled = schemaVersion < 3
      || Boolean(detail.terminal || detail.in_flight || pendingSwitch || detail.pending_switch_error);
    $("run-switch-resolve").hidden = !pendingSwitch;
    $("run-switch-resolve").disabled = !pendingSwitch;
    $("run-switch-status").textContent = pendingSwitch
      ? `Unresolved ${pendingSwitch.role} switch (${pendingSwitch.state}): ${pendingSwitch.source_session_id} → ${pendingSwitch.target_session_id}`
      : detail.pending_switch_error
        ? "Session lease store unavailable."
        : schemaVersion < 3
          ? "Switch requires a v3 run document."
          : detail.terminal
            ? "Run is terminal."
            : detail.in_flight
              ? "A turn is in flight."
              : "";
    const roleLeases = detail.role_leases || null;
    $("run-lease-status").textContent = roleLeases
      ? `Leases: implementer ${roleLeases.implementer} · reviewer ${roleLeases.reviewer}`
      : "Session lease store unavailable.";
    const leaseRole = $("run-lease-role").value;
    $("run-lease-reattach").disabled = !roleLeases || Boolean(detail.terminal || pendingSwitch)
      || ["active", "no_session"].includes(roleLeases[leaseRole]);
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
    appendDetailRow(metrics, "Implementer session", detail.implementer_session_id);
    appendDetailRow(metrics, "Reviewer session", detail.reviewer_session_id);
    appendDetailRow(metrics, "Run schema", detail.schema_version);
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
    const switches = $("run-switches");
    switches.replaceChildren();
    const switchHistory = detail.session_switch_history || [];
    if (!switchHistory.length) {
      const empty = document.createElement("li");
      empty.textContent = "No session switches recorded.";
      switches.append(empty);
    } else {
      for (const record of switchHistory) {
        const item = document.createElement("li");
        const left = document.createElement("span");
        left.className = "mono";
        left.textContent = `${record.role || "-"} · ${record.source_session_id || "-"} → ${record.target_session_id || "-"}`;
        const right = document.createElement("span");
        right.className = "muted";
        right.textContent = `${record.result || "-"} · ${record.switched_at || "-"}`;
        item.append(left, right);
        switches.append(item);
      }
    }
    const reasons = [];
    if (detail.blocked_reason) reasons.push(`Blocked: ${detail.blocked_reason}`);
    if (detail.recovery_reason) reasons.push(`Recovery: ${detail.recovery_reason}`);
    $("run-reasons").textContent = reasons.join("\n");
  }

  function renderTasks() {
    const target = $("tasks-view");
    target.replaceChildren();
    const tasks = (state.tasks && state.tasks.tasks) || [];
    if (!tasks.length) {
      const empty = document.createElement("li");
      empty.textContent = "No tasks yet.";
      target.append(empty);
      return;
    }
    for (const task of tasks) {
      const item = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "run-row";
      const left = document.createElement("span");
      left.className = "mono";
      left.textContent = task.task_id;
      const title = document.createElement("span");
      title.className = "muted";
      title.textContent = ` ${task.title || ""}`;
      left.append(title);
      const right = document.createElement("span");
      right.className = "muted";
      right.textContent = `${task.state || "unknown"}${task.current ? " · current" : ""}`;
      button.append(left, right);
      button.addEventListener("click", () => loadTaskDetail(task.task_id));
      item.append(button);
      target.append(item);
    }
  }

  function renderTaskDetail(detail) {
    $("task-detail").hidden = false;
    $("task-detail-title").textContent = `${detail.task_id} — ${detail.title || ""}`;
    const metrics = $("task-metrics");
    metrics.replaceChildren();
    appendDetailRow(metrics, "State", detail.state);
    appendDetailRow(metrics, "Current", detail.current ? "yes" : "no");
    appendDetailRow(metrics, "Plan ready", detail.plan_ready ? "yes" : "no");
    appendDetailRow(metrics, "Implementation passes", detail.implementation_passes);
    appendDetailRow(metrics, "Fix iterations", detail.fix_iterations_used);
    appendDetailRow(metrics, "Updated", detail.updated_at);
    appendDetailRow(metrics, "Baseline", detail.baseline_available ? "available" : "unavailable");
    const usage = detail.usage || {};
    appendDetailRow(
      metrics,
      "Provider calls",
      `${usage.total_calls ?? 0} total · ${usage.implementer_calls ?? 0} implementer · ${usage.reviewer_calls ?? 0} reviewer`,
    );
    appendDetailRow(metrics, "Token/cost", "not available in provider records");

    const tests = $("task-tests");
    tests.replaceChildren();
    const testItems = [];
    if (detail.tests && detail.tests.passed !== null && detail.tests.passed !== undefined) {
      testItems.push(`Last run: ${detail.tests.passed ? "PASS" : "FAIL"}`);
    } else {
      testItems.push("Last run: not recorded");
    }
    for (const line of (detail.tests && detail.tests.evidence) || []) {
      testItems.push(line);
    }
    for (const line of testItems) {
      const item = document.createElement("li");
      item.textContent = line;
      tests.append(item);
    }

    const findings = $("task-findings");
    findings.replaceChildren();
    const review = (detail.review && detail.review.last) || null;
    const findingItems = review ? (review.findings || []) : [];
    const currentFindings = (detail.review && detail.review.current_findings) || [];
    const openP3 = (detail.review && detail.review.open_p3) || [];
    const allFindings = findingItems.concat(currentFindings, openP3);
    if (!allFindings.length) {
      const empty = document.createElement("li");
      empty.textContent = "No review findings recorded.";
      findings.append(empty);
    } else {
      for (const finding of allFindings) {
        const item = document.createElement("li");
        const left = document.createElement("span");
        left.className = "mono";
        left.textContent = `${finding.severity || "?"} ${finding.title || ""}`;
        const right = document.createElement("span");
        right.className = "muted";
        right.textContent = finding.files && finding.files.length
          ? finding.files.join(", ")
          : "";
        item.append(left, right);
        findings.append(item);
      }
    }

    const diff = $("task-diff");
    const git = detail.git || {};
    diff.textContent = git.available
      ? (git.stat || "(no changes)")
      : `Unavailable: ${git.reason || "no baseline"}`;

    const calls = $("task-calls");
    calls.replaceChildren();
    const providerCalls = (detail.usage && detail.usage.provider_calls) || [];
    if (!providerCalls.length) {
      const empty = document.createElement("li");
      empty.textContent = "No provider calls recorded.";
      calls.append(empty);
    } else {
      for (const call of providerCalls) {
        const item = document.createElement("li");
        const left = document.createElement("span");
        left.className = "mono";
        left.textContent = `${call.call_id} · ${call.kind}`;
        const right = document.createElement("span");
        right.className = "muted";
        right.textContent = `${call.phase} · ${call.success ? "success" : "failed"} · ${call.external_calls} external · ${call.duration_seconds.toFixed(2)}s`;
        item.append(left, right);
        calls.append(item);
      }
    }

    const attempts = $("task-attempts");
    attempts.replaceChildren();
    const reviewAttempts = (detail.usage && detail.usage.review_attempts) || [];
    if (!reviewAttempts.length) {
      const empty = document.createElement("li");
      empty.textContent = "No review attempts recorded.";
      attempts.append(empty);
    } else {
      for (const attempt of reviewAttempts) {
        const item = document.createElement("li");
        const left = document.createElement("span");
        left.className = "mono";
        left.textContent = `#${attempt.review_number} · ${attempt.status}`;
        const right = document.createElement("span");
        right.className = "muted";
        right.textContent = `${attempt.provider} · ${attempt.external_calls} external · ${attempt.transport_attempts} transport / ${attempt.format_attempts} format`;
        item.append(left, right);
        attempts.append(item);
      }
    }

    const reviews = $("task-reviews");
    reviews.replaceChildren();
    const history = (detail.review && detail.review.history) || [];
    if (!history.length) {
      const empty = document.createElement("li");
      empty.textContent = "No reviews recorded.";
      reviews.append(empty);
    } else {
      for (const entry of history) {
        const item = document.createElement("li");
        const left = document.createElement("span");
        left.textContent = entry.decision || "review";
        const right = document.createElement("span");
        right.className = "muted";
        right.textContent = entry.summary || "";
        item.append(left, right);
        reviews.append(item);
      }
    }

    const notes = [];
    if (detail.blocked && (detail.blocked.code || detail.blocked.reason)) {
      notes.push(`Blocked: ${detail.blocked.code || ""} ${detail.blocked.reason || ""}`.trim());
    }
    if (detail.final_gate) {
      notes.push(`Final gate: ${detail.final_gate.approved_by || "approved"}`);
    }
    $("task-notes").textContent = notes.join("\n");
  }

  async function loadTaskDetail(taskId) {
    if (!taskId) return;
    const request = ++state.taskDetailRequest;
    try {
      const detail = await api(`/api/tasks/${encodeURIComponent(taskId)}`);
      if (request !== state.taskDetailRequest) return;
      state.selectedTaskId = taskId;
      state.taskDetail = detail;
      showAlert("");
      renderTaskDetail(detail);
    } catch (error) {
      if (request !== state.taskDetailRequest) return;
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else {
        state.selectedTaskId = "";
        state.taskDetail = null;
        $("task-detail").hidden = true;
        showAlert(`${error.code ? `${error.code}: ` : ""}${error.message}`);
      }
    }
  }

  async function loadRunDetail(runId) {
    if (!runId) return;
    if (state.messagesRunId !== runId) {
      state.messagesRunId = runId;
      state.messages = [];
      state.messagesCursor = "";
      state.messagesRequest += 1;
      renderMessages();
    }
    const request = ++state.runDetailRequest;
    $("run-action-result").textContent = "";
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

  async function decideRun() {
    const detail = state.runDetail;
    if (!detail) return;
    const decision = $("run-decision").value;
    if (!window.confirm(`Apply decision "${decision}" to ${detail.run_id}?`)) return;
    const button = $("run-decide");
    button.disabled = true;
    try {
      await api(`/api/runs/${encodeURIComponent(detail.run_id)}/decide`, {
        method: "POST",
        headers: { "X-DevRelay-Confirm": "apply" },
        body: {
          expected_updated_at: detail.updated_at,
          decision,
          confirm: "apply",
        },
      });
      await loadRunDetail(detail.run_id);
      $("run-action-result").textContent = `Decision "${decision}" recorded.`;
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else if (error.code === "run_changed") {
        await loadRunDetail(detail.run_id);
        $("run-action-result").textContent = "The run changed; reloaded. Retry the decision.";
      } else {
        $("run-action-result").textContent = `${error.code ? `${error.code}: ` : ""}${error.message}`;
      }
    } finally {
      button.disabled = false;
    }
  }

  async function interruptRun() {
    const detail = state.runDetail;
    if (!detail) return;
    const role = $("run-interrupt-role").value;
    if (!window.confirm(`Request an interrupt of the ${role} session for ${detail.run_id}?`)) return;
    const button = $("run-interrupt");
    button.disabled = true;
    try {
      const data = await api(`/api/runs/${encodeURIComponent(detail.run_id)}/interrupt`, {
        method: "POST",
        headers: { "X-DevRelay-Confirm": "apply" },
        body: { role, confirm: "apply" },
      });
      const message = data.interrupt_verified
        ? "Interrupt accepted and verified."
        : "Interrupt request accepted; terminal state is not verified.";
      await loadRunDetail(detail.run_id);
      $("run-action-result").textContent = message;
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else {
        $("run-action-result").textContent = `${error.code ? `${error.code}: ` : ""}${error.message}`;
      }
    } finally {
      button.disabled = false;
    }
  }

  function renderMessages() {
    const view = $("messages-view");
    view.replaceChildren();
    if (!state.messages.length) {
      const empty = document.createElement("li");
      empty.textContent = "No messages loaded.";
      view.append(empty);
    } else {
      for (const message of state.messages) {
        const item = document.createElement("li");
        const left = document.createElement("span");
        left.className = "mono";
        left.textContent = `${message.role || "unknown"} ${message.message_id || ""}`.trim();
        const right = document.createElement("span");
        right.className = "muted";
        right.textContent = message.text || "(no text)";
        item.append(left, right);
        view.append(item);
      }
    }
    $("messages-status").textContent = state.messages.length
      ? `${state.messages.length} message(s) · cursor ${state.messagesCursor || "(start)"}`
      : "No messages loaded.";
  }

  async function loadMessages(reset = false) {
    if (!state.selectedRunId) return;
    if (reset) {
      state.messages = [];
      state.messagesCursor = "";
      state.messagesRequest += 1;
      renderMessages();
    }
    if (state.messagesInFlight) {
      state.messagesQueued = true;
      return;
    }
    const request = ++state.messagesRequest;
    const role = $("messages-role").value;
    const runId = state.selectedRunId;
    const params = new URLSearchParams({ role });
    if (state.messagesCursor) params.set("cursor", state.messagesCursor);
    state.messagesInFlight = true;
    try {
      const data = await api(
        `/api/runs/${encodeURIComponent(runId)}/messages?${params.toString()}`,
      );
      if (
        request !== state.messagesRequest
        || runId !== state.selectedRunId
        || role !== $("messages-role").value
      ) {
        return;
      }
      state.messages = state.messages.concat(data.messages || []).slice(-200);
      state.messagesCursor = data.next_cursor || "";
      renderMessages();
      if (data.cursor_unknown) {
        $("messages-status").textContent += " · cursor expired; new window";
      }
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else {
        $("messages-status").textContent = `${error.code ? `${error.code}: ` : ""}${error.message}`;
      }
    } finally {
      state.messagesInFlight = false;
      if (state.messagesQueued) {
        state.messagesQueued = false;
        loadMessages(false);
      }
    }
  }

  function setMessagesAuto(enabled) {
    if (state.messagesTimer) {
      clearInterval(state.messagesTimer);
      state.messagesTimer = null;
    }
    if (enabled) state.messagesTimer = setInterval(() => loadMessages(false), 5000);
  }

  async function sendManualPrompt() {
    const detail = state.runDetail;
    if (!detail) return;
    const role = $("run-prompt-role").value;
    const prompt = $("run-prompt-text").value.trim();
    if (!prompt) {
      $("run-action-result").textContent = "Enter a prompt first.";
      return;
    }
    if (!window.confirm(`Send this manual prompt to the ${role} session of ${detail.run_id}?`)) {
      return;
    }
    const button = $("run-prompt-send");
    button.disabled = true;
    try {
      const data = await api(`/api/runs/${encodeURIComponent(detail.run_id)}/prompt`, {
        method: "POST",
        headers: { "X-DevRelay-Confirm": "apply" },
        body: { role, prompt, confirm: "apply" },
      });
      $("run-prompt-text").value = "";
      const callCount = Array.isArray(data.call_ids) ? data.call_ids.length : 0;
      $("run-action-result").textContent = data.completed
        ? `Prompt completed (${callCount} call id(s)).`
        : `Prompt not confirmed: ${data.code || "submission_not_confirmed"}`;
      await loadMessages(false);
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else {
        $("run-action-result").textContent = `${error.code ? `${error.code}: ` : ""}${error.message}`;
      }
    } finally {
      button.disabled = false;
    }
  }

  async function recoverPromptMarker() {
    const detail = state.runDetail;
    if (!detail) return;
    if (!window.confirm(
      "Clear the durable pending manual-prompt marker? Verify the session has no unresolved reply first; this does not interrupt or resend anything.",
    )) {
      return;
    }
    const button = $("run-prompt-recover");
    button.disabled = true;
    try {
      const data = await api(
        `/api/runs/${encodeURIComponent(detail.run_id)}/prompt/recover`,
        {
          method: "POST",
          headers: { "X-DevRelay-Confirm": "apply" },
          body: { confirm: "apply" },
        },
      );
      $("run-action-result").textContent = data.cleared
        ? "Pending manual-prompt marker cleared."
        : "No pending manual-prompt marker was recorded.";
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else {
        $("run-action-result").textContent = `${error.code ? `${error.code}: ` : ""}${error.message}`;
      }
    } finally {
      button.disabled = false;
    }
  }

  async function holdRun() {
    const detail = state.runDetail;
    if (!detail) return;
    const reason = window.prompt("Reason for the advisory hold (does not pause a provider turn):");
    if (!reason || !reason.trim()) return;
    if (!window.confirm(`Place an advisory hold on ${detail.run_id}? This blocks new web prompts, not an in-flight turn.`)) {
      return;
    }
    try {
      const data = await api(`/api/runs/${encodeURIComponent(detail.run_id)}/hold`, {
        method: "POST",
        headers: { "X-DevRelay-Confirm": "apply" },
        body: {
          expected_updated_at: detail.updated_at,
          reason: reason.trim(),
          confirm: "apply",
        },
      });
      await loadRunDetail(detail.run_id);
      $("run-action-result").textContent = data.held
        ? "Advisory hold recorded."
        : "Advisory hold was not recorded.";
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else {
        $("run-action-result").textContent = `${error.code ? `${error.code}: ` : ""}${error.message}`;
      }
    }
  }

  async function releaseHold() {
    const detail = state.runDetail;
    if (!detail) return;
    if (!window.confirm(`Release the advisory hold on ${detail.run_id}?`)) return;
    try {
      const data = await api(
        `/api/runs/${encodeURIComponent(detail.run_id)}/hold/release`,
        {
          method: "POST",
          headers: { "X-DevRelay-Confirm": "apply" },
          body: { confirm: "apply" },
        },
      );
      await loadRunDetail(detail.run_id);
      $("run-action-result").textContent = data.cleared
        ? "Advisory hold released."
        : "No advisory hold was active.";
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else {
        $("run-action-result").textContent = `${error.code ? `${error.code}: ` : ""}${error.message}`;
      }
    }
  }

  async function switchSession() {
    const detail = state.runDetail;
    if (!detail) return;
    const role = $("run-switch-role").value;
    const target = $("run-switch-target").value.trim();
    const source = detail[`${role}_session_id`] || "";
    if (!target) {
      $("run-action-result").textContent = "Enter a target session id first.";
      return;
    }
    if (target === source) {
      $("run-action-result").textContent = `${target} is already the ${role} session.`;
      return;
    }
    if (!window.confirm(
      `Switch the ${role} session of ${detail.run_id}?\n\nFrom: ${source || "-"}\nTo: ${target}\n\n`
      + "The bridge must verify the target belongs to this workspace. The switch is recorded as run evidence and is never retried automatically.",
    )) {
      return;
    }
    const button = $("run-switch");
    button.disabled = true;
    try {
      await api(`/api/runs/${encodeURIComponent(detail.run_id)}/session/switch`, {
        method: "POST",
        headers: { "X-DevRelay-Confirm": "apply" },
        body: {
          role,
          target_session_id: target,
          expected_updated_at: detail.updated_at,
          expected_source_session_id: source,
          confirm: "apply",
        },
      });
      $("run-switch-target").value = "";
      await loadRunDetail(detail.run_id);
      await refreshSessions().catch(() => {});
      $("run-action-result").textContent = `The ${role} session is now ${target}.`;
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
        return;
      }
      if (error.code === "run_changed") {
        await loadRunDetail(detail.run_id);
        $("run-action-result").textContent = "The run changed; reloaded. Review the current session and retry.";
      } else if (error.code === "switch_lease_uncertain") {
        // The run already records the target; only the lease commit failed.
        $("run-switch-target").value = "";
        await loadRunDetail(detail.run_id);
        await refreshSessions().catch(() => {});
        $("run-action-result").textContent = "The run now records the target session, but the lease commit failed. "
          + "Prompts stay blocked until you use Resolve pending switch. Do not retry the switch.";
      } else {
        $("run-action-result").textContent = `${error.code ? `${error.code}: ` : ""}${error.message}`;
      }
    } finally {
      if (state.runDetail && state.selectedRunId === detail.run_id) renderRunDetail(state.runDetail);
    }
  }

  async function reattachLease() {
    const detail = state.runDetail;
    if (!detail) return;
    const role = $("run-lease-role").value;
    const sessionId = detail[`${role}_session_id`] || "";
    if (!window.confirm(
      `Re-attach the ${role} lease of ${detail.run_id} to ${sessionId}?\n\n`
      + "The run document decides which session gets the lease. Any other active lease left for this run/role "
      + "is released in the same write. No provider I/O and no run write.",
    )) {
      return;
    }
    const button = $("run-lease-reattach");
    button.disabled = true;
    try {
      const data = await api(
        `/api/runs/${encodeURIComponent(detail.run_id)}/session/lease/reattach`,
        {
          method: "POST",
          headers: { "X-DevRelay-Confirm": "apply" },
          body: { role, expected_updated_at: detail.updated_at, confirm: "apply" },
        },
      );
      await loadRunDetail(detail.run_id);
      await refreshSessions().catch(() => {});
      const orphans = (data.released_orphans || []).length;
      $("run-action-result").textContent = `Lease re-attached to ${data.session_id}`
        + (orphans ? `; released ${orphans} orphaned lease(s).` : ".");
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
        return;
      }
      if (error.code === "run_changed") await loadRunDetail(detail.run_id);
      $("run-action-result").textContent = `${error.code ? `${error.code}: ` : ""}${error.message}`;
    } finally {
      if (state.runDetail && state.selectedRunId === detail.run_id) renderRunDetail(state.runDetail);
    }
  }

  async function resolveSwitch() {
    const detail = state.runDetail;
    const pending = detail && detail.pending_switch;
    if (!pending) return;
    if (!window.confirm(
      `Resolve the unresolved ${pending.role} switch on ${detail.run_id}?\n\n`
      + `${pending.source_session_id} → ${pending.target_session_id} (${pending.state})\n\n`
      + "The run document decides: if it records the switch, the target lease becomes active and the source is released; "
      + "otherwise the target lease is released. No provider I/O and no run write.",
    )) {
      return;
    }
    const button = $("run-switch-resolve");
    button.disabled = true;
    try {
      const data = await api(
        `/api/runs/${encodeURIComponent(detail.run_id)}/session/switch/recover`,
        {
          method: "POST",
          headers: { "X-DevRelay-Confirm": "apply" },
          body: { switch_id: pending.switch_id, confirm: "apply" },
        },
      );
      await loadRunDetail(detail.run_id);
      await refreshSessions().catch(() => {});
      $("run-action-result").textContent = data.result === "committed"
        ? `Switch completed: the ${data.role} session ${data.session_id} now holds the lease.`
        : `Switch aborted: the ${data.role} session stays ${data.session_id}.`;
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
        return;
      }
      await loadRunDetail(detail.run_id);
      $("run-action-result").textContent = `${error.code ? `${error.code}: ` : ""}${error.message}`;
    } finally {
      if (state.runDetail && state.selectedRunId === detail.run_id) renderRunDetail(state.runDetail);
    }
  }

  async function activateProject() {
    const select = $("project-select");
    const projectId = select.value;
    if (!projectId) return;
    const active = ((state.projects || {}).projects || []).find((item) => item.active);
    if (active && active.project_id === projectId) {
      showAlert("That project is already active.");
      return;
    }
    if (!window.confirm("Switch the active workspace? In-memory run and task detail will reset.")) {
      return;
    }
    const button = $("project-activate");
    button.disabled = true;
    state.workspaceEpoch += 1;
    state.switchingProject = true;
    if (state.autoTimer) {
      clearInterval(state.autoTimer);
      state.autoTimer = null;
    }
    $("auto-refresh").checked = false;
    try {
      await api(`/api/projects/${encodeURIComponent(projectId)}/activate`, {
        method: "POST",
        headers: { "X-DevRelay-Confirm": "apply" },
        body: { confirm: "apply" },
      });
      state.selectedRunId = "";
      state.runDetail = null;
      state.runDetailRequest += 1;
      state.selectedTaskId = "";
      state.taskDetail = null;
      state.taskDetailRequest += 1;
      state.messages = [];
      state.messagesCursor = "";
      state.messagesRunId = "";
      $("run-detail").hidden = true;
      $("task-detail").hidden = true;
      if (state.messagesTimer) {
        clearInterval(state.messagesTimer);
        state.messagesTimer = null;
      }
      $("messages-auto").checked = false;
      state.switchingProject = false;
      try {
        await loadAll();
        showAlert("Active project switched.");
      } catch (reloadError) {
        showAlert(`Project switched, but reload failed: ${reloadError.message}`);
      }
    } catch (error) {
      if (error.status === 401) {
        clearSession();
        showLogin("Session expired. Enter the token again.");
      } else {
        showAlert(`${error.code ? `${error.code}: ` : ""}${error.message}`);
      }
    } finally {
      state.switchingProject = false;
      button.disabled = false;
    }
  }

  async function refreshRuns() {
    if (state.refreshInFlight || state.switchingProject) return;
    const epoch = state.workspaceEpoch;
    state.refreshInFlight = true;
    try {
      const runs = await api("/api/runs?limit=8");
      if (epoch !== state.workspaceEpoch) return;
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
    const epoch = state.workspaceEpoch;
    const [status, projects, config, wiring, runs, tasks, sessions] = await Promise.all([
      api("/api/status"),
      api("/api/projects"),
      api("/api/config"),
      api("/api/wiring"),
      api("/api/runs?limit=8"),
      api("/api/tasks?limit=20"),
      api("/api/sessions"),
    ]);
    if (epoch !== state.workspaceEpoch) return false;
    state.status = status;
    state.projects = projects;
    state.config = config;
    state.wiring = wiring;
    state.runs = runs;
    state.tasks = tasks;
    state.sessions = sessions;
    renderSummary();
    renderConfig();
    renderWiringPanel();
    renderStatus();
    renderSessions();
    renderTasks();
    return true;
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
  $("project-activate").addEventListener("click", activateProject);
  $("run-decide").addEventListener("click", decideRun);
  $("run-interrupt").addEventListener("click", interruptRun);
  $("run-hold").addEventListener("click", holdRun);
  $("run-hold-release").addEventListener("click", releaseHold);
  $("run-switch").addEventListener("click", switchSession);
  $("run-switch-resolve").addEventListener("click", resolveSwitch);
  $("run-lease-reattach").addEventListener("click", reattachLease);
  $("run-lease-role").addEventListener("change", () => {
    if (state.runDetail) renderRunDetail(state.runDetail);
  });
  $("run-prompt-send").addEventListener("click", sendManualPrompt);
  $("run-prompt-recover").addEventListener("click", recoverPromptMarker);
  $("messages-refresh").addEventListener("click", () => loadMessages(true));
  $("messages-auto").addEventListener("change", (event) => {
    setMessagesAuto(event.target.checked);
  });
  $("messages-role").addEventListener("change", () => loadMessages(true));
  $("run-detail-close").addEventListener("click", () => {
    state.selectedRunId = "";
    state.runDetail = null;
    state.runDetailRequest += 1;
    if (state.messagesTimer) {
      clearInterval(state.messagesTimer);
      state.messagesTimer = null;
    }
    $("messages-auto").checked = false;
    state.messages = [];
    state.messagesCursor = "";
    renderMessages();
    $("run-detail").hidden = true;
  });
  $("task-detail-close").addEventListener("click", () => {
    state.selectedTaskId = "";
    state.taskDetail = null;
    state.taskDetailRequest += 1;
    $("task-detail").hidden = true;
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
