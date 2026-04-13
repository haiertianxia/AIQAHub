import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { api, type AiHistoryItem, type AiResult } from "../lib/api";
import { AiReplayComparison } from "../components/AiReplayComparison";
import { Highlight } from "../components/Highlight";
import { PaginationControls } from "../components/PaginationControls";
import { QueryToolbar } from "../components/QueryToolbar";
import { PageState } from "../components/PageState";
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
  const [executionFilter, setExecutionFilter] = useState("");
  const [modelFilter, setModelFilter] = useState("");
  const [insightTypeFilter, setInsightTypeFilter] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [selected, setSelected] = useState<AiHistoryItem | null>(null);
  const [result, setResult] = useState<AiResult | null>(null);
  const [replaySource, setReplaySource] = useState<AiHistoryItem | null>(null);
  const [loading, setLoading] = useState(true);
  const [replaying, setReplaying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await loadHistory({ page: 1 });
        if (!cancelled) {
          setHistory(data);
          setSelected((current) => data.find((item) => item.id === current?.id) ?? data[0] ?? null);
          setError(null);
        }
      } catch (cause) {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Failed to load AI history.");
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

  const loadHistory = async (overrides?: {
    page?: number;
    search?: string;
    execution_id?: string;
    model_name?: string;
    insight_type?: string;
  }) => {
    const params = new URLSearchParams();
    params.set("page", String(overrides?.page ?? page));
    params.set("page_size", String(pageSize));
    params.set("sort", "-id");
    const effectiveSearch = overrides?.search ?? search;
    const effectiveExecutionId = overrides?.execution_id ?? executionFilter;
    const effectiveModelName = overrides?.model_name ?? modelFilter;
    const effectiveInsightType = overrides?.insight_type ?? insightTypeFilter;
    if (effectiveSearch.trim()) {
      params.set("search", effectiveSearch.trim());
    }
    if (effectiveExecutionId.trim()) {
      params.set("execution_id", effectiveExecutionId.trim());
    }
    if (effectiveModelName.trim()) {
      params.set("model_name", effectiveModelName.trim());
    }
    if (effectiveInsightType.trim()) {
      params.set("insight_type", effectiveInsightType.trim());
    }
    return api.get<AiHistoryItem[]>(`/ai/history?${params.toString()}`);
  };

  const replay = async (item: AiHistoryItem) => {
    setReplaying(true);
    setError(null);
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
      setReplaySource(item);
      const refreshed = await loadHistory();
      setHistory(refreshed);
      setSelected(refreshed.find((entry) => entry.id === item.id) ?? refreshed[0] ?? item);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Replay failed.");
    } finally {
      setReplaying(false);
    }
  };

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const refreshed = await loadHistory({ page: 1 });
      setHistory(refreshed);
      setSelected(refreshed[0] ?? null);
      setPage(1);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to search AI history.");
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = async () => {
    setSearch("");
    setExecutionFilter("");
    setModelFilter("");
    setInsightTypeFilter("");
    setLoading(true);
    setError(null);
    try {
      const refreshed = await loadHistory({
        page: 1,
        search: "",
        execution_id: "",
        model_name: "",
        insight_type: "",
      });
      setHistory(refreshed);
      setSelected(refreshed[0] ?? null);
      setPage(1);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to clear AI filters.");
    } finally {
      setLoading(false);
    }
  };

  const onSelectItem = (item: AiHistoryItem) => {
    setSelected(item);
  };

  const goToPage = async (nextPage: number) => {
    setLoading(true);
    setError(null);
    try {
      const refreshed = await loadHistory({ page: nextPage });
      setHistory(refreshed);
      setSelected(refreshed[0] ?? null);
      setPage(nextPage);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to change AI history page.");
    } finally {
      setLoading(false);
    }
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
      <QueryToolbar onSubmit={onSubmit}>
          <div className="field">
            <label>Search</label>
            <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="execution or prompt text" />
          </div>
          <div className="field">
            <label>Execution ID</label>
            <input value={executionFilter} onChange={(event) => setExecutionFilter(event.target.value)} placeholder="exe_123" />
          </div>
          <div className="field">
            <label>Model</label>
            <input value={modelFilter} onChange={(event) => setModelFilter(event.target.value)} placeholder="mock-llm" />
          </div>
          <div className="field">
            <label>Insight Type</label>
            <input value={insightTypeFilter} onChange={(event) => setInsightTypeFilter(event.target.value)} placeholder="analysis" />
          </div>
          <div className="page-actions" style={{ alignItems: "end" }}>
            <button className="primary-button" type="submit">
              Search
            </button>
            <button className="badge" type="button" onClick={() => void clearFilters()}>
              Clear
            </button>
          </div>
      </QueryToolbar>

      {loading ? <PageState kind="loading" message="Loading AI history..." /> : null}
      {error ? <PageState kind="error" message={error} /> : null}
      <div className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel">
          <h4>History</h4>
          <div className="list">
            {history.length === 0 && !loading && !error ? <PageState kind="empty" message="No matching AI history." /> : null}
            {history.map((item) => (
              <div
                key={item.id}
                className={`list-item ${selected?.id === item.id ? "active-row" : ""}`}
                role="button"
                tabIndex={0}
                onClick={() => onSelectItem(item)}
                onKeyDown={() => onSelectItem(item)}
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
          <PaginationControls page={page} pageSize={pageSize} itemCount={history.length} onPrevious={() => void goToPage(page - 1)} onNext={() => void goToPage(page + 1)} />
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
            <AiReplayComparison
              sourceLabel={`Source ${replaySource?.id ?? selected?.id ?? "-"}`}
              sourceOutput={(replaySource?.output_json ?? selected?.output_json ?? {}) as Record<string, unknown>}
              replayLabel={`Replay ${result.model}`}
              replayOutput={result.result}
            />
          ) : null}
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
