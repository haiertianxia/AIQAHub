import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { GovernancePage } from "./GovernancePage";

const { getMock } = vi.hoisted(() => ({ getMock: vi.fn() }));

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../lib/api")>("../lib/api");
  return {
    ...actual,
    api: {
      ...actual.api,
      get: getMock,
    },
  };
});

const overviewFixture = {
  window: "last_24h",
  window_start: "2026-04-14T00:00:00Z",
  window_end: "2026-04-14T23:59:59Z",
  asset_block_count: 0,
  gate_fail_count: 0,
  settings_rollback_count: 0,
  connector_error_count: 0,
  recent_audit_count: 1,
  recent_events: [],
  ai_provider: "mock",
  ai_model_name: "demo",
  ai_fallback_count: 0,
  notification_send_count: 0,
  notification_failed_count: 0,
  notification_skip_count: 0,
  notification_fallback_count: 0,
};

const eventFixture = {
  id: "gov_playwright_1",
  kind: "audit_event",
  source_type: "audit_log",
  source_id: "audit_playwright_1",
  timestamp: "2026-04-14T10:00:00Z",
  severity: "info",
  status: null,
  target_type: "execution",
  target_id: "exe_playwright_1",
  project_id: null,
  environment: null,
  channel: null,
  provider: null,
  target: null,
  event_type: null,
  policy_scope_type: null,
  policy_scope_id: null,
  fallback_from: null,
  fallback_reason: null,
  title: "Audit action: playwright_completed",
  description: "execution:exe_playwright_1",
  metadata: { actor_id: "system" },
};

const detailFixture = {
  ...eventFixture,
  raw: {
    actor_id: "system",
    action: "playwright_completed",
    target_type: "execution",
    target_id: "exe_playwright_1",
    request_json: { adapter: "playwright", job_name: "pw-regression" },
    response_json: { summary: { playwright: { job_name: "pw-regression" } } },
    note: "playwright governance projection",
  },
};

describe("GovernancePage", () => {
  beforeEach(() => {
    getMock.mockReset();
  });

  it("applies the playwright preset through existing governance filters", async () => {
    getMock
      .mockResolvedValueOnce(overviewFixture)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        {
          ...eventFixture,
          title: "Audit action: playwright_completed",
          description: "execution:exe_playwright_1",
        },
      ])
      .mockResolvedValueOnce(detailFixture);

    render(
      <MemoryRouter>
        <GovernancePage />
      </MemoryRouter>,
    );

    await waitFor(() => expect(getMock).toHaveBeenCalledWith("/governance/overview"));
    fireEvent.click(screen.getByRole("button", { name: "Playwright Preset" }));

    await waitFor(() =>
      expect(
        getMock.mock.calls.some(
          ([url]) =>
            typeof url === "string" &&
            url.startsWith("/governance/events?") &&
            url.includes("kind=audit_event") &&
            url.includes("target_type=execution") &&
            url.includes("search=playwright_"),
        ),
      ).toBe(true)
    );
    expect(screen.getByText("Audit action: playwright_completed")).toBeTruthy();
  });
});
