# Playwright Execution Visibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Surface Playwright execution details inside the existing execution detail page, report detail page, and governance center using only existing summaries, artifacts, tasks, and audit projections.

**Architecture:** Playwright stays an execution adapter. The implementation only adds read-only UI projections for the existing `ExecutionRead.summary.playwright`, task rows, artifacts, and governance/audit rows. A small shared Playwright view-model module and a lightweight Vitest harness keep the execution, report, and governance pages consistent without introducing new endpoints, persistence, pages, or deep links.

**Tech Stack:** React, TypeScript, Vitest, Testing Library, FastAPI, SQLAlchemy, Pydantic, pytest, Vite.

---

### Task 1: Lock the raw Playwright data contract and add a frontend test harness

**Files:**
- Create: `frontend/vitest.config.ts`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`
- Create: `frontend/src/lib/playwright.ts`
- Create: `frontend/src/components/PlaywrightSummaryCard.tsx`
- Create: `frontend/src/components/PlaywrightSummaryCard.test.tsx`
- Create: `tests/api/test_playwright_execution.py`
- Modify: `tests/api/test_execution_worker.py`
- Modify: `tests/api/test_governance.py`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Write the failing test**

Add regression assertions that pin the raw Playwright data the UI will read:
- `tests/api/test_playwright_execution.py` should assert the execution detail payload still exposes the raw `summary.playwright` fields the UI needs (`job_name`, `job_id`, `status`, `completion_source`, `poll_count`, `browser`, `headless`, `base_url`).
- `tests/api/test_execution_worker.py` should keep the validation-failure and timeout paths locked to the same raw Playwright summary values.
- `tests/api/test_governance.py` should assert Playwright-related audit/governance rows still come from the existing audit-log projection and do not introduce a new event kind or new API shape.
- `frontend/src/components/PlaywrightSummaryCard.test.tsx` should render a raw Playwright summary object and prove the card does not normalize or remap values.
- `frontend/src/components/PlaywrightSummaryCard.test.tsx` should also render a partial Playwright summary and prove missing fields render as `-` instead of breaking the card.

```python
def test_playwright_summary_fields_remain_raw():
    payload = client.get(f"/api/v1/executions/{execution_id}").json()
    assert payload["summary"]["playwright"]["completion_source"] == "trigger"
    assert payload["summary"]["playwright"]["browser"] == "firefox"
```

- [ ] **Step 2: Run the tests to verify they fail on the current branch**

Run:
```bash
python3 -m pytest tests/api/test_playwright_execution.py tests/api/test_execution_worker.py tests/api/test_governance.py -q
npm --prefix frontend run test -- frontend/src/components/PlaywrightSummaryCard.test.tsx
```
Expected: FAIL until the Playwright view-model, card, and Vitest harness exist and the governance assertions are matched by the current projection data.

- [ ] **Step 3: Write the minimal implementation**

Implement a shared read-only helper module and card:
- `frontend/src/lib/playwright.ts` exposes type guards and field pickers for raw Playwright summary data.
- `frontend/src/components/PlaywrightSummaryCard.tsx` renders the raw summary fields and artifact links without normalization, and falls back to `-` for missing fields.
- `frontend/vitest.config.ts`, `frontend/package.json`, and `frontend/package-lock.json` add the minimal Vitest harness needed to exercise the card and page renderers.
- `frontend/package.json` should add a `test` script plus the Vitest, jsdom, and Testing Library packages required by the harness (`vitest`, `jsdom`, `@testing-library/react`, `@testing-library/dom`), then `npm --prefix frontend install` should refresh the lockfile.
- `frontend/src/lib/api.ts` exports the minimal Playwright summary and artifact shape used by the UI.

- [ ] **Step 4: Run the tests to verify they pass**

Run:
```bash
npm --prefix frontend run test -- frontend/src/components/PlaywrightSummaryCard.test.tsx
python3 -m pytest tests/api/test_playwright_execution.py tests/api/test_execution_worker.py tests/api/test_governance.py -q
npm --prefix frontend run build
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/vitest.config.ts frontend/package.json frontend/package-lock.json frontend/src/lib/playwright.ts frontend/src/components/PlaywrightSummaryCard.tsx frontend/src/components/PlaywrightSummaryCard.test.tsx frontend/src/lib/api.ts tests/api/test_playwright_execution.py tests/api/test_execution_worker.py tests/api/test_governance.py
git commit -m "feat: add raw playwright visibility contract"
```

### Task 2: Render Playwright details in execution detail

**Files:**
- Create: `frontend/src/pages/ExecutionDetailPage.test.tsx`
- Modify: `frontend/src/pages/ExecutionDetailPage.tsx`
- Modify: `frontend/src/lib/playwright.ts`
- Modify: `frontend/src/components/PlaywrightSummaryCard.tsx`

- [ ] **Step 1: Write the failing test**

Add a page regression that renders a mocked `ExecutionDetailPage` with a Playwright summary and asserts the Playwright panel shows the raw values only.

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
npm --prefix frontend run test -- frontend/src/pages/ExecutionDetailPage.test.tsx
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
npm --prefix frontend run test -- frontend/src/pages/ExecutionDetailPage.test.tsx
npm --prefix frontend run build
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ExecutionDetailPage.tsx frontend/src/pages/ExecutionDetailPage.test.tsx frontend/src/lib/playwright.ts frontend/src/components/PlaywrightSummaryCard.tsx
git commit -m "feat: show playwright details in execution detail"
```

