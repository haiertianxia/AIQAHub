import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { api, type AiHistoryItem, type AiResult } from "../lib/api";
import { Highlight } from "../components/Highlight";
import { Section } from "../components/Section";

function getInputText(item: AiHistoryItem) {
  const value = item.input_json["input_text"];
  return typeof value === "string" ? value : "";
}

function getContextExecutionId(item: AiHistoryItem) {
  const context = item.input_json["context"];
  if (typeof context !== "object" || context === null) {
    return "";
  }
  const executionId = (context as Record<string, unknown>)["execution_id"];
  return typeof executionId === "string" ? executionId : "";
}

export function AiHistoryPage() {
  const [history, setHistory] = useState<AiHistoryItem[]>([]);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<AiHistoryItem | null>(null);
  const [result, setResult] = useState<AiResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [replaying, setReplaying] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await api.get<AiHistoryItem[]>("/ai/history?limit=50");
        if (!cancelled) {
          setHistory(data);
          setSelected(data[0] ?? null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!search) {
      return history;
    }
    const lowered = search.toLowerCase();
    return history.filter((item) => {
      const inputText = getInputText(item).toLowerCase();
      const outputText = JSON.stringify(item.output_json).toLowerCase();
      return (
        item.execution_id.toLowerCase().includes(lowered) ||
        item.model_name.toLowerCase().includes(lowered) ||
        item.insight_type.toLowerCase().includes(lowered) ||
        inputText.includes(lowered) ||
        outputText.includes(lowered)
      );
    });
  }, [history, search]);

  const replay = async (item: AiHistoryItem) => {
    setReplaying(true);
    try {
      const resultData = await api.post<AiResult>("/ai/analyze", {
        input_text: getInputText(item) || "replayed analysis",
        context: {
          ...((item.input_json["context"] as Record<string, unknown>) || {}),
          replay_of: item.id,
          execution_id: getContextExecutionId(item),
        },
      });
      setResult(resultData);
      const refreshed = await api.get<AiHistoryItem[]>("/ai/history?limit=50");
      setHistory(refreshed);
      setSelected(refreshed[0] ?? item);
    } finally {
      setReplaying(false);
    }
  };

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
  };

  return (
    <Section
      title="AI 历史"
      description="查看历史分析、回放上下文并重跑 AI 分析。"
      action={
        <div className="page-actions">
          <Link className="badge" to="/ai">
            返回 AI 分析
          </Link>
        </div>
      }
    >
      <form className="inline-form" onSubmit={onSubmit}>
        <div className="page-actions">
          <div className="field">
            <label>Search</label>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="execution or prompt text" />
          </div>
        </div>
      </form>

      {loading ? <div className="subtle">Loading AI history...</div> : null}
      <div className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel">
          <h4>History</h4>
          <div className="list">
            {filtered.length === 0 && !loading ? <div className="subtle">No matching AI history.</div> : null}
            {filtered.map((item) => (
              <div
                key={item.id}
                className={`list-item ${selected?.id === item.id ? "active-row" : ""}`}
                role="button"
                tabIndex={0}
                onClick={() => setSelected(item)}
                onKeyDown={() => setSelected(item)}
              >
                <div>
                  <div>
                    <Highlight text={item.execution_id} query={search} />
                  </div>
                  <div className="subtle">
                    <Highlight text={`${item.insight_type} · ${item.model_name} · ${item.prompt_version}`} query={search} />
                  </div>
                  <div className="subtle">Context {getContextExecutionId(item) || "-"}</div>
                </div>
                <button className="badge" type="button" onClick={() => replay(item)} disabled={replaying}>
                  Replay
                </button>
              </div>
            ))}
          </div>
        </div>
        <div className="panel">
          <h4>Detail</h4>
          {selected ? (
            <>
              <div className="subtle">
                {selected.model_name} · {selected.prompt_version} · {selected.confidence}
              </div>
              <pre className="code-block" style={{ marginTop: 12 }}>
                {JSON.stringify(selected.input_json, null, 2)}
              </pre>
              <pre className="code-block" style={{ marginTop: 12 }}>
                {JSON.stringify(selected.output_json, null, 2)}
              </pre>
            </>
          ) : (
            <div className="subtle">Select a history item.</div>
          )}
          {result ? (
            <div className="panel soft" style={{ marginTop: 12 }}>
              <h4>Replay Result</h4>
              <div className="subtle">
                Model {result.model} · Confidence {result.confidence}
              </div>
              <pre className="code-block" style={{ marginTop: 12 }}>
                {JSON.stringify(result.result, null, 2)}
              </pre>
            </div>
          ) : null}
        </div>
      </div>
    </Section>
  );
}
