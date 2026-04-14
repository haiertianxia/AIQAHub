import { render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { describe, expect, it, vi, beforeEach } from "vitest";

import { ExecutionDetailPage } from "./ExecutionDetailPage";

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

describe("ExecutionDetailPage", () => {
  beforeEach(() => {
    getMock.mockReset();
    postMock.mockReset();
  });

  it("renders a playwright panel with raw summary values when summary.playwright exists", async () => {
    getMock
      .mockResolvedValueOnce({
        id: "exe_playwright_demo",
        project_id: "proj_demo",
        suite_id: "suite_demo",
        env_id: "env_demo",
        trigger_type: "manual",
        trigger_source: "ui",
        request_params: { adapter: "playwright" },
        status: "running",
        summary: {
          playwright: {
            job_name: "pw-regression",
            job_id: "playwright-pw-regression",
            status: "running",
            completion_source: "trigger",
            poll_count: 2,
            browser: "firefox",
            headless: false,
            base_url: "https://sit.example.com",
          },
        },
        completion_source: "trigger",
        started_at: "2026-04-14T00:00:00Z",
        completed_at: null,
      })
      .mockResolvedValueOnce([
        {
          id: "artifact_pw_html",
          execution_id: "exe_playwright_demo",
          artifact_type: "playwright-html-report",
          name: "playwright-report",
          storage_uri: "memory://playwright/report/index.html",
        },
      ])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([]);

    render(
      <MemoryRouter initialEntries={["/executions/exe_playwright_demo"]}>
        <Routes>
          <Route path="/executions/:executionId" element={<ExecutionDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(getMock).toHaveBeenCalledTimes(4));

    const card = screen.getByLabelText("Playwright summary");

    expect(within(card).getByRole("heading", { name: "Playwright" })).toBeTruthy();
    expect(within(card).getByText("pw-regression")).toBeTruthy();
    expect(within(card).getByText("playwright-pw-regression")).toBeTruthy();
    expect(within(card).getByText("firefox")).toBeTruthy();
    expect(within(card).getByText("false")).toBeTruthy();
    expect(within(card).getByText("https://sit.example.com")).toBeTruthy();
    expect(within(card).getByText("playwright-report")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /run execution/i })).toBeNull();
    expect(postMock).not.toHaveBeenCalled();
  });

  it("does not render a playwright panel when summary.playwright is missing", async () => {
    getMock
      .mockResolvedValueOnce({
        id: "exe_non_playwright_demo",
        project_id: "proj_demo",
        suite_id: "suite_demo",
        env_id: "env_demo",
        trigger_type: "manual",
        trigger_source: "ui",
        request_params: { adapter: "jenkins" },
        status: "running",
        summary: {},
        completion_source: "trigger",
        started_at: "2026-04-14T00:00:00Z",
        completed_at: null,
      })
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([]);

    render(
      <MemoryRouter initialEntries={["/executions/exe_non_playwright_demo"]}>
        <Routes>
          <Route path="/executions/:executionId" element={<ExecutionDetailPage />} />
        </Routes>
      </MemoryRouter>,
    );

    await waitFor(() => expect(getMock).toHaveBeenCalledTimes(4));

    expect(screen.queryByLabelText("Playwright summary")).toBeNull();
    expect(screen.queryByRole("button", { name: /run execution/i })).toBeNull();
    expect(postMock).not.toHaveBeenCalled();
  });
});
