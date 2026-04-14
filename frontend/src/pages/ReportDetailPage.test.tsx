import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ReportDetailPage } from "./ReportDetailPage";

const { getMock } = vi.hoisted(() => ({ getMock: vi.fn() }));
const { postMock } = vi.hoisted(() => ({ postMock: vi.fn() }));

vi.mock("../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../lib/api")>("../lib/api");
  return {
    ...actual,
    api: {
      ...actual.api,
      get: getMock,
      post: postMock,
    },
  };
});

describe("ReportDetailPage", () => {
  beforeEach(() => {
    getMock.mockReset();
    postMock.mockReset();
  });

  it("renders a compact raw playwright summary when report.summary.playwright exists", async () => {
    getMock.mockResolvedValueOnce({
      execution_id: "exe_playwright_report",
      status: "failed",
      summary: {
        status: "failed",
        playwright: {
          job_name: "pw-report",
          job_id: "playwright-pw-report",
          status: "failed",
          completion_source: "validation",
          poll_count: 1,
          browser: "chromium",
          headless: true,
          base_url: "https://sit.example.com",
          validation: {
            status: "failed",
            message: "Playwright connector misconfigured",
          },
          fallback_from: "openai",
          fallback_reason: "provider unavailable",
        },
      },
      artifacts: [
        {
          name: "playwright-html-report",
          uri: "memory://playwright/report/index.html",
          type: "playwright-html-report",
        },
      ],
      tasks: [
        {
          id: "task_pw_wait",
          task_key: "wait_for_playwright",
          task_name: "Wait For Playwright",
          status: "failed",
          output: {},
        },
      ],
      task_count: 1,
      completion_source: "validation",
      started_at: "2026-04-14T00:00:00Z",
      completed_at: "2026-04-14T00:01:00Z",
    });
    postMock.mockResolvedValueOnce({
      execution_id: "exe_playwright_report",
      result: "FAIL",
      score: 10,
      reason: "validation failed",
      task_count: 1,
      failed_tasks: 1,
      task_threshold: 1,
      completion_source: "validation",
    });

    render(
      <MemoryRouter initialEntries={["/reports/exe_playwright_report"]}>
        <Routes>
          <Route path="/reports/:executionId" element={<ReportDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(getMock).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(postMock).toHaveBeenCalledTimes(1));

    const card = screen.getByLabelText("Playwright summary");

    expect(within(card).getByText("pw-report")).toBeTruthy();
    expect(within(card).getByText("playwright-pw-report")).toBeTruthy();
    expect(within(card).getByText("failed")).toBeTruthy();
    expect(within(card).getByText("validation")).toBeTruthy();
    expect(within(card).getByText("1")).toBeTruthy();
    expect(within(card).getByText("chromium")).toBeTruthy();
    expect(within(card).getByText("true")).toBeTruthy();
    expect(within(card).getByText("https://sit.example.com")).toBeTruthy();
    expect(within(card).getByText(/Playwright connector misconfigured/)).toBeTruthy();
    expect(within(card).getByText(/Fallback from/)).toBeTruthy();
  });
});
