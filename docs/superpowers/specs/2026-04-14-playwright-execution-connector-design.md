# Playwright Execution Connector Design

## Goal

Make Playwright a first-class execution connector for UI and end-to-end test runs so the platform can trigger, track, and summarize browser-based tests through the same `Execution -> Task -> Artifact -> Governance` pipeline already used by Jenkins and local worker executions.

The first version should be intentionally small:

- validate Playwright configuration
- trigger a Playwright execution job
- poll for completion
- collect execution artifacts
- surface the result in the existing execution, report, and governance views

Do not turn this into a separate browser automation product or a test authoring studio.

## Problem

The platform already has:

- a placeholder Playwright connector
- a unified execution model
- execution tasks and artifacts
- governance and reporting surfaces that can display execution outcomes

However, Playwright is not yet a real execution path:

- the connector only validates config
- the execution worker only knows about local/default steps and Jenkins
- UI/E2E runs cannot be triggered from the platform
- Playwright-specific artifacts such as traces, screenshots, videos, and HTML reports are not normalized into the shared execution pipeline

As a result, the platform still lacks a first-class UI/E2E execution connector even though that is a core fit for AIQAHub.

## Design Overview

Implement Playwright as a minimal execution connector that plugs into the existing execution worker flow.

The connector should stay lightweight:

- `validate_config()` confirms the connector is usable
- `trigger_job()` creates a Playwright job handle from execution parameters
- `get_job_status()` normalizes job status to the platform status vocabulary
- `list_artifacts()` returns the expected Playwright artifacts for the job

The execution worker should treat `adapter=playwright` as a first-class execution mode.

For the first version, the platform should:

- create Playwright-specific tasks inside the existing execution
- track `running / success / failed / timeout` outcomes using the shared execution state machine
- record Playwright artifacts in the same `ExecutionArtifact` table
- expose Playwright results through the existing execution detail, report detail, and governance views

## Connector Contract

Extend the Playwright connector so it mirrors the same shape as the Jenkins connector without introducing a new execution subsystem.

Recommended connector methods:

- `validate_config()`
- `trigger_job(job_name, parameters)`
- `get_job_status(job_name, job_id, final_status="success")`
- `list_artifacts(job_name, job_id)`

The connector should normalize all results to the shared platform connector status vocabulary:

- `created`
- `queued`
- `running`
- `success`
- `failed`
- `timeout`
- `canceled`

Playwright-specific details can live in the returned `details` payload, but the platform-facing status must remain normalized.

## Execution Flow

When an execution is created with `adapter=playwright` or `adapter_type=playwright`, the worker should:

1. mark the execution as running
2. create a `trigger_playwright` task
3. create a `wait_for_playwright` task when the job is long-running
4. record a shared summary that includes:
   - `completion_source`
   - `started_at`
   - `job_name`
   - `job_id`
   - `artifacts`
5. collect artifacts into the existing artifact table
6. finish the execution using the shared `success / failed / timeout` semantics

This should mirror the existing Jenkins flow closely enough that report, timeline, and governance consumers do not need connector-specific branches.

## Artifact Strategy

Normalize Playwright artifacts into the same execution artifact model used by all other execution types.

Expected artifact types for the first version:

- `playwright-trace`
- `playwright-screenshot`
- `playwright-video`
- `playwright-junit`
- `playwright-html-report`

Each artifact should store:

- `execution_id`
- `artifact_type`
- `name`
- `storage_uri`

The first version does not need a dedicated artifact store or separate Playwright report database table.

## Data Model

Do not add a new persistence table for Playwright in the first version.

Reuse existing execution data:

- `Execution.request_params_json` for Playwright job parameters
- `Execution.summary_json` for run state, completion source, and job metadata
- `ExecutionTask` for the trigger/poll lifecycle
- `ExecutionArtifact` for collected Playwright outputs

Suggested request parameters:

- `adapter = "playwright"`
- `job_name`
- `source_ref`
- `base_url`
- `browser`
- `headless`
- `suite_name`
- `report_mode`

Keep the request payload flexible so teams can pass browser-specific knobs without changing the schema every time.

## Proposed API and Service Changes

### Connector API

Expose Playwright through the existing connector test route:

- `POST /api/v1/connectors/playwright/test`

The test route should validate that the connector is configured, available, and able to produce a runnable Playwright job handle.

### Execution Worker

Extend the worker entrypoint so it recognizes Playwright as a first-class adapter:

- `run_execution`
- `wait_for_playwright`
- timeout sweep support for stuck Playwright jobs

### Execution Service

Keep the existing execution status transitions, timeline generation, and artifact recording APIs.

The only required change is to allow Playwright job metadata and task lifecycle data to flow through the same summary and task machinery as the other execution types.

### Frontend

The execution creation and detail views should be able to:

- select `playwright` as an adapter
- display Playwright job metadata in execution details
- show Playwright artifacts in the artifact section
- keep existing shared loading, empty, and error states

No separate Playwright page is required in the first version.

## Error Handling

Playwright execution should follow the same non-disruptive platform model used elsewhere:

- if Playwright config is missing, validation should fail clearly
- if job triggering fails, the task should fail and the execution should be marked failed
- if a job times out, the execution should be marked `timeout`
- if artifact collection fails, the execution outcome should still be preserved
- if the connector returns an unknown status, normalize it to the closest platform status and continue

Playwright failures should be visible in governance and reporting, but they should not break the rest of the platform.

## Testing Strategy

Add coverage for:

- Playwright connector config validation
- Playwright connector job triggering
- Playwright execution dispatch through the existing execution run flow
- Playwright status normalization
- Playwright artifact collection
- timeout handling for stuck Playwright executions
- report and governance visibility of Playwright outcomes

The integration tests should verify that:

- a Playwright execution can be created and run through the platform
- the resulting execution shows up in reports and governance
- artifacts are recorded in the shared artifact table
- failure or timeout does not break the rest of the execution pipeline

## Out of Scope

This first version does not add:

- a browser recording studio
- a Playwright test authoring UI
- a trace viewer
- a video player
- distributed browser orchestration
- a dedicated Playwright persistence model

## Success Criteria

The Playwright execution connector is successful when:

- operators can launch Playwright-based UI/E2E runs from the platform
- the execution lifecycle is visible in the same task and timeline model as other connectors
- Playwright artifacts appear in the shared execution artifact store
- governance and reporting surfaces can summarize Playwright executions without special casing

