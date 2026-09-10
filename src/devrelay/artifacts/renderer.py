"""Markdown rendering and parsing for DevRelay artifacts.

All artifacts are designed to be read by humans *and* machines:

* ``task.md`` / ``task.json``   - the Task Packet
* ``reviews/review-NN-request.md`` - manual reviewer handoff
* ``final/report.md``           - the "why is this task DONE?" report
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Optional

from devrelay.models import (
    Finding,
    ReviewDecision,
    ReviewResult,
    RiskLevel,
    TaskPacket,
    TaskRun,
    WorkspaceSnapshot,
)
from devrelay.redact import redact_text

SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "title": ("title",),
    "objective": ("objective", "goal", "目的", "目标"),
    "scope": ("scope", "in scope", "范围"),
    "out_of_scope": (
        "out of scope",
        "out-of-scope",
        "not in scope",
        "禁止项",
        "非目标",
    ),
    "acceptance_criteria": (
        "acceptance criteria",
        "acceptance",
        "验收标准",
        "完成标准",
    ),
    "constraints": ("constraints", "限制", "约束"),
    "tests_required": ("tests required", "tests", "测试要求", "需要运行的测试"),
    "risk_level": ("risk level", "risk", "风险等级"),
    "notes": ("notes", "备注", "说明"),
}


@dataclass
class ReviewBundle:
    """Everything an independent reviewer is allowed to see for one task."""

    task_id: str
    packet: TaskPacket
    workspace_root: str
    initial_snapshot: WorkspaceSnapshot | None = None
    diff: str = ""
    changed_files: list[str] = field(default_factory=list)
    diff_truncated: bool = False
    implementation_summary: str = ""
    implementation_report_paths: list[str] = field(default_factory=list)
    test_evidence: list[str] = field(default_factory=list)
    previous_reviews: list[ReviewResult] = field(default_factory=list)
    current_findings: list[Finding] = field(default_factory=list)
    preexisting_dirty_files: list[str] = field(default_factory=list)
    attempt: int = 1
    is_fix: bool = False


# --------------------------------------------------------------------------
# Reviewer redaction boundary
# --------------------------------------------------------------------------

def _clean_finding(finding: Finding) -> Finding:
    return finding.model_copy(
        update={
            "title": redact_text(finding.title or ""),
            "description": redact_text(finding.description or ""),
            "evidence": redact_text(finding.evidence or ""),
            "recommendation": redact_text(finding.recommendation or ""),
            "files": [redact_text(name) for name in finding.files],
        }
    )


def sanitize_review_bundle(bundle: ReviewBundle) -> ReviewBundle:
    """The single redaction boundary for anything a reviewer may see.

    Applied once between the engine and BOTH reviewer paths (remote HTTP
    payload and manual review-request artifact), so every field that can carry
    workspace content is pattern-redacted consistently.  This is best-effort
    pattern matching, not a data-loss-prevention system.
    """
    packet = bundle.packet.model_copy(
        update={
            "title": redact_text(bundle.packet.title or ""),
            "objective": redact_text(bundle.packet.objective or ""),
            "notes": redact_text(bundle.packet.notes or ""),
            "scope": [redact_text(x) for x in bundle.packet.scope],
            "out_of_scope": [redact_text(x) for x in bundle.packet.out_of_scope],
            "acceptance_criteria": [
                redact_text(x) for x in bundle.packet.acceptance_criteria
            ],
            "constraints": [redact_text(x) for x in bundle.packet.constraints],
            "tests_required": [redact_text(x) for x in bundle.packet.tests_required],
        }
    )
    history = [
        review.model_copy(
            update={
                "summary": redact_text(review.summary or ""),
                "findings": [_clean_finding(f) for f in review.findings],
            }
        )
        for review in bundle.previous_reviews
    ]
    return replace(
        bundle,
        packet=packet,
        diff=redact_text(bundle.diff or ""),
        implementation_summary=redact_text(bundle.implementation_summary or ""),
        test_evidence=[redact_text(line) for line in bundle.test_evidence],
        previous_reviews=history,
        current_findings=[_clean_finding(f) for f in bundle.current_findings],
        changed_files=[redact_text(name) for name in bundle.changed_files],
        implementation_report_paths=[
            redact_text(p) for p in bundle.implementation_report_paths
        ],
        preexisting_dirty_files=[
            redact_text(name) for name in bundle.preexisting_dirty_files
        ],
    )


# --------------------------------------------------------------------------
# Task Packet rendering / parsing
# --------------------------------------------------------------------------

def _bullets(items: list[str], heading: str) -> str:
    if not items:
        return ""
    body = "\n".join(f"- {item}" for item in items)
    return f"## {heading}\n\n{body}\n\n"


def render_task_markdown(packet: TaskPacket) -> str:
    """Render a canonical task.md from a validated TaskPacket."""
    parts = [
        f"# Task {packet.task_id}",
        "",
        f"**Title:** {packet.title or '(untitled)'}",
        f"**Risk level:** {packet.risk_level.value}",
        "",
        "## Objective",
        "",
        packet.objective or "(no objective yet)",
        "",
    ]
    parts.append(_bullets(packet.scope, "Scope"))
    parts.append(_bullets(packet.out_of_scope, "Out of Scope"))
    parts.append(_bullets(packet.acceptance_criteria, "Acceptance Criteria"))
    parts.append(_bullets(packet.constraints, "Constraints"))
    parts.append(_bullets(packet.tests_required, "Tests Required"))
    if packet.notes:
        parts.append(f"## Notes\n\n{packet.notes}\n\n")
    return "".join(parts)


def starter_task_markdown(task_id: str, title: str) -> str:
    """Template written by ``devrelay start`` before the plan is imported."""
    return (
        f"# Task {task_id}\n\n"
        f"**Title:** {title or '(untitled)'}\n"
        "**Risk level:** NORMAL\n\n"
        "## Objective\n\n(write the objective, then `devrelay plan import task.md`)\n\n"
        "## Scope\n\n- (in scope)\n\n"
        "## Out of Scope\n\n- (explicitly out of scope)\n\n"
        "## Acceptance Criteria\n\n- (how will we know it is done?)\n\n"
        "## Constraints\n\n- (constraints / forbidden changes)\n\n"
        "## Tests Required\n\n- (targeted tests first; full regression only at release gates)\n\n"
        "## Notes\n\n"
    )


_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")


def _match_section(heading: str) -> str | None:
    key = heading.strip().lower()
    for canonical, aliases in SECTION_ALIASES.items():
        if key in aliases:
            return canonical
    return None


def parse_task_markdown(text: str, default_task_id: str) -> TaskPacket:
    """Parse a task.md into a validated TaskPacket.

    Raises ValueError with a clear message when required sections are missing
    or the risk level is unknown.
    """
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        stripped = raw.strip()
        match = _HEADING_RE.match(raw)
        if match:
            canonical = _match_section(match.group(1))
            current = canonical
            sections.setdefault(canonical or "", [])
            continue
        if current and stripped:
            sections.setdefault(current, []).append(stripped)

    def missing(name: str) -> bool:
        return name not in sections or not sections[name]

    if missing("title"):
        raise ValueError("task.md is missing a 'Title' section")
    if missing("objective"):
        raise ValueError("task.md is missing an 'Objective' section")

    title = sections["title"][0]
    objective = "\n".join(sections["objective"])

    def items(name: str) -> list[str]:
        out: list[str] = []
        for line in sections.get(name, []):
            out.append(re.sub(r"^[-*]\s+", "", line).strip())
        return [line for line in out if line]

    risk_text = " ".join(sections.get("risk_level", ["NORMAL"]))
    risk_text = re.sub(r"^[-*]\s*", "", risk_text).strip().upper()
    risk_values = {member.value for member in RiskLevel}
    if risk_text not in risk_values:
        raise ValueError(
            f"unknown risk level '{risk_text}' in task.md "
            f"(expected one of {sorted(risk_values)})"
        )
    risk = RiskLevel(risk_text)

    notes_lines = [re.sub(r"^[-*]\s+", "", ln).strip() for ln in sections.get("notes", [])]
    return TaskPacket(
        task_id=default_task_id,
        title=title,
        objective=objective,
        scope=items("scope"),
        out_of_scope=items("out_of_scope"),
        acceptance_criteria=items("acceptance_criteria"),
        constraints=items("constraints"),
        tests_required=items("tests_required"),
        risk_level=risk,
        notes="\n".join(notes_lines),
    )


# --------------------------------------------------------------------------
# Reviewer prompts / requests
# --------------------------------------------------------------------------

REVIEWER_SYSTEM_PROMPT = """\
You are a fully independent read-only code reviewer for the DevRelay pipeline.
You MUST NOT modify code, run commands, or produce anything other than the
review result. You review the task's current delta only.

