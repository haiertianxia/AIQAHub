# Playwright Execution Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface Playwright execution details inside the existing execution detail page, report detail page, and governance center using only existing summaries, artifacts, tasks, and audit projections.

**Architecture:** Playwright stays an execution adapter. The implementation only adds read-only UI projections for the existing `ExecutionRead.summary.playwright`, task rows, artifacts, and governance/audit rows. A small shared Playwright view-model module keeps the execution and report pages consistent without introducing new endpoints, persistence, pages, or deep links.

**Tech Stack:** React, TypeScript, FastAPI, SQLAlchemy, Pydantic, pytest, Vite.

---

### Task 1: Lock the raw Playwright data contract

**Files:**
- Create: `frontend/src/lib/playwright.ts`
- Create: `frontend/src/components/PlaywrightSummaryCard.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `tests/api/test_playwright_execution.py`
- Modify: `tests/api/test_governance.py`

- [ ] **Step 1: Write the failing test**

Add regression assertions that pin the raw Playwright data the UI will read:
- `tests/api/test_playwright_execution.py` should assert the execution detail payload still exposes the raw `summary.playwright` fields the UI needs (`job_name`, `job_id`, `status`, `completion_source`, `poll_count`, `browser`, `headless`, `base_url`).
- `tests/api/test_governance.py` should assert Playwright-related audit/governance rows still come from the existing audit-log projection and do not introduce a new event kind or new API shape.

```python
def test_playwright_summary_fields_remain_raw():
    payload = client.get(f"/api/v1/executions/{execution_id}").json()
    assert payload["summary"]["playwright"]["completion_source"] == "trigger"
    assert payload["summary"]["playwright"]["browser"] == "firefox"
```

- [ ] **Step 2: Run the tests to verify they fail on the current branch**

Run:
```bash
python3 -m pytest tests/api/test_playwright_execution.py tests/api/test_governance.py -q
```
Expected: FAIL until the Playwright view-model and card exist and the governance assertions are matched by the current projection data.

- [ ] **Step 3: Write the minimal implementation**

Implement a shared read-only helper module and card:
- `frontend/src/lib/playwright.ts` exposes type guards and field pickers for raw Playwright summary data.
- `frontend/src/components/PlaywrightSummaryCard.tsx` renders the raw summary fields and artifact links without normalization.
- `frontend/src/lib/api.ts` exports the minimal Playwright summary and artifact shape used by the UI.

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
python3 -m pytest tests/api/test_playwright_execution.py tests/api/test_governance.py -q
npm --prefix frontend run build
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/playwright.ts frontend/src/components/PlaywrightSummaryCard.tsx frontend/src/lib/api.ts tests/api/test_playwright_execution.py tests/api/test_governance.py
git commit -m "feat: add raw playwright visibility contract"
```

### Task 2: Render Playwright details in execution detail

**Files:**
- Modify: `frontend/src/pages/ExecutionDetailPage.tsx`
- Modify: `frontend/src/lib/playwright.ts`
- Modify: `frontend/src/components/PlaywrightSummaryCard.tsx`

- [ ] **Step 1: Write the failing test**

Add an execution-detail regression that asserts the page can read and render the Playwright panel from `execution.summary.playwright` without requiring any new endpoint or page.

Because there is no frontend test harness in the repo, use the build as the failing gate: wire the page to the new card and helper in a way that breaks the current build first, then fix it in the implementation step.

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
npm --prefix frontend run build
```
Expected: FAIL until the execution page imports and uses the new Playwright card/helper correctly.

- [ ] **Step 3: Write the minimal implementation**

Update `ExecutionDetailPage` to:
- show a dedicated Playwright panel only when `summary.playwright` exists,
- render raw values only,
- show artifact links using the existing artifact list,
- keep the rest of the execution detail page unchanged.

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
npm --prefix frontend run build
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ExecutionDetailPage.tsx frontend/src/lib/playwright.ts frontend/src/components/PlaywrightSummaryCard.tsx
git commit -m "feat: show playwright details in execution detail"
```

### Task 3: Render Playwright summary in report detail

**Files:**
- Modify: `frontend/src/pages/ReportDetailPage.tsx`
- Modify: `frontend/src/components/PlaywrightSummaryCard.tsx`
- Modify: `tests/api/test_reports_gates_execution_detail.py`

- [ ] **Step 1: Write the failing test**

Extend the report-detail regression so that the raw report payload used by the page still contains the artifacts and tasks needed by the Playwright summary card.
Add assertions that the report detail page should be able to read:
- raw execution status,
- raw completion source,
- raw poll count,
- artifact rows from the existing report response.

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/api/test_reports_gates_execution_detail.py -q
```
Expected: FAIL until the report page is wired to the shared Playwright summary card and the assertions are updated.

- [ ] **Step 3: Write the minimal implementation**

Update `ReportDetailPage` to:
- render a compact Playwright summary section only from existing report/task/artifact fields,
- keep the section read-only,
- keep the existing report summary, artifact, and task sections intact.

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
python3 -m pytest tests/api/test_reports_gates_execution_detail.py -q
npm --prefix frontend run build
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ReportDetailPage.tsx frontend/src/components/PlaywrightSummaryCard.tsx tests/api/test_reports_gates_execution_detail.py
git commit -m "feat: show playwright summary in report detail"
```

### Task 4: Surface Playwright rows in governance

**Files:**
- Modify: `frontend/src/pages/GovernancePage.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `tests/api/test_governance.py`

- [ ] **Step 1: Write the failing test**

Extend the governance regression to assert that Playwright-related audit/projection rows remain visible through the existing governance stream and detail drawer.
Keep the assertion framed around the existing audit-log projection only; do not introduce a new kind, tab, or deep link.

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
python3 -m pytest tests/api/test_governance.py -q
```
Expected: FAIL until the governance page is wired to display the Playwright rows from the existing projection.

- [ ] **Step 3: Write the minimal implementation**

Update `GovernancePage` to:
- surface Playwright-related rows in the existing event stream,
- keep the event list/detail drawer model unchanged,
- show only raw values already present in the governance projection,
- avoid adding any new route or event category.

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
python3 -m pytest tests/api/test_governance.py -q
npm --prefix frontend run build
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/GovernancePage.tsx frontend/src/lib/api.ts tests/api/test_governance.py
git commit -m "feat: surface playwright rows in governance"
```

### Task 5: Final verification and cleanup

**Files:**
- Modify: none expected

- [ ] **Step 1: Run the full targeted verification**

Run:
```bash
python3 -m pytest tests/api/test_playwright_execution.py tests/api/test_reports_gates_execution_detail.py tests/api/test_governance.py -q
npm --prefix frontend run build
```
Expected: PASS.

- [ ] **Step 2: Check the worktree**

Run:
```bash
git status --short
```
Expected: no unexpected files outside the Playwright visibility change set.

- [ ] **Step 3: Commit if any cleanup was needed**

If cleanup introduced any tracked changes, commit them with:

```bash
git add .
git commit -m "chore: finalize playwright visibility cleanup"
```

