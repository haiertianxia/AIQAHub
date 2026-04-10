# Governance Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a read-only governance center at `/governance` that aggregates asset, gate, settings, connector, and audit signals into a single operational view.

**Architecture:** Keep the implementation as a read-only aggregation layer on top of the current services. Add a small governance service that computes overview counts and normalized events from existing tables and service outputs, then render a dedicated frontend page with overview cards, a filterable event stream, and a detail drawer.

**Tech Stack:** Python, FastAPI, SQLAlchemy, Pydantic, React, TypeScript, Vite, pytest.

---

### Task 1: Governance Data Contract

**Files:**
- Create: `app/schemas/governance.py`
- Modify: `app/services/audit_service.py`
- Modify: `app/services/asset_service.py`
- Modify: `app/services/gate_service.py`
- Modify: `app/services/settings_service.py`
- Modify: `app/services/connector_service.py`
- Modify: `app/schemas/audit.py`
- Modify: `app/schemas/asset.py`
- Modify: `app/schemas/gate.py`
- Modify: `app/schemas/settings.py`
- Modify: `app/schemas/connector.py`
- Test: `tests/api/test_governance.py`

- [x] **Step 1: Write the failing tests**

```python
def test_governance_overview_returns_recent_counts(client):
    ...

def test_governance_events_have_stable_ids(client):
    ...

def test_governance_event_detail_matches_event_stream(client):
    ...
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest tests/api/test_governance.py -v`
Expected: FAIL because the governance contract and endpoints do not exist yet.

- [x] **Step 3: Implement the governance schema and aggregation helpers**

Implement:
- overview read model
- normalized event read model
- deterministic event id generation
- UTC-normalized timestamps

- [x] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest tests/api/test_governance.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add app/schemas/governance.py app/services/audit_service.py app/services/asset_service.py app/services/gate_service.py app/services/settings_service.py app/services/connector_service.py app/schemas/audit.py app/schemas/asset.py app/schemas/gate.py app/schemas/settings.py app/schemas/connector.py tests/api/test_governance.py
git commit -m "feat: add governance data contract"
```

### Task 2: Governance API

**Files:**
- Create: `app/api/v1/routes/governance.py`
- Modify: `app/api/v1/router.py`
- Modify: `app/services/audit_service.py`
- Modify: `app/services/asset_service.py`
- Modify: `app/services/gate_service.py`
- Modify: `app/services/settings_service.py`
- Modify: `app/services/connector_service.py`
- Modify: `tests/api/test_governance.py`

- [x] **Step 1: Write the failing tests**

```python
def test_governance_overview_endpoint(client):
    ...

def test_governance_events_endpoint_filters_by_type(client):
    ...

def test_governance_event_detail_endpoint(client):
    ...
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest tests/api/test_governance.py -v`
Expected: FAIL because the route is not wired yet.

- [x] **Step 3: Add the governance routes**

Implement:
- `GET /api/v1/governance/overview`
- `GET /api/v1/governance/events`
- `GET /api/v1/governance/events/{id}`

- [x] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest tests/api/test_governance.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add app/api/v1/routes/governance.py app/api/v1/router.py app/services/audit_service.py app/services/asset_service.py app/services/gate_service.py app/services/settings_service.py app/services/connector_service.py tests/api/test_governance.py
git commit -m "feat: add governance api"
```

### Task 3: Governance Dashboard

**Files:**
- Create: `frontend/src/pages/GovernancePage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/components/Section.tsx` if needed
- Modify: `frontend/src/components/QueryToolbar.tsx` if needed
- Modify: `frontend/src/components/PaginationControls.tsx` if needed
- Modify: `frontend/src/components/PageState.tsx` if needed
- Test: `npm --prefix frontend run build`

- [x] **Step 1: Write the failing tests**

Use build verification and page-level expectations:
- the new page should compile
- the page should consume the governance API contract
- the page should render overview cards, event stream, and detail drawer

- [x] **Step 2: Run the build to verify it fails**

Run: `npm --prefix frontend run build`
Expected: FAIL before the page and types exist.

- [x] **Step 3: Implement the governance dashboard**

Implement:
- route at `/governance`
- overview cards
- filterable event stream
- detail drawer
- fallback error/empty/loading states

- [x] **Step 4: Run the build to verify it passes**

Run: `npm --prefix frontend run build`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add frontend/src/pages/GovernancePage.tsx frontend/src/App.tsx frontend/src/lib/api.ts frontend/src/components/Section.tsx frontend/src/components/QueryToolbar.tsx frontend/src/components/PaginationControls.tsx frontend/src/components/PageState.tsx
git commit -m "feat: add governance dashboard"
```
