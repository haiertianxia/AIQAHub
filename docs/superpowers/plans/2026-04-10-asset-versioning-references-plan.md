# Asset Versioning and Reference Graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Status:** Implemented on `master`. This plan is retained as a historical record of the asset governance work already landed.

**Goal:** Turn the current asset registry into a governed asset system with revision history, reference tracking, and safe deletion rules.

**Architecture:** Keep `assets` as the active asset view and add two supporting tables: `asset_revisions` for immutable history and `asset_links` for inbound references. Put all lifecycle rules in the service layer so the API stays small, the frontend stays simple, and dependency protection is enforced in one place.

**Tech Stack:** Python, FastAPI, SQLAlchemy, Pydantic, React, TypeScript, Vite, pytest.

---

### Task 1: Asset Revision History

**Files:**
- Create: `app/models/asset_revision.py`
- Modify: `app/models/asset.py`
- Modify: `app/models/__init__.py`
- Modify: `app/crud/asset.py`
- Modify: `app/services/asset_service.py`
- Modify: `app/api/v1/routes/assets.py`
- Modify: `app/db/seed.py`
- Test: `tests/api/test_assets.py`

- [x] **Step 1: Write the failing tests**

```python
def test_create_asset_writes_initial_revision(client):
    ...

def test_update_asset_writes_new_revision(client):
    ...

def test_asset_revision_history_is_returned(client):
    ...
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest tests/api/test_assets.py -v`
Expected: FAIL because `asset_revisions` and revision history are not wired yet.

- [x] **Step 3: Implement the revision model and service behavior**

```python
class AssetRevision(Base):
    ...
```

Implement:
- initial revision on create
- revision write on update
- revision list endpoint

- [x] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest tests/api/test_assets.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add app/models/asset_revision.py app/models/asset.py app/models/__init__.py app/crud/asset.py app/services/asset_service.py app/api/v1/routes/assets.py app/db/seed.py tests/api/test_assets.py
git commit -m "feat: add asset revision history"
```

### Task 2: Asset Reference Graph and Delete Guard

**Files:**
- Create: `app/models/asset_link.py`
- Modify: `app/models/__init__.py`
- Modify: `app/crud/asset.py`
- Modify: `app/services/asset_service.py`
- Modify: `app/api/v1/routes/assets.py`
- Modify: `tests/api/test_assets.py`

- [x] **Step 1: Write the failing tests**

```python
def test_create_asset_link_records_reference(client):
    ...

def test_duplicate_asset_link_is_rejected(client):
    ...

def test_delete_asset_with_links_is_blocked(client):
    ...
```

- [x] **Step 2: Run the tests to verify they fail**

Run: `python3 -m pytest tests/api/test_assets.py -v`
Expected: FAIL because reference tracking and delete protection are not implemented yet.

- [x] **Step 3: Implement the reference graph and lifecycle guard**

```python
class AssetLink(Base):
    ...
```

Implement:
- link create/delete endpoints
- uniqueness for `(asset_id, ref_type, ref_id)`
- delete blocking when links exist
- soft archival only when removing an asset with no links

- [x] **Step 4: Run the tests to verify they pass**

Run: `python3 -m pytest tests/api/test_assets.py -v`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add app/models/asset_link.py app/models/__init__.py app/crud/asset.py app/services/asset_service.py app/api/v1/routes/assets.py tests/api/test_assets.py
git commit -m "feat: add asset reference graph"
```

### Task 3: Asset Governance UI

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Modify: `frontend/src/pages/AssetsPage.tsx`
- Test: `npm --prefix frontend run build`

- [x] **Step 1: Write the failing tests**

Use build-time verification plus manual UI review targets:
- asset list should show version and reference count
- asset detail should expose revision history
- asset detail should expose reference links

- [x] **Step 2: Run the build to verify the current UI does not yet include the governance view**

Run: `npm --prefix frontend run build`
Expected: PASS after the implementation lands, with the new governance sections present.

- [x] **Step 3: Implement the governance view**

Implement:
- revision history drawer or panel
- reference list panel
- current version badge
- delete/archive guard messaging

- [x] **Step 4: Run the build to verify it passes**

Run: `npm --prefix frontend run build`
Expected: PASS.

- [x] **Step 5: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/pages/AssetsPage.tsx
git commit -m "feat: expose asset governance view"
```
