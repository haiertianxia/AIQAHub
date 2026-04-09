type AiReplayComparisonProps = {
  sourceLabel: string;
  sourceOutput: Record<string, unknown>;
  replayLabel: string;
  replayOutput: Record<string, unknown>;
};

function toComparableText(value: Record<string, unknown>) {
  return JSON.stringify(value, null, 2);
}

function getChangedKeys(source: Record<string, unknown>, replay: Record<string, unknown>) {
  const keys = new Set([...Object.keys(source), ...Object.keys(replay)]);
  return [...keys].filter((key) => JSON.stringify(source[key]) !== JSON.stringify(replay[key]));
}

export function AiReplayComparison({ sourceLabel, sourceOutput, replayLabel, replayOutput }: AiReplayComparisonProps) {
  const changedKeys = getChangedKeys(sourceOutput, replayOutput);

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
