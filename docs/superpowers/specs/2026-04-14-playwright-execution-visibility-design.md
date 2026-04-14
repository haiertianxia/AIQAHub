# Playwright Execution Visibility Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Playwright executions visible and debuggable from the execution detail page, report detail page, and governance center without adding a new page or a new persistence model.

**Architecture:** Playwright remains an execution adapter, not a separate product surface. The existing worker, tasks, artifacts, summaries, and audit logs are treated as read-only projections for this work. The UI reads those existing projections and renders a Playwright card inside the existing execution detail page, a compact Playwright summary inside the existing report detail page, and a Playwright-related projection inside the existing governance center.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, Celery, React, TypeScript, existing execution/report/governance views.

---

## Context

Playwright execution is already present as a connector and worker path. The missing piece is user-visible output that makes it easy to answer:
- what Playwright ran,
- how it was polled or completed,
- what artifacts were produced,
- whether it fell back, timed out, or failed validation,
- and how that outcome is reflected in governance.

We already have the right data surfaces:
- `Execution.summary.playwright`
- `ExecutionTask` rows for `trigger_playwright` and `wait_for_playwright`
- `ExecutionArtifact` rows for Playwright report artifacts
- `AuditLog` rows projected into governance events

This work only improves visibility and traceability. It does not change the connector contract, the worker lifecycle, or the persistence model.

## Non-Goals

- No new Playwright-specific page.
- No new database tables.
- No new API endpoints.
- No schema migrations.
- No new event types.
- No Playwright browser runner in the frontend.
- No change to Jenkins behavior.
- No change to existing governance storage beyond reading existing audit projections.
- No new Playwright-specific page, route, or navigation entry.

## Proposed Layout

### Execution Detail Page
Add a dedicated Playwright panel to `ExecutionDetailPage` that is shown when `summary.playwright` exists. The panel should render:
- `job_name`
- `job_id`
- `status`
- `completion_source`
- `poll_count`
- `browser`
- `headless`
- `base_url`
- links to Playwright artifacts
- a simple link to the existing `/governance` page when an audit record exists; no event-specific deep link is required

The panel should tolerate partial data. Missing fields must render as `-` rather than breaking the page.

### Report Detail Page
Add a compact Playwright summary section to `ReportDetailPage` that mirrors the execution summary:
- terminal status
- completion source
- poll count
- artifact summary
- optional fallback/validation notes when present

This section should stay compact and should not duplicate the full execution detail layout.

### Governance Center
Expose Playwright execution outcomes through the existing governance event stream by relying on the existing governance projection only. The governance center should show only fields that already exist in that projection:
- validation failures
- successful completions
- timeout completions
- related execution identifier only when it already exists in the current projection
- adapter context only when it already exists in the current audit payload

The governance view should not create a new Playwright-only data model or a new subsection/tab. These outcomes remain existing governance projection rows in the current governance stream, surfaced through the existing event list and detail drawer only. The governance view should simply surface Playwright-related governance rows alongside the existing governance stream, and omit missing context rather than inventing new fields.

## Data Flow

1. The existing worker and services already produce Playwright execution summaries, task rows, artifacts, and audit logs.
2. If validation fails, the execution is already marked failed and the audit log already records that outcome.
3. If the run is triggered, the existing summary namespace and task outputs are already updated by the worker.
4. Polling already updates the same summary namespace and task outputs until the execution reaches a terminal state.
5. Terminal success, timeout, and validation failure are already represented in the audit log and execution summary.
6. The UI reads only existing execution, artifact, task, report, and governance endpoints to display the result.

## Error Handling

- If Playwright summary data is incomplete, the execution detail page still renders the rest of the execution.
- If artifact links are missing, the Playwright card still shows status and completion source.
- If governance event lookup fails, the execution detail page must remain usable.
- Validation failure should be displayed as a terminal failed execution with an explicit validation completion source.
- Timeout should be displayed as `poller_exhausted` in the Playwright summary and `timeout` at the execution level.

## Testing

Add or extend tests to cover:
- execution detail rendering of Playwright summary fields,
- report detail rendering of Playwright summary and artifacts,
- governance projection of Playwright validation, completion, and timeout events,
- fallback/validation failure paths still producing readable execution summaries,
- and existing execution worker tests remain green after the visibility changes.

## Implementation Notes

- Keep the Playwright panel read-only.
- Prefer existing summary and audit projections over new endpoints.
- Keep the UI logic defensive: missing Playwright fields should not break the page.
- Use the existing governance event stream and audit log conversion for visibility.
- Do not add new endpoints, schema migrations, event kinds, or Playwright-specific persisted records for this work.
- Limit UI changes to additions inside `ExecutionDetailPage`, `ReportDetailPage`, and the existing governance center only.
- The UI must derive Playwright visibility from existing `ExecutionRead.summary`, `ExecutionArtifact`, `ExecutionTask`, `ReportSummary`, and `AuditLog` shapes only; do not add Playwright-specific response fields.
- Display only values already present in `ExecutionRead.summary.playwright` and the existing governance projection; do not introduce new enums, normalized values, or display-only string replacements.
