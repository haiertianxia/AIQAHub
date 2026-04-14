import type { ExecutionArtifact, PlaywrightSummary } from "./api";

export const PLAYWRIGHT_SUMMARY_FIELDS = [
  ["job_name", "Job Name"],
  ["job_id", "Job ID"],
  ["status", "Status"],
  ["completion_source", "Completion Source"],
  ["poll_count", "Poll Count"],
  ["browser", "Browser"],
  ["headless", "Headless"],
  ["base_url", "Base URL"],
] as const;

export type PlaywrightSummaryField = (typeof PLAYWRIGHT_SUMMARY_FIELDS)[number][0];
export type RawPlaywrightSummary = PlaywrightSummary;

export function isRawPlaywrightSummary(value: unknown): value is RawPlaywrightSummary {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

export function getRawPlaywrightSummary(value: unknown): RawPlaywrightSummary | null {
  return isRawPlaywrightSummary(value) ? value : null;
}

export function getPlaywrightField(summary: RawPlaywrightSummary | null | undefined, field: PlaywrightSummaryField): string {
  if (!summary) {
    return "-";
  }
  const value = summary[field];
  if (value === null || value === undefined) {
    return "-";
  }
  if (typeof value === "string") {
    return value || "-";
  }
  if (typeof value === "boolean" || typeof value === "number") {
    return String(value);
  }
  return JSON.stringify(value);
}

export function listPlaywrightArtifacts(artifacts: ExecutionArtifact[] | null | undefined): ExecutionArtifact[] {
  return (artifacts ?? []).filter(
    (artifact) => artifact.artifact_type.startsWith("playwright-") || artifact.name.toLowerCase().includes("playwright"),
  );
}
