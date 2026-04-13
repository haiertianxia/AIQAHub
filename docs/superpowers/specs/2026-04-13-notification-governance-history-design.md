# Notification Governance History Design

## Goal

Surface notification delivery history, failures, policy matches, and fallback behavior inside the existing governance center so operators can answer:

- what notifications were sent?
- which channel delivered them?
- did the notification use a project override or a global default?
- did delivery fail, skip, or fall back?
- which execution, gate, or AI event triggered the notification?

This should be an observability and audit view, not a new standalone notification page.

## Problem

The platform already supports:

- channel providers for email, DingTalk, and WeCom
- settings-backed notification policies
- notification tests from the settings page
- execution and gate events that trigger notifications opportunistically

However, notification sending is still operationally opaque:

- there is no central place to see which notifications were attempted
- policy routing decisions are not visible at a glance
- fallback and skip outcomes are not surfaced in the governance view
- notification behavior is not easy to audit alongside execution, gate, and AI events

The governance center already aggregates platform change signals, so notification delivery history should be added there instead of building a separate surface.

## Design Overview

Use the existing governance center as the single read-only operational view.

Notification sending should be recorded as structured audit/governance events whenever the platform:

- sends a notification for execution failure
- sends a notification for gate failure
- sends a notification test from settings
- falls back from a real provider to another provider
- skips delivery because a channel is disabled or not configured

The governance page should then expose a dedicated `Notification Events` section that is derived from those recorded events.

This first version should remain lightweight:

- do not add a new standalone notification page
- do not add a new notification history table
- do not change the non-blocking semantics of notification delivery
- do not make notification failures affect execution or gate status

## Data Source Strategy

Notification history should be derived from existing audit/governance records.

The notification service should write a structured audit entry for each attempt using the existing `audit_logs` table, with notification-specific semantics encoded in `action`, `target_type`, `request_json`, and `response_json`.

Recommended audit conventions:

- `target_type = "notification"`
- `action = "notification_send" | "notification_test" | "notification_skip" | "notification_fallback"`
- `target_id = <execution_id | gate_execution_id | settings_environment | synthetic test id>`

The payload should include fields such as:

- `event_type`
- `project_id`
- `channel`
- `provider`
- `status`
- `target`
- `policy_scope_type`
- `policy_scope_id`
- `fallback_from`
- `fallback_reason`
- `subject`
- `message`

The governance layer can then project those audit entries into notification events.

This keeps notification history:

- consistent with existing governance/audit patterns
- queryable alongside other platform signals
- free of new persistence tables in the first version

## Event Model

Extend the governance event vocabulary with notification-specific kinds:

- `notification_send`
- `notification_test`

Notification events should expose:

- `kind`
- `project_id`
- `environment`
- `status`
- `channel`
- `provider`
- `target`
- `subject`
- `message`
- `policy_scope_type`
- `policy_scope_id`
- `fallback_from`
- `fallback_reason`
- `created_at`

Notification events should also include the source trigger when known:

- execution failure
- gate failure
- settings test

## Proposed API

Reuse the existing governance API shape and extend it with notification filtering.

### `GET /api/v1/governance/overview`

Add notification-related summary counts to the last-24-hours overview:

- `notification_send_count`
- `notification_failed_count`
- `notification_fallback_count`
- `notification_skipped_count`

### `GET /api/v1/governance/events`

Support notification filtering in the unified event stream.

Suggested query parameters:

- `kind`
- `target_type`
- `project_id`
- `environment`
- `status`
- `search`
- `channel`
- `provider`
- `page`
- `page_size`

Notification events should appear in the same stream as asset, gate, settings, connector, and audit events.

### `GET /api/v1/governance/events/{id}`

Return a notification event detail payload with:

- raw audit payload
- policy match details
- fallback details
- jump links to the triggering execution, gate result, or settings page

## Notification Service Recording Rules

Notification sending should emit audit/governance records at the following points:

1. before dispatch
   - record the request intent and selected event type
2. after policy routing
   - record the chosen scope, channel, and subject
3. after dispatch
   - record success, failure, or skip
4. after fallback
   - record the fallback source and fallback reason

The governance projection should derive notification events from these audit records without introducing a separate history table in this version.

Notification tests triggered from settings should also be recorded so operators can tell test sends apart from operational sends.

## Frontend Layout

The governance center should continue to be the main surface at `/governance`.

Add a `Notification Events` section to the page with:

- summary cards for send/fail/fallback/skip counts
- a filterable event stream
- a detail drawer for the selected notification event
- jump links to the triggering page when available

Reuse the existing shared UI components:

- `QueryToolbar`
- `PaginationControls`
- `PageState`
- `Section`
- `Highlight`

## Error Handling

Notification governance should follow the same partial-failure model as the rest of the governance center:

- if notification projection fails, keep the rest of the governance view usable
- if one notification record lacks routing metadata, show the known fields and leave missing fields blank
- if the detail drawer fails, keep the event list usable
- if no notification events exist yet, show a clear empty state

Delivery failures should remain non-blocking:

- notification failures should not affect execution completion
- notification failures should not affect gate verdicts
- notification failures should be visible as governance outcomes, not runtime blockers

## Testing Strategy

Add coverage for:

- notification sends recorded as governance/audit events
- execution failure and gate failure both producing notification events
- settings test sends producing notification test events
- policy scope, channel, provider, fallback, and skip metadata appearing in governance projections
- governance overview counts including notification metrics
- frontend build success

Prefer tests that verify:

- notification events are visible in the governance stream
- notification failures do not change core execution or gate status
- notification history remains available through the governance center even when a provider falls back

## Out of Scope

This first version does not add:

- a standalone notification history page
- a dedicated notification database table
- websocket live streaming
- analytics dashboards for notification trend analysis
- retry orchestration or delivery backoff

## Success Criteria

The notification governance view is successful when:

- an operator can inspect notification delivery history from the governance center
- policy routing and fallback behavior are visible without opening raw logs
- notification failures are visible but non-blocking
- notification tests are distinguishable from operational sends
