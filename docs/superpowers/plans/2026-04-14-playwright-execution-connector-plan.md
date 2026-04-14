# Playwright Execution Connector Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use @superpowers:subagent-driven-development (recommended) or @superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Playwright a first-class execution connector that can be configured, triggered, polled, and summarized through the existing execution pipeline.

**Architecture:** Keep Playwright inside the current worker/process model and reuse the existing `Execution`, `ExecutionTask`, `ExecutionArtifact`, governance, and reporting surfaces. The first version should use a persisted platform job handle under `summary.playwright.*`, collect only the essential v1 artifacts, and expose the result through the current execution and governance views without adding a separate Playwright subsystem.

**Tech Stack:** Python, FastAPI, SQLAlchemy, Pydantic, Celery, React, TypeScript, Vite, pytest.

---

### Task 1: Playwright Connector Contract and Settings Validation

**Files:**
- Modify: `app/core/config.py`
- Modify: `app/connectors/playwright/client.py`
- Modify: `app/api/v1/routes/connectors.py`
- Modify: `app/schemas/connector.py`
- Modify: `app/services/connector_service.py`
- Test: `tests/api/test_connectors.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_playwright_connector_fails_when_disabled(client):
    ...

def test_playwright_connector_requires_command_and_workdir(client):
    ...

def test_playwright_connector_test_route_returns_normalized_result(client):
    ...
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `python3 -m pytest tests/api/test_connectors.py -q`
Expected: FAIL because Playwright validation still returns an unconditional success result and the route does not enforce the new config semantics.

- [ ] **Step 3: Implement the minimal connector contract**

Add:

- `playwright_enabled`
- `playwright_command`
- `playwright_workdir`
- optional defaults for base URL / browser / headless

Update the Playwright connector so `validate_config()` fails clearly when required settings are missing or disabled, and `test_connector("playwright", ...)` returns a normalized `ConnectorRead`.

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run: `python3 -m pytest tests/api/test_connectors.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/core/config.py app/connectors/playwright/client.py app/api/v1/routes/connectors.py app/schemas/connector.py app/services/connector_service.py tests/api/test_connectors.py
git commit -m "feat: harden playwright connector validation"
```

### Task 2: Playwright Execution Worker Path

**Files:**
- Modify: `app/workers/execution_tasks.py`
- Modify: `app/services/execution_service.py`
- Modify: `app/connectors/playwright/client.py`
- Modify: `app/schemas/execution.py`
- Modify: `app/schemas/connector.py`
- Test: `tests/api/test_playwright_execution.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_playwright_execution_creates_playwright_summary(client):
    ...

def test_playwright_execution_records_required_artifacts(client):
    ...

def test_playwright_execution_timeout_is_swept(client):
    ...
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `python3 -m pytest tests/api/test_playwright_execution.py -q`
Expected: FAIL because the worker does not yet branch on `adapter=playwright`, and the summary/artifact structure is missing.

- [ ] **Step 3: Implement the minimal worker path**

Extend `run_execution` so `adapter=playwright`:

- creates a `trigger_playwright` task
- stores a persisted handle under `summary.playwright`
- creates `wait_for_playwright` when the trigger returns a non-terminal status
- records `playwright-junit` and `playwright-html-report` artifacts in `ExecutionArtifact`
- uses the existing execution state machine for `running / success / failed / timeout`

Keep trace/screenshot/video collection best-effort only.

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run: `python3 -m pytest tests/api/test_playwright_execution.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/workers/execution_tasks.py app/services/execution_service.py app/connectors/playwright/client.py app/schemas/execution.py app/schemas/connector.py tests/api/test_playwright_execution.py
git commit -m "feat: add playwright execution worker path"
```

### Task 3: Execution Detail, Report, and Governance Visibility

**Files:**
- Modify: `app/services/report_service.py`
- Modify: `app/services/governance_service.py` if connector/execution projection needs a small adjustment
- Modify: `frontend/src/pages/ExecutionDetailPage.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/pages/GovernancePage.tsx` if Playwright needs a small visibility tweak
- Test: `tests/api/test_playwright_execution.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_playwright_execution_appears_in_report_and_governance(client):
    ...

def test_playwright_summary_uses_namespaced_metadata(client):
    ...
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `python3 -m pytest tests/api/test_playwright_execution.py -q`
Expected: FAIL until the report and governance consumers understand the `summary.playwright.*` namespace.

- [ ] **Step 3: Implement the minimal visibility updates**

Ensure the shared summary keeps:

- `summary.playwright.job_name`
- `summary.playwright.job_id`
- `summary.playwright.status`
- `summary.playwright.artifacts`
- `summary.playwright.completion_source`

Update the execution detail page so it renders Playwright metadata and artifact links from the shared execution/artifact model.

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run: `python3 -m pytest tests/api/test_playwright_execution.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add app/services/report_service.py app/services/governance_service.py frontend/src/pages/ExecutionDetailPage.tsx frontend/src/lib/api.ts frontend/src/pages/GovernancePage.tsx tests/api/test_playwright_execution.py
git commit -m "feat: surface playwright execution in reporting"
```

### Task 4: Settings and Documentation

**Files:**
- Modify: `frontend/src/pages/SettingsPage.tsx`
- Modify: `README.md`
- Modify: `docs/architecture-and-runbook.md`
- Modify: `docs/superpowers/specs/2026-04-14-playwright-execution-connector-design.md` only if implementation details need clarification after coding
- Test: `tests/api/test_control_pages.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_settings_page_exposes_playwright_fields(client):
    ...
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run: `python3 -m pytest tests/api/test_control_pages.py -q`
Expected: FAIL if the settings page or its API contract does not yet expose the required Playwright controls.

- [ ] **Step 3: Update the settings page and docs**

Expose the Playwright settings fields and document:

- required env/config values
- summary namespace conventions
- v1 artifact scope
- governance visibility behavior

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run: `python3 -m pytest tests/api/test_control_pages.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/SettingsPage.tsx README.md docs/architecture-and-runbook.md docs/superpowers/specs/2026-04-14-playwright-execution-connector-design.md tests/api/test_control_pages.py
git commit -m "docs: document playwright execution connector"
```

### Task 5: End-to-End Verification

**Files:**
- All files touched above

- [ ] **Step 1: Run the full verification suite**

Run:

```bash
python3 -m pytest -q
python3 -m compileall app tests/api
npm --prefix frontend run build
```

Expected: all pass.

- [ ] **Step 2: Commit or clean up**

If any final adjustment is needed, make it now, then commit the final state of the branch.

```bash
git add .
git commit -m "feat: finalize playwright execution connector"
```

