type AiReplayComparisonProps = {
  sourceLabel: string;
  sourceOutput: Record<string, unknown>;
  replayLabel: string;
  replayOutput: Record<string, unknown>;
};

function toComparableText(value: Record<string, unknown>) {
  return JSON.stringify(value, null, 2);
}

function formatComparableValue(value: unknown) {
  if (value === null || value === undefined) {
    return "-";
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  return JSON.stringify(value, null, 2);
}

function getChangedKeys(source: Record<string, unknown>, replay: Record<string, unknown>) {
  const keys = new Set([...Object.keys(source), ...Object.keys(replay)]);
  return [...keys].filter((key) => JSON.stringify(source[key]) !== JSON.stringify(replay[key]));
}

export function AiReplayComparison({ sourceLabel, sourceOutput, replayLabel, replayOutput }: AiReplayComparisonProps) {
  const changedKeys = getChangedKeys(sourceOutput, replayOutput);
  const keyRows = [...new Set([...Object.keys(sourceOutput), ...Object.keys(replayOutput)])].map((key) => ({
    key,
    changed: JSON.stringify(sourceOutput[key]) !== JSON.stringify(replayOutput[key]),
    sourceValue: sourceOutput[key],
    replayValue: replayOutput[key],
  }));

  return (
    <div className="panel soft" style={{ marginTop: 12 }}>
      <h4>Replay Compare</h4>
      <div className="subtle" style={{ marginBottom: 12 }}>
        Changes{" "}
        {changedKeys.length === 0 ? (
          " none"
        ) : (
          <span className="page-actions" style={{ display: "inline-flex", gap: 8, marginLeft: 8, flexWrap: "wrap" }}>
            {changedKeys.map((key) => (
              <span key={key} className="badge warn">
                {key}
              </span>
            ))}
          </span>
        )}
      </div>
      <div className="panel" style={{ marginBottom: 12, padding: 12 }}>
        <h5 style={{ marginBottom: 8 }}>Field Diff</h5>
        <div className="list">
          {keyRows.length === 0 ? <div className="subtle">No comparable fields.</div> : null}
          {keyRows.map((row) => (
            <div
              key={row.key}
              className="list-item"
              style={{
                alignItems: "start",
                background: row.changed ? "rgba(91, 231, 196, 0.08)" : undefined,
              }}
            >
              <div style={{ flex: 1 }}>
                <div className="page-actions" style={{ justifyContent: "space-between" }}>
                  <strong>{row.key}</strong>
                  <span className={`badge ${row.changed ? "warn" : "ok"}`}>{row.changed ? "changed" : "same"}</span>
                </div>
                <div className="grid cols-2" style={{ marginTop: 8 }}>
                  <div>
                    <div className="subtle" style={{ marginBottom: 4 }}>
                      {sourceLabel}
                    </div>
                    <pre className="code-block" style={{ margin: 0 }}>
                      {formatComparableValue(row.sourceValue)}
                    </pre>
                  </div>
                  <div>
                    <div className="subtle" style={{ marginBottom: 4 }}>
                      {replayLabel}
                    </div>
                    <pre className="code-block" style={{ margin: 0 }}>
                      {formatComparableValue(row.replayValue)}
                    </pre>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="grid cols-2">
        <div>
          <div className="subtle" style={{ marginBottom: 8 }}>
            {sourceLabel}
          </div>
          <pre className="code-block">{toComparableText(sourceOutput)}</pre>
        </div>
        <div>
          <div className="subtle" style={{ marginBottom: 8 }}>
            {replayLabel}
          </div>
          <pre className="code-block">{toComparableText(replayOutput)}</pre>
        </div>
      </div>
    </div>
  );
}
