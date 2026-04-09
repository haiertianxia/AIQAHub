import { useEffect, useState, type FormEvent } from "react";

import { api, type AiHistoryItem, type AiResult, type Execution } from "../lib/api";
import { Section } from "../components/Section";

export function AiPage() {
  const [inputText, setInputText] = useState("登录失败回归");
  const [confidence, setConfidence] = useState<AiResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<AiHistoryItem[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [contextExecutionId, setContextExecutionId] = useState("");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const [historyData, executionData] = await Promise.all([
        api.get<AiHistoryItem[]>("/ai/history?limit=10"),
        api.get<Execution[]>("/executions?status=success"),
      ]);
      if (!cancelled) {
        setHistory(historyData);
        setExecutions(executionData);
        setContextExecutionId((current) => current || executionData[0]?.id || "");
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    try {
      const result = await api.post<AiResult>("/ai/analyze", {
        input_text: inputText,
        context: { source: "ai-page", execution_id: contextExecutionId },
      });
      setConfidence(result);
      const [historyData] = await Promise.all([api.get<AiHistoryItem[]>("/ai/history?limit=10")]);
      setHistory(historyData);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Section title="AI" description="需求摘要、测试建议、风险分析和根因初判">
      <form className="inline-form" onSubmit={submit}>
        <div className="field-grid">
          <div className="field" style={{ gridColumn: "1 / -1" }}>
            <label>Context Execution</label>
            <select value={contextExecutionId} onChange={(event) => setContextExecutionId(event.target.value)}>
              {executions.map((execution) => (
                <option key={execution.id} value={execution.id}>
                  {execution.id} · {execution.status}
                </option>
              ))}
            </select>
          </div>
          <div className="field" style={{ gridColumn: "1 / -1" }}>
            <label>Input Text</label>
            <textarea value={inputText} onChange={(event) => setInputText(event.target.value)} />
          </div>
        </div>
        <button className="primary-button" type="submit" disabled={loading}>
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </form>

      {confidence ? (
        <div className="panel soft" style={{ marginTop: 16 }}>
          <h4>AI Result</h4>
          <div className="subtle">
            Model {confidence.model} · Confidence {confidence.confidence}
          </div>
          <pre className="code-block" style={{ marginTop: 12 }}>
            {JSON.stringify(confidence.result, null, 2)}
          </pre>
        </div>
      ) : null}

      <div className="panel" style={{ marginTop: 16 }}>
        <h4>History</h4>
        <div className="list">
          {history.length === 0 ? <div className="subtle">No AI history yet.</div> : null}
          {history.map((item) => (
            <div key={item.id} className="list-item">
              <div>
                <div>{item.execution_id}</div>
                <div className="subtle">
                  {item.insight_type} · {item.model_name} · {item.prompt_version} · {item.confidence}
                </div>
                <pre className="code-block" style={{ marginTop: 8 }}>
                  {JSON.stringify(item.output_json, null, 2)}
                </pre>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}
