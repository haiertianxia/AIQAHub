# AIQAHub Platform Finalization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the remaining platformization work by unifying query semantics, completing the core domain surfaces, and hardening configuration, gate, connector, and asset boundaries.

**Architecture:** Keep the current FastAPI + SQLAlchemy backend and React + Vite frontend. Add a shared query contract and helper layer first, then tighten the domain modules that still have partial CRUD or read-only behavior. Preserve existing response shapes where possible so the work lands as an incremental hardening pass rather than a rewrite.

**Tech Stack:** Python, FastAPI, SQLAlchemy, Pydantic, React, TypeScript, Vite, pytest.

---

### Task 1: Unified Query Contract

**Files:**
- Create: `app/schemas/query.py`
- Create: `app/services/query_filters.py`
- Modify: `app/api/v1/routes/executions.py`
- Modify: `app/api/v1/routes/reports.py`
- Modify: `app/api/v1/routes/audit.py`
- Modify: `app/api/v1/routes/ai.py`
- Modify: `app/services/execution_service.py`
- Modify: `app/services/report_service.py`
- Modify: `app/services/audit_service.py`
- Modify: `app/services/ai_service.py`
- Modify: `frontend/src/pages/ExecutionsPage.tsx`
- Modify: `frontend/src/pages/ReportsPage.tsx`
- Modify: `frontend/src/pages/AuditPage.tsx`
- Modify: `frontend/src/pages/AiHistoryPage.tsx`
- Test: `tests/api/test_query_contract.py`

- [x] **Step 1: Write the failing tests**

```python
def test_query_params_are_shared_across_list_endpoints(client):
    ...
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest tests/api/test_query_contract.py -v`
Expected: FAIL because the shared query model and helpers do not exist yet.

- [x] **Step 3: Implement the shared query schema and filter helpers**

```python
class ListQueryParams(BaseModel):
    ...
```

- [x] **Step 4: Wire each list endpoint to the shared contract**

Run: `python3 -m pytest tests/api/test_query_contract.py -v`
Expected: PASS.

- [x] **Step 5: Update frontend query parameter mapping**

Run: `npm --prefix frontend run build`
Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add app/schemas/query.py app/services/query_filters.py ...
git commit -m "feat: unify query contract across platform lists"
```

### Task 2: Suites and Environments Hardening

**Files:**
- Modify: `app/services/suite_service.py`
- Modify: `app/api/v1/routes/suites.py`
- Modify: `frontend/src/pages/SuitesPage.tsx`
- Modify: `frontend/src/pages/ExecutionsPage.tsx`
- Modify: `app/services/environment_service.py`
- Modify: `app/api/v1/routes/environments.py`
- Modify: `frontend/src/pages/EnvironmentsPage.tsx` if created
- Test: `tests/api/test_suites_environments.py`

- [x] **Step 1: Write the failing tests**
- [x] **Step 2: Run the tests to verify they fail**
- [x] **Step 3: Add suite and environment CRUD/validation hardening**
- [x] **Step 4: Run the tests to verify they pass**
- [x] **Step 5: Commit**

### Task 3: Settings Configuration Center

**Files:**
- Modify: `app/schemas/settings.py`
- Modify: `app/services/settings_service.py`
- Modify: `app/api/v1/routes/settings.py`
- Modify: `frontend/src/pages/SettingsPage.tsx`
- Modify: `tests/api/test_control_pages.py`

- [x] **Step 1: Write the failing tests**
- [x] **Step 2: Run the tests to verify they fail**
- [x] **Step 3: Add editable config fields and save/test flow**
- [x] **Step 4: Run the tests to verify they pass**
- [x] **Step 5: Commit**

### Task 4: Gate Versioning and Policy Boundaries

**Files:**
- Modify: `app/models/quality_rule.py`
- Modify: `app/services/gate_service.py`
- Modify: `app/api/v1/routes/gates.py`
- Modify: `frontend/src/pages/GatesPage.tsx`
- Test: `tests/api/test_gates.py`

- [x] **Step 1: Write the failing tests**
- [x] **Step 2: Run the tests to verify they fail**
- [x] **Step 3: Add rule versioning, policy scope, and history**
- [x] **Step 4: Run the tests to verify they pass**
- [x] **Step 5: Commit**

### Task 5: Connector Contract Unification

**Files:**
- Modify: `app/connectors/base.py`
- Modify: `app/connectors/jenkins/client.py`
- Modify: `app/connectors/playwright/client.py`
- Modify: `app/connectors/llm/client.py`
- Modify: `app/services/connector_service.py`
- Modify: `app/workers/execution_tasks.py`
- Test: `tests/api/test_connectors.py`
- Test: `tests/api/test_jenkins_webhook.py`

- [x] **Step 1: Write the failing tests**
- [x] **Step 2: Run the tests to verify they fail**
- [x] **Step 3: Normalize connector interfaces and status mapping**
- [x] **Step 4: Run the tests to verify they pass**
- [x] **Step 5: Commit**

### Task 6: Asset Registry Completion

**Files:**
- Modify: `app/services/asset_service.py`
- Modify: `app/api/v1/routes/assets.py`
- Modify: `frontend/src/pages/AssetsPage.tsx`
- Test: `tests/api/test_assets.py` if new coverage is needed

- [x] **Step 1: Write the failing tests**
- [x] **Step 2: Run the tests to verify they fail**
- [x] **Step 3: Add asset versioning, references, and filtering**
- [x] **Step 4: Run the tests to verify they pass**
- [x] **Step 5: Commit**
