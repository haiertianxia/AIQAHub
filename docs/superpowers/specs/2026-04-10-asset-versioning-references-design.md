# Asset Versioning and Reference Graph Design

## Goal

Turn `assets` from a simple registry into a governed platform capability with:

- current-state asset records
- version history
- reference tracking
- safe deletion / archival rules
- lightweight impact analysis

This is a platform hardening step, not a rewrite. The current `assets` table remains the source of truth for the active asset view.

## Problem

The current asset surface can create and list assets, but it cannot answer basic governance questions:

- Which version is active?
- Who is referencing this asset?
- Can this asset be safely deleted?
- What changed between revisions?
- What would be impacted if this asset changes?

Without a revision trail and reference graph, asset reuse is hard to trust and platform operations remain manual.

## Design Overview

Use a two-table extension around the existing `assets` table:

1. `assets`
   - stores the current active asset state
   - remains the primary list/detail source

2. `asset_revisions`
   - stores immutable snapshots of each asset change
   - provides history and rollback visibility

3. `asset_links`
   - stores inbound references to an asset
   - provides dependency visibility and deletion protection

This keeps the public surface simple while making the internal governance explicit.

## Data Model

### `assets`

Keep the current table shape:

- `id`
- `project_id`
- `asset_type`
- `name`
- `version`
- `source_ref`
- `metadata_json`
- `status`

Semantics:

- `version` is the current active version label
- `status` indicates lifecycle state such as `active` or `archived`
- `metadata_json` remains the extensibility point for asset-specific details

### `asset_revisions`

Proposed fields:

- `id`
- `asset_id`
- `version`
- `snapshot_json`
- `change_summary`
- `created_by`
- `created_at`

Semantics:

- every create or update writes a new revision row
- `snapshot_json` captures the asset payload at that point in time
- `change_summary` explains what changed in a human-readable way
- `(asset_id, version)` should be unique so the same revision label cannot be duplicated for one asset

### `asset_links`

Proposed fields:

- `id`
- `asset_id`
- `ref_type`
- `ref_id`
- `ref_name`
- `reason`
- `created_at`

Semantics:

- `ref_type` identifies the consumer category
- `reason` is required and explains why the reference exists
- links are inbound references used for deletion checks and impact analysis
- `(asset_id, ref_type, ref_id)` should be unique to avoid duplicate links for the same consumer

Supported `ref_type` values initially:

- `suite`
- `gate_rule`
- `settings`
- `ai_profile`
- `environment`

## Lifecycle Rules

### Create

- create the asset in `assets`
- write the first revision into `asset_revisions`
- do not require links at create time

### Update

- update the active `assets` row
- write a new revision row
- preserve the previous revision history

### Archive

- allow soft archival through `status=archived`
- keep revisions and links readable
- archived assets remain visible in history and impact views

### Delete

- if there are active links, deletion is blocked
- if there are no links, the first iteration should perform soft archival only by setting `status=archived`
- hard delete is out of scope for the first version
- deletion must be explicit and never silent

## API Surface

The asset API should remain small and composable:

- `GET /api/v1/assets`
- `POST /api/v1/assets`
- `PUT /api/v1/assets/{id}`
- `GET /api/v1/assets/{id}`
- `GET /api/v1/assets/{id}/revisions`
- `GET /api/v1/assets/{id}/links`
- `POST /api/v1/assets/{id}/links`
- `DELETE /api/v1/assets/{id}/links/{link_id}`

### Query semantics

`GET /api/v1/assets` should support:

- `project_id`
- `asset_type`
- `status`
- `search`

Search should cover the current asset record, not the entire revision log.

## Frontend Behavior

The asset page should evolve from a list-only surface into a governance view:

- list shows current version, status, and reference count
- detail drawer shows revision history
- references panel shows inbound links and their reasons
- empty and error states should stay non-blocking

This should stay lightweight. The goal is visibility, not a separate asset management product.

## Error Handling

The service layer should enforce these rules:

- duplicate active assets with the same logical identity should be rejected or handled explicitly
- updates that would violate link integrity should fail clearly
- delete attempts on referenced assets should return a descriptive error
- link creation should fail if the referenced target is unknown
- version conflicts should resolve in favor of the current persisted active row
- duplicate link creation should be rejected deterministically

Errors should explain:

- what asset was affected
- which reference blocked the action
- what the operator should do next

## Testing Strategy

Add coverage for:

- revision creation on asset create
- revision creation on asset update
- reference creation and deletion
- delete blocking when references exist
- filtered list queries by `project_id`, `asset_type`, `status`, and `search`
- revision history retrieval
- reference history retrieval

## Out of Scope

This design does not add:

- full semver enforcement
- compare/diff UI for revisions
- dependency graph visualization
- automatic migration of historical assets into revisions
- cross-project asset sharing rules

Those are future enhancements after the governance core is stable.

## Success Criteria

This design is successful when:

- every asset change leaves an audit trail in revisions
- every inbound consumer of an asset is visible in links
- delete protection prevents accidental dependency breakage
- list and detail views remain simple and fast
- tests verify governance behavior instead of only CRUD behavior
