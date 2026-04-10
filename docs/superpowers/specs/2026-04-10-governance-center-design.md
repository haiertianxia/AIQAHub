# Governance Center Design

## Goal

Build a unified governance center that aggregates platform change signals across assets, gates, settings, connectors, and audit logs into a single operational view.

## Problem

The platform now has several strong but isolated governance surfaces:

- asset revisions and reference graphs
- gate rule history and evaluation results
- settings history and rollback
- connector status and validation
- audit logs

These surfaces work well individually, but operators still have to hop between pages to answer basic questions:

- what changed recently?
- what is blocked right now?
- what was rolled back?
- which connector is unhealthy?
- which object is the source of the problem?

The governance center should unify those answers without introducing a new persistence layer.

## Design Overview

Use a read-only aggregation layer on top of the existing services and tables.

The governance center should:

- summarize current risk and change counts
- expose a unified event stream
- provide a details view for a selected event
- support filtering by object type, environment, project, status, and search

The first version should be intentionally lightweight and should not introduce new database tables.

## Data Sources

The governance center should compose data from:

- `AuditService`
- `AssetService`
- `GateService`
- `SettingsService`
- `ConnectorService`

Derived signals can be computed from existing tables and service responses:

- asset impact blocks from asset links
- gate changes from quality rule audit and revision history
- settings rollbacks from settings history
- connector health from connector status
- audit totals from audit logs

## Proposed API

### `GET /api/v1/governance/overview`

Return summary cards for the dashboard header.

Suggested fields:

- `asset_block_count`
- `gate_fail_count`
- `settings_rollback_count`
- `connector_error_count`
- `recent_audit_count`
- `recent_events`

`recent_events` should be a compact list of high-signal items for first paint.

### `GET /api/v1/governance/events`

Return the unified, filterable event stream.

Suggested query parameters:

- `type`
- `target_type`
- `project_id`
- `environment`
- `status`
- `search`
- `page`
- `page_size`

Event rows should be derived, not independently stored.

### `GET /api/v1/governance/events/{id}`

Return the event detail payload for a selected item.

Suggested fields:

- `id`
- `type`
- `target_type`
- `target_id`
- `summary`
- `source`
- `related_objects`
- `blocking_reasons`
- `raw_payload`

The detail payload should support deep linking back to the owning domain page.

## Event Model

The governance center should normalize the platform into a small set of event kinds:

- `asset_change`
- `asset_block`
- `gate_change`
- `gate_fail`
- `settings_update`
- `settings_rollback`
- `connector_status`
- `audit_event`

Each event should expose:

- `type`
- `target_type`
- `target_id`
- `project_id`
- `environment`
- `status`
- `message`
- `created_at`

This keeps the UI and filtering logic stable even as the underlying sources grow.

## Frontend Layout

The page should be a dedicated governance dashboard with three regions:

1. Overview row
   - asset blocks
   - gate fails
   - settings rollbacks
   - connector errors
   - audit total

2. Event stream
   - filterable list
   - paginated
   - clickable rows

3. Detail drawer
   - raw event payload
   - related objects
   - jump links to the owning pages

Shared UI utilities should be reused:

- `QueryToolbar`
- `PaginationControls`
- `PageState`
- `Section`
- `Highlight`

## Error Handling

The governance center is a read-only operational surface, so partial failures should degrade gracefully:

- if one source fails, show the rest of the overview
- if the event stream fails, keep the overview visible and show a local error state
- if the detail drawer fails, keep the list usable
- if there are no events, show a clear empty state

The page should never fail closed just because one source is unavailable.

## Testing Strategy

Add coverage for:

- overview counts and recent items
- event stream filtering
- event pagination
- event detail lookup
- partial failure resilience
- frontend build success

Prefer tests that verify the page remains usable even when one source is unavailable.

## Out of Scope

This first version does not add:

- a new database table
- a graph visualization
- real-time websocket streaming
- automatic incident creation
- mutation actions from the governance center

Those can be revisited after the read-only dashboard proves useful.

## Success Criteria

The governance center is successful when:

- an operator can answer "what changed?" from one page
- blocked assets, failed gates, and rolled-back settings are visible together
- connector issues and audit noise are grouped into one operational surface
- all data is derived from existing platform sources
- the page remains useful even if one source is temporarily unavailable