### Task 3: Render Playwright summary in report detail

**Files:**
- Create: `frontend/src/pages/ReportDetailPage.test.tsx`
- Modify: `frontend/src/pages/ReportDetailPage.tsx`
- Modify: `frontend/src/components/PlaywrightSummaryCard.tsx`
- Modify: `tests/api/test_reports_gates_execution_detail.py`

- [ ] **Step 1: Write the failing test**

Add a report-detail regression that renders a mocked `ReportDetailPage` with Playwright artifacts/tasks and asserts the compact summary section stays raw.
- The assertion must cover raw `status`, raw `completion_source`, raw `poll_count`, and any fallback/validation notes that already exist in the current summary or projection.

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
npm --prefix frontend run test -- frontend/src/pages/ReportDetailPage.test.tsx
python3 -m pytest tests/api/test_reports_gates_execution_detail.py -q
```
Expected: FAIL until the report page is wired to the shared Playwright summary card and the assertions are updated.

- [ ] **Step 3: Write the minimal implementation**

Update `ReportDetailPage` to:
- render a compact Playwright summary section only from existing report/task/artifact fields,
- show raw `status`, `completion_source`, and `poll_count` values directly from the existing payload,
- show fallback or validation notes only if they already exist in the existing report summary or projection,
- keep the section read-only,
- keep the existing report summary, artifact, and task sections intact.

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
npm --prefix frontend run test -- frontend/src/pages/ReportDetailPage.test.tsx
python3 -m pytest tests/api/test_reports_gates_execution_detail.py -q
npm --prefix frontend run build
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ReportDetailPage.tsx frontend/src/pages/ReportDetailPage.test.tsx frontend/src/components/PlaywrightSummaryCard.tsx tests/api/test_reports_gates_execution_detail.py
git commit -m "feat: show playwright summary in report detail"
```

### Task 4: Surface Playwright rows in governance

**Files:**
- Create: `frontend/src/pages/GovernancePage.test.tsx`
- Modify: `frontend/src/pages/GovernancePage.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `tests/api/test_governance.py`

- [ ] **Step 1: Write the failing test**

Add a governance regression that asserts Playwright-related audit/projection rows remain visible through the existing governance stream and detail drawer.
Keep the assertion framed around the existing audit-log projection only; do not introduce a new kind, tab, or deep link. The row shape to lock is the existing `audit_event` projection emitted by `AuditService` for `AuditLog` rows with `source_type=audit_log`, `target_type=execution`, and `action` values that begin with `playwright_`.
- The concrete UI behavior should be a Playwright preset in the existing governance filter bar that sets the existing `kind=audit_event` and `search=playwright_` query fields, while the existing detail drawer continues to show the raw row payload.

- [ ] **Step 2: Run the test to verify it fails**

Run:
```bash
npm --prefix frontend run test -- frontend/src/pages/GovernancePage.test.tsx
python3 -m pytest tests/api/test_governance.py -q
```
Expected: FAIL until the governance page is wired to display the Playwright rows from the existing projection.

- [ ] **Step 3: Write the minimal implementation**

Update `GovernancePage` to:
- add a Playwright preset in the existing governance filter bar that sets the existing `kind=audit_event` and `search=playwright_` filters,
- keep the event list/detail drawer model unchanged,
- show only raw values already present in the governance projection,
- avoid adding any new route or event category.

- [ ] **Step 4: Run the test to verify it passes**

Run:
```bash
npm --prefix frontend run test -- frontend/src/pages/GovernancePage.test.tsx
python3 -m pytest tests/api/test_governance.py -q
npm --prefix frontend run build
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/GovernancePage.tsx frontend/src/pages/GovernancePage.test.tsx frontend/src/lib/api.ts tests/api/test_governance.py
git commit -m "feat: surface playwright rows in governance"
```

### Task 5: Final verification and cleanup

**Files:**
- Modify: none expected

- [ ] **Step 1: Run the full targeted verification**

Run:
```bash
npm --prefix frontend run test
python3 -m pytest tests/api/test_playwright_execution.py tests/api/test_execution_worker.py tests/api/test_reports_gates_execution_detail.py tests/api/test_governance.py -q
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
