# Celery Worker Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current execution placeholder with a real Celery-backed local worker flow that updates execution state, records artifacts, and produces report-ready summaries.

**Architecture:** Keep AIQAHub's modular-monolith shape. Add a small execution contract in the orchestration layer, a local worker adapter backed by Celery tasks, and minimal service methods that transition executions through queued/running/success or failed states. The worker will persist artifacts and summary data to the existing database models so reports, gates, and audit logs continue to work without extra glue.

**Tech Stack:** Python, FastAPI, Celery, SQLAlchemy, pytest.

---

### Task 1: Define the execution contract and worker entrypoints

**Files:**
- Modify: `app/orchestration/engine.py`
- Modify: `app/orchestration/state_machine.py`
- Modify: `app/workers/execution_tasks.py`
- Modify: `app/workers/celery_app.py`
- Test: `tests/api/test_execution_worker.py`

- [ ] **Step 1: Write the failing test**

```python
def test_plan_and_run_execution_transition_and_persist_summary():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/api/test_execution_worker.py -q`
Expected: FAIL because planning/running helpers and worker state updates are not implemented yet.

- [ ] **Step 3: Write minimal implementation**

Add an orchestration helper that:
- moves an execution from `created` to `queued`
- dispatches a Celery task
- supports `queued -> running -> success|failed`
- returns a minimal summary payload

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/api/test_execution_worker.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/orchestration/engine.py app/orchestration/state_machine.py app/workers/execution_tasks.py app/workers/celery_app.py tests/api/test_execution_worker.py
git commit -m "feat: add celery execution contract"
```

### Task 2: Persist execution lifecycle updates

**Files:**
- Modify: `app/services/execution_service.py`
- Modify: `app/models/execution.py`
- Modify: `app/db/seed.py`
- Test: `tests/api/test_execution_worker.py`

- [ ] **Step 1: Write the failing test**

```python
def test_execution_run_updates_state_and_summary():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/api/test_execution_worker.py -q`
Expected: FAIL because execution status is still static after run dispatch.

- [ ] **Step 3: Write minimal implementation**

Add execution update helpers that:
- set status to `queued`
- record `running` and terminal status
- store `summary_json`
- preserve existing list/detail API shapes

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/api/test_execution_worker.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/execution_service.py app/models/execution.py app/db/seed.py tests/api/test_execution_worker.py
git commit -m "feat: persist execution lifecycle"
```

### Task 3: Wire the UI to the new worker flow

**Files:**
- Modify: `frontend/src/pages/ExecutionsPage.tsx`
- Modify: `frontend/src/pages/ExecutionDetailPage.tsx`
- Modify: `frontend/src/lib/api.ts`
- Test: `npm --prefix frontend run build`

- [ ] **Step 1: Write the failing test**

Use the build as the guardrail and add a focused UI test only if needed later. For now, the failing condition is the missing worker status fields in the API response contract.

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix frontend run build`
Expected: FAIL only if the API contract changes unexpectedly.

- [ ] **Step 3: Write minimal implementation**

Expose worker status and summary fields in the frontend types and show the state progression in the execution list/detail pages.

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix frontend run build`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ExecutionsPage.tsx frontend/src/pages/ExecutionDetailPage.tsx frontend/src/lib/api.ts
git commit -m "feat: surface celery execution status in ui"
```
