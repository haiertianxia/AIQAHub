# Notification Policy Routing Design

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add configurable notification policies so execution failures, gate failures, and AI fallback events can route to project-scoped and global channels.

**Architecture:** Keep routing inside the existing settings-backed configuration model. A notification event is resolved through layered policy lookup: project override first, then global default. Providers remain channel-specific adapters, while notification dispatch stays non-blocking and returns structured results for audit and UI display.

**Tech Stack:** FastAPI, Pydantic, existing settings JSON history, local webhook/SMTP test servers, pytest, React/Vite.

---

## Problem Statement

Notification delivery is currently channel-aware, but policy-aware routing is missing. The platform can send messages to email, DingTalk, and WeCom, yet there is no way to say which event should go to which channel for a specific project.

This feature adds that missing control plane:
- global default notification policies
- project-level overrides
- event-specific routing for `execution_failed`, `gate_failed`, and `ai_fallback`
- settings persistence and rollback support
- non-blocking dispatch that never breaks the core execution or gate flow

## Goals

- Route notifications by event type and project scope.
- Keep global defaults and project overrides in the existing settings history model.
- Continue to support `email`, `dingtalk`, and `wecom` providers.
- Make notification sending auditable and testable.
- Preserve the invariant that notification failures do not change execution or gate results.

## Non-Goals

- Do not build a full expression language or query DSL.
- Do not add environment-level overrides in this iteration.
- Do not introduce a database-backed rules engine.
- Do not block execution or gate paths on notification failures.

## Proposed Data Model

Store notification policy data in settings overrides/history with the following structure:

```json
{
  "notification_policies": [
    {
      "scope_type": "global",
      "scope_id": "",
      "event_type": "execution_failed",
      "enabled": true,
      "channels": ["dingtalk", "wecom"],
      "subject_template": "Execution failed: {execution_id}",
      "filters": {
        "project_id": ["proj_demo"],
        "env_type": ["prod"]
      }
    }
  ]
}
```

Supported fields:
- `scope_type`: `global` or `project`
- `scope_id`: empty for global, project id for project overrides
- `event_type`: `execution_failed`, `gate_failed`, `ai_fallback`
- `enabled`: boolean switch
- `channels`: ordered channel list
- `subject_template`: optional format string
- `filters`: optional exact-match filters for `project_id`, `env_type`, and `severity`

## Routing Rules

1. Determine the event type from the caller.
2. Load current settings for the active environment.
3. Search for a matching project-level policy first.
4. Fall back to global policy if no project policy matches.
5. If no policy matches, use `notification_default_channel`.
6. Send once per configured channel in order.
7. Return structured results for each channel without raising a fatal error to the business flow.

## Failure Handling

- If a policy is disabled, treat it as skipped.
- If a channel is disabled or misconfigured, return a failed send result for that channel only.
- If all channels fail, record the error in the notification result but do not fail the triggering execution or gate evaluation.
- If a policy lookup fails, use the default channel and continue.

## UI Requirements

The Settings page should expose:
- default notification channel
- provider configuration fields for email, DingTalk, and WeCom
- a policy list grouped by global and project scope
- create/edit/delete/toggle actions for policies
- a test notification action for the selected policy

## API Requirements

Add notification endpoints:
- `POST /api/v1/notifications/test`

Notification policy editing should reuse the existing settings endpoints by extending `SettingsRead` / `SettingsUpdate` with `notification_policies`.

## Testing Requirements

Add tests for:
- project policy overrides global policy
- global policy is used when no project policy exists
- disabled policy is skipped
- notification failures do not break execution, gate completion, or AI fallback
- test notification endpoint uses the selected channel and target
