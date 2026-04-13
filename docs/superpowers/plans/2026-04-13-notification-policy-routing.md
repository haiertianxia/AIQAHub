# Notification Policy Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement settings-backed notification policy routing with global defaults, project overrides, and non-blocking channel dispatch.

**Architecture:** Extend the existing settings history model to store policy data, add a notification service that resolves policies before dispatch, and keep provider adapters isolated by channel. Execution and gate flows call the service opportunistically; notification failures are captured and logged without affecting core status transitions.

**Tech Stack:** FastAPI, Pydantic, existing JSON-backed settings storage, pytest, local HTTP SMTP/webhook test servers, React/Vite.

---

### Task 1: Add notification policy test coverage

**Files:**
- Create: `tests/api/test_notification_policies.py`

- [x] **Step 1: Write the failing test**

```python
def test_project_policy_overrides_global_policy():
    ...
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/api/test_notification_policies.py -q`
Expected: FAIL because policy routing does not exist yet.

- [x] **Step 3: Write minimal implementation**

No implementation yet.

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/api/test_notification_policies.py -q`
Expected: PASS after routing is implemented.

- [x] **Step 5: Commit**

```bash
git add tests/api/test_notification_policies.py
git commit -m "test: cover notification policy routing"
```

### Task 2: Extend settings schema and persistence for policies

**Files:**
- Modify: `app/schemas/settings.py`
- Modify: `app/services/settings_service.py`
- Modify: `app/core/config.py`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/pages/SettingsPage.tsx`

- [x] **Step 1: Write the failing test**

Use Task 1 tests to drive the settings model fields.

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/api/test_notification_policies.py -q`
Expected: FAIL with missing policy fields or routing support.

- [x] **Step 3: Write minimal implementation**

Add `notification_policies` to `SettingsRead`, `SettingsUpdate`, and `SettingsHistoryEntry`, persist them in the existing JSON override/history files, and surface them in the Settings UI.

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/api/test_notification_policies.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add app/schemas/settings.py app/services/settings_service.py app/core/config.py frontend/src/lib/api.ts frontend/src/pages/SettingsPage.tsx
git commit -m "feat: persist notification policies in settings"
```

### Task 3: Implement notification policy resolver and routing

**Files:**
- Create: `app/services/notification_policy_service.py`
- Modify: `app/services/notification_service.py`
- Modify: `app/notifications/notifier.py`
- Modify: `app/api/v1/routes/notifications.py`

- [x] **Step 1: Write the failing test**

Use Task 1 tests to exercise project/global policy lookup and default fallback.

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/api/test_notification_policies.py -q`
Expected: FAIL because policy resolver and routing are missing.

- [x] **Step 3: Write minimal implementation**

Add a policy resolver that selects project overrides before global defaults, and dispatch through the existing channel providers.

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/api/test_notification_policies.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add app/services/notification_policy_service.py app/services/notification_service.py app/notifications/notifier.py app/api/v1/routes/notifications.py
git commit -m "feat: route notifications by policy"
```

### Task 4: Wire execution, gate, and AI fallback events to notification service

**Files:**
- Modify: `app/services/execution_service.py`
- Modify: `app/services/gate_service.py`
- Modify: `app/services/ai_service.py`
- Modify: `app/workers/notification_tasks.py`

- [x] **Step 1: Write the failing test**

Add tests that ensure a failed execution, a gate failure, and an AI fallback each trigger notification dispatch without breaking the main flow.

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/api/test_notification_policies.py -q`
Expected: FAIL before event wiring exists.

- [x] **Step 3: Write minimal implementation**

Call the notification service opportunistically from execution terminal transitions, gate failures, and AI fallback paths.

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/api/test_notification_policies.py -q`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add app/services/execution_service.py app/services/gate_service.py app/workers/notification_tasks.py
git commit -m "feat: wire notification events"
```

### Task 5: Verify end-to-end behavior and document usage

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture-and-runbook.md`

- [x] **Step 1: Run full verification**

Run:
```bash
python3 -m pytest -q
python3 -m compileall app
npm --prefix frontend run build
```
Expected: all pass.

- [x] **Step 2: Update docs**

Document notification policies, test endpoint, and supported channels.

- [x] **Step 3: Commit**

```bash
git add README.md docs/architecture-and-runbook.md
git commit -m "docs: document notification policy routing"
```