Severity contract:
- P0: catastrophic / data loss / severe security problem
- P1: core functionality broken / obvious release blocker
- P2: real bug / important acceptance criterion missing / significant regression risk
- P3: non-blocking improvement

Do not manufacture blocking findings for style preferences. Focus on:
1. acceptance criteria satisfaction
2. scope creep or out-of-scope damage
3. logic bugs
4. missing tests
5. error handling
6. race / state / data consistency risks
7. security / privacy risks
8. backward compatibility

Respond with ONLY a single JSON object matching this schema:
{
  "decision": "PASS" | "REQUEST_CHANGES" | "BLOCKED",
  "summary": "short human summary",
  "findings": [
    {
      "severity": "P0" | "P1" | "P2" | "P3",
      "title": "short title",
      "description": "detail",
      "files": ["path/relative", ...],
      "evidence": "concrete evidence",
      "recommendation": "what to do"
    }
  ]
}
No markdown fences, no prose outside the JSON object.
"""


def render_review_user_prompt(bundle: ReviewBundle) -> str:
    head = bundle.initial_snapshot.head_sha if bundle.initial_snapshot else None
    branch = bundle.initial_snapshot.branch if bundle.initial_snapshot else None
    lines = [
        f"# Review request — task {bundle.task_id} (attempt {bundle.attempt})",
        "",
        f"## Task Packet ({bundle.packet.title})",
        "",
        f"- Task: {bundle.task_id}",
        f"- Title: {bundle.packet.title or '(untitled)'}",
        f"- Risk: {bundle.packet.risk_level.value}",
        "",
        "### Objective",
        "",
        bundle.packet.objective,
        "",
    ]
    if bundle.packet.scope:
        lines += ["### In scope", ""] + [f"- {s}" for s in bundle.packet.scope] + [""]
    if bundle.packet.out_of_scope:
        lines += ["### Out of scope", ""] + [f"- {s}" for s in bundle.packet.out_of_scope] + [""]
    if bundle.packet.acceptance_criteria:
        lines += ["### Acceptance criteria", ""] + [f"- {s}" for s in bundle.packet.acceptance_criteria] + [""]

    lines += [
        "## Workspace state",
        "",
        f"- Workspace: {bundle.workspace_root}",
        f"- Initial HEAD: {head or '(no commit yet)'}",
        f"- Initial branch: {branch or '-'}",
        "",
    ]
    if bundle.preexisting_dirty_files:
        lines += ["### PREEXISTING_DIRTY_FILES (present before the task started, not agent changes)", ""]
        lines += [f"- {f}" for f in bundle.preexisting_dirty_files] + [""]

    if bundle.changed_files:
        lines += ["## Changed files (git name-only vs initial HEAD)", ""]
        lines += [f"- {f}" for f in bundle.changed_files] + [""]

    lines += ["## Current diff", ""]
    if bundle.diff_truncated:
        lines += [
            "> WARNING: the diff exceeded the configured size limit and was truncated."
            " Review the listed changed files / implementation report and request"
            " the full diff from the human when needed.",
            "",
        ]
    lines.append(bundle.diff or "(no diff)")
    lines.append("")

    if bundle.test_evidence:
        lines += ["## Test evidence", ""] + [f"- {line}" for line in bundle.test_evidence] + [""]

    if bundle.implementation_summary:
        lines += ["## Implementation report (latest iteration)", "", bundle.implementation_summary, ""]

    if bundle.previous_reviews:
        lines += ["## Previous review history", ""]
        for i, review in enumerate(bundle.previous_reviews, start=1):
            lines.append(f"- review #{i}: decision={review.decision.value}, findings={len(review.findings)}")
            if review.summary:
                lines.append(f"  summary: {review.summary}")
        lines.append("")

    if bundle.current_findings:
        lines += ["## Findings the current fix iteration must address", ""]
        for finding in bundle.current_findings:
            lines.append(f"- [{finding.severity.value}] {finding.title} — {finding.description}")
        lines.append("")

    lines += [
        "## Your task",
        "",
        "Review the delta above against the acceptance criteria. Output ONLY the",
        "JSON object described by your instructions — never markdown fences.",
    ]
    return "\n".join(lines)


def render_review_request_md(bundle: ReviewBundle, review_number: int) -> str:
    """Human-readable manual reviewer handoff document."""
    body = render_review_user_prompt(bundle)
    return (
        f"# Manual review request #{review_number} — {bundle.task_id}\n\n"
        f"This review is **read-only**. Do not modify code.\n\n"
        "**Diff scope: task baseline -> current workspace.** The diff and "
        "changed-file list below are TASK-RELATIVE. Pre-existing user changes "
        "are excluded from the diff and only listed by name for context.\n\n"
        "Produce a review JSON file with this shape and import it with:\n"
        "    devrelay review import <file>.json\n\n"
        "```json\n"
        "{\n"
        '  "decision": "PASS",\n'
        '  "summary": "one paragraph",\n'
        '  "findings": [\n'
        "    {\n"
        '      "severity": "P2",\n'
        '      "title": "short title",\n'
        '      "description": "detail",\n'
        '      "files": ["src/x.py"],\n'
        '      "evidence": "concrete evidence",\n'
        '      "recommendation": "what to do"\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "```\n\n"
        "Severity contract: P0 catastrophic, P1 core breakage, P2 real bug / "
        "missing acceptance, P3 non-blocking improvement.\n"
        "Decisions: PASS (no P0/P1/P2), REQUEST_CHANGES (blocking findings "
        "exist), BLOCKED (review could not be completed safely).\n\n"
        "---\n\n" + body
    )


# --------------------------------------------------------------------------
# Final report
# --------------------------------------------------------------------------

def render_final_report(
    task: TaskRun,
    *,
    preexisting_changes: list[str],
    task_changed_files: list[str],
    task_diff_stat_text: str,
    head_now: str | None,
    note: str = "",
    policy_notes: list[str] | None = None,
) -> str:
    packet = task.packet
    baseline = task.baseline
    lines = [
        f"# Final report — {task.task_id}",
        "",
        f"**Task:** {task.title or '(untitled)'}",
        f"**Status:** {task.state.value}",
        "",
        "## Task",
        "",
    ]
    if packet:
        lines += [
            f"- Objective: {packet.objective or '(none)'}",
            f"- Risk level: {packet.risk_level.value}",
            "",
        ]
        if packet.acceptance_criteria:
            lines += ["- Acceptance criteria:"] + [
                f"    - {c}" for c in packet.acceptance_criteria
            ] + [""]
    lines += [
        f"- Initial HEAD: {baseline.head_sha if baseline else (task.initial_snapshot.head_sha if task.initial_snapshot else None)}",
        f"- Final HEAD: {head_now or '(working tree not committed by DevRelay)'}",
        f"- Initial branch: {baseline.branch if baseline else (task.initial_snapshot.branch if task.initial_snapshot else '-')}",
        f"- Baseline status: "
        + (
            f"COMPLETE (tree {baseline.baseline_worktree_tree_sha})"
            if baseline and baseline.baseline_complete
            else "NONE - legacy task (precise task delta unavailable)"
        ),
        f"- Implementation passes: {task.implementation_passes}",
        f"- Fix iterations used: {task.fix_iterations_used}",
        "",
        "## Pre-existing Workspace Changes (excluded from the task delta)",
        "",
    ]
    lines += [f"- {name}" for name in preexisting_changes] or ["- (none)"]
    lines.append("")
    lines.append("## Task Changed Files (task baseline -> current workspace)")
    lines.append("")
    lines += [f"- {name}" for name in task_changed_files] or ["- (none)"]
    lines.append("")
    lines.append("## Task-relative Diff Summary")
    lines.append("")
    lines.append(f"```\n{task_diff_stat_text or '(no changes)'}\n```")
    lines.append("")
    lines.append("## Implementation Summary")
    lines.append("")
    if task.implementation_report_paths:
        for rel in task.implementation_report_paths:
            lines.append(f"- {rel}")
    else:
        lines.append("- (no implementation reports)")
    lines.append("")
    lines.append("## Repository Policy Checks")
    lines.append("")
    if task.policy_violations:
        lines.append(f"- Violations: {len(task.policy_violations)}")
        for violation in task.policy_violations:
            lines.append(
                f"    - [{violation.id}] {violation.type.value}: "
                f"{violation.description}"
            )
    else:
        lines.append("- No policy violations recorded for any provider run.")
    lines.append("")
    lines.append("## Policy Violations History")
    lines.append("")
    if policy_notes:
        lines += [f"- {item}" for item in policy_notes]
    else:
        lines.append("- (none)")
    lines.append("")
    lines.append("## Test Evidence")
    lines.append("")
    lines += [f"- {line}" for line in task.test_evidence] or ["- (none)"]
    lines.append("")
    lines.append("## Reviewer Findings History")
    lines.append("")
    if task.review_history:
        for i, review in enumerate(task.review_history, start=1):
            lines.append(
                f"- review #{i}: decision={review.decision.value}, "
                f"findings={len(review.findings)}"
            )
            for finding in review.findings:
                lines.append(f"    - [{finding.severity.value}] {finding.title}")
    else:
        lines.append("- (no reviews recorded)")
    lines.append("")
    lines.append("## Open P3 (non-blocking)")
    lines.append("")
    lines += [f"- [{f.severity.value}] {f.title}" for f in task.open_p3] or ["- (none)"]
    lines.append("")
    lines.append("## Final Gate")
    lines.append("")
    if task.final_gate:
        lines += [
            f"- Approved by: {task.final_gate.approved_by}",
            f"- Approved at: {task.final_gate.approved_at}",
            f"- Note: {task.final_gate.note or '-'}",
        ]
    else:
        lines.append("- (manual final gate pending)")
    lines.append("")
    lines.append("## Why is this task considered complete?")
    lines.append("")
    if packet and packet.acceptance_criteria:
        for criterion in packet.acceptance_criteria:
            lines.append(f"- [x] {criterion}")
    else:
        lines.append("- (no acceptance criteria recorded in the Task Packet)")
    if note:
        lines += ["", f"Gate note: {note}"]
    lines.append("")
    lines.append("## Known Limitations")
    lines.append("")
    lines.append(
        "- Push prohibition is BEST-EFFORT / PROVIDER-LIMITED: a local "
        "postcondition check cannot mathematically prove that no `git push` "
        "occurred. Codex runs under the sandbox configured in `codex.args` "
        "when the provider supports it."
    )
    lines.append(
        "- Pre-existing user changes are excluded from the task delta, but "
        "files touched by both user and agent are listed under both sections."
    )
    return "\n".join(lines)
