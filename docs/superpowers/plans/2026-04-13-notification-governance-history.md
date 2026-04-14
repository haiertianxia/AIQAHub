# Notification Governance History Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface notification delivery history, routing decisions, fallbacks, and skips in the existing governance center without adding a new persistence table or standalone page.

**Architecture:** Keep notification delivery non-blocking and reuse the existing audit log and governance projection pipeline as the source of truth. Record notification attempts as structured audit entries, derive governance events from those audit rows, and render the results inside the existing `/governance` page alongside asset, gate, settings, connector, and audit signals.

**Tech Stack:** Python, FastAPI, SQLAlchemy, Pydantic, React, TypeScript, Vite, pytest.

---

### Task 1: Notification Governance Test Coverage

**Files:**
- Create: `tests/api/test_notification_governance.py`
- Modify: `tests/api/test_governance.py` if shared helpers need to move
- Modify: `tests/api/test_notifications.py` if notification send assertions need to be tightened

- [x] **Step 1: Write the failing tests**

```python
def test_notification_sends_appear_in_governance_overview(client):
    ...

def test_notification_events_are_filterable_by_kind_and_channel(client):
    ...

def test_notification_event_detail_includes_policy_and_fallback_metadata(client):
    ...
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest tests/api/test_notification_governance.py -v`
Expected: FAIL because notification governance projection does not exist yet.

- [x] **Step 3: Add the minimal test scaffolding**

Create helpers that seed notification sends through the existing notification service and expose stable assertions for governance projections.

- [x] **Step 4: Run the tests to verify they still fail for the missing implementation**

Run: `python3 -m pytest tests/api/test_notification_governance.py -v`
Expected: FAIL until the governance projection and routing metadata are implemented.

- [x] **Step 5: Commit**

```bash
git add tests/api/test_notification_governance.py tests/api/test_notifications.py tests/api/test_governance.py
git commit -m "test: cover notification governance history"
```

### Task 2: Notification Audit Projection and Governance API

**Files:**
- Modify: `app/schemas/governance.py`
- Modify: `app/services/notification_service.py`
- Modify: `app/services/notification_policy_service.py`
- Modify: `app/services/audit_service.py`
- Modify: `app/api/v1/routes/governance.py`
- Modify: `app/api/v1/routes/notifications.py`
- Modify: `app/schemas/notification.py`
- Modify: `app/schemas/audit.py` if audit response shape needs notification fields
- Modify: `app/workers/notification_tasks.py` if notification dispatch is still queued in a worker path

- [x] **Step 1: Write the failing tests**

Use the new notification governance tests to drive:

- `notification_send`
- `notification_test`
- `notification_skip`
- `notification_fallback`
- overview counters for notification outcomes

- [x] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest tests/api/test_notification_governance.py -v`
Expected: FAIL because notification audit projection and governance filtering are not implemented yet.

- [x] **Step 3: Implement the notification audit projection**

Add structured audit recording for notification sends, including:

- `target_type = "notification"`
- `action = "notification_send" | "notification_test" | "notification_skip" | "notification_fallback"`
- `target_id` derived from execution, gate, settings, or synthetic test context
- `request_json` / `response_json` fields carrying:
  - `event_type`
  - `project_id`
  - `channel`
  - `provider`
  - `status`
  - `target`
  - `policy_scope_type`
  - `policy_scope_id`
  - `fallback_from`
  - `fallback_reason`

Project those audit records into governance events and expose them through:

- `GET /api/v1/governance/overview`
- `GET /api/v1/governance/events`
- `GET /api/v1/governance/events/{id}`

Make notification-derived events filterable by:

- kind
- project
- environment
- status
- channel
- provider
- search

- [x] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest tests/api/test_notification_governance.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add app/schemas/governance.py app/services/notification_service.py app/services/notification_policy_service.py app/services/audit_service.py app/api/v1/routes/governance.py app/api/v1/routes/notifications.py app/schemas/notification.py app/schemas/audit.py app/workers/notification_tasks.py
git commit -m "feat: project notification history into governance"
```

### Task 3: Governance Dashboard Notification Section

**Files:**
- Modify: `frontend/src/pages/GovernancePage.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/App.tsx` if route labels or navigation need refinement
- Modify: `frontend/src/components/Section.tsx` if needed
- Modify: `frontend/src/components/QueryToolbar.tsx` if needed
- Modify: `frontend/src/components/PaginationControls.tsx` if needed
- Modify: `frontend/src/components/PageState.tsx` if needed

- [x] **Step 1: Write the failing build expectation**

Use the front-end build as the contract:

```bash
npm --prefix frontend run build
```

Expected: FAIL before the governance page understands notification-specific event fields.

- [x] **Step 2: Implement the notification section**

Add a `Notification Events` section to `/governance` that shows:

- notification send/fail/fallback/skip counts
- a filterable notification event stream
- a detail drawer with raw payload and routing metadata
- jump links back to the triggering execution, gate, or settings page when possible

Reuse the existing shared UI primitives and the current governance page layout rather than introducing a new page.

- [x] **Step 3: Run the build to verify it passes**

Run: `npm --prefix frontend run build`
Expected: PASS.

- [x] **Step 4: Commit**

```bash
git add frontend/src/pages/GovernancePage.tsx frontend/src/lib/api.ts frontend/src/App.tsx frontend/src/components/Section.tsx frontend/src/components/QueryToolbar.tsx frontend/src/components/PaginationControls.tsx frontend/src/components/PageState.tsx
git commit -m "feat: add notification events to governance center"
```

### Task 4: Documentation and End-to-End Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture-and-runbook.md`
- Modify: `docs/superpowers/specs/2026-04-13-notification-governance-history-design.md` if implementation details need to be clarified after coding

- [x] **Step 1: Run full verification**

Run:

```bash
python3 -m pytest -q
python3 -m compileall app
npm --prefix frontend run build
```

Expected: all pass.

- [x] **Step 2: Update docs**

Document:

- the new notification governance section in `/governance`
- the audit projection conventions for notification events
- the fact that notification failures remain non-blocking

- [x] **Step 3: Commit**

```bash
git add README.md docs/architecture-and-runbook.md docs/superpowers/specs/2026-04-13-notification-governance-history-design.md
git commit -m "docs: document notification governance history"
```
