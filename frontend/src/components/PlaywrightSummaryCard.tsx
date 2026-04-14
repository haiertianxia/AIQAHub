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
};

export function PlaywrightSummaryCard({ summary, artifacts = [] }: PlaywrightSummaryCardProps) {
  const playwrightArtifacts = listPlaywrightArtifacts(artifacts);

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
      <div style={{ marginTop: 16 }}>
        <div className="metric-label">Artifacts</div>
        {playwrightArtifacts.length > 0 ? (
          <div className="grid" style={{ marginTop: 8 }}>
            {playwrightArtifacts.map((artifact) => (
              <a key={artifact.id} href={artifact.storage_uri}>
                {artifact.name}
              </a>
            ))}
          </div>
        ) : (
          <div>-</div>
        )}
      </div>
    </section>
  );
}
