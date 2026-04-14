import type { ExecutionArtifact } from "../lib/api";
import {
  PLAYWRIGHT_SUMMARY_FIELDS,
  getPlaywrightField,
  listPlaywrightArtifacts,
  type RawPlaywrightSummary,
} from "../lib/playwright";

type PlaywrightSummaryCardProps = {
  summary?: RawPlaywrightSummary | null;
  artifacts?: ExecutionArtifact[];
  showArtifacts?: boolean;
};

export function PlaywrightSummaryCard({ summary, artifacts = [], showArtifacts = true }: PlaywrightSummaryCardProps) {
  const playwrightArtifacts = listPlaywrightArtifacts(artifacts);
  const validation = summary && typeof summary.validation === "object" && summary.validation !== null
    ? (summary.validation as Record<string, unknown>)
    : null;
  const validationMessage = typeof validation?.message === "string" && validation.message ? validation.message : null;
  const fallbackFrom = typeof summary?.fallback_from === "string" && summary.fallback_from ? summary.fallback_from : null;
  const fallbackReason =
    typeof summary?.fallback_reason === "string" && summary.fallback_reason ? summary.fallback_reason : null;

  return (
    <section className="panel soft" aria-label="Playwright summary">
      <h3>Playwright</h3>
      <div className="grid cols-2">
        {PLAYWRIGHT_SUMMARY_FIELDS.map(([field, label]) => (
          <div key={field}>
            <div className="metric-label">{label}</div>
            <div>{getPlaywrightField(summary, field)}</div>
          </div>
        ))}
      </div>
      {validationMessage ? (
        <div style={{ marginTop: 16 }}>
          <div className="metric-label">Validation</div>
          <div>{validationMessage}</div>
        </div>
      ) : null}
      {fallbackFrom ? (
        <div style={{ marginTop: 16 }}>
          <div className="metric-label">Fallback</div>
          <div>
            Fallback from {fallbackFrom}
            {fallbackReason ? `: ${fallbackReason}` : ""}
          </div>
        </div>
      ) : null}
      {showArtifacts ? (
        <div style={{ marginTop: 16 }}>
          <div className="metric-label">Artifacts</div>
          {playwrightArtifacts.length > 0 ? (
            <div className="grid" style={{ marginTop: 8 }}>
              {playwrightArtifacts.map((artifact) => (
                <div key={artifact.id}>{artifact.name}</div>
              ))}
            </div>
          ) : (
            <div>-</div>
          )}
        </div>
      ) : null}
    </section>
  );
}
