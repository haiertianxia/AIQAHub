import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PlaywrightSummaryCard } from "./PlaywrightSummaryCard";

describe("PlaywrightSummaryCard", () => {
  it("renders raw playwright values without remapping", () => {
    render(
      <PlaywrightSummaryCard
        summary={{
          job_name: "pw-regression",
          job_id: "playwright-pw-regression",
          status: "running",
          completion_source: "trigger",
          poll_count: 2,
          browser: "firefox",
          headless: false,
          base_url: "https://sit.example.com",
        }}
        artifacts={[
          {
            id: "art_pw_html",
            execution_id: "exe_demo",
            artifact_type: "playwright-html-report",
            name: "html-report",
            storage_uri: "memory://playwright/demo/html-report/index.html",
          },
        ]}
      />,
    );

    expect(screen.getByText("Playwright")).toBeTruthy();
    expect(screen.getByText("pw-regression")).toBeTruthy();
    expect(screen.getByText("playwright-pw-regression")).toBeTruthy();
    expect(screen.getByText("running")).toBeTruthy();
    expect(screen.getByText("trigger")).toBeTruthy();
    expect(screen.getByText("2")).toBeTruthy();
    expect(screen.getByText("firefox")).toBeTruthy();
    expect(screen.getByText("false")).toBeTruthy();
    expect(screen.getByText("https://sit.example.com")).toBeTruthy();
    expect(screen.getByText("html-report")).toBeTruthy();
  });

  it("renders missing playwright fields as dash", () => {
    render(<PlaywrightSummaryCard summary={{ job_name: "pw-partial" }} artifacts={[]} />);

    expect(screen.getByText("pw-partial")).toBeTruthy();
    expect(screen.getAllByText("-").length).toBeGreaterThan(1);
  });
});
