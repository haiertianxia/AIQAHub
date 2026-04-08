import { useState, type FormEvent } from "react";

import { api, type AiResult } from "../lib/api";
import { Section } from "../components/Section";

export function AiPage() {
  const [inputText, setInputText] = useState("登录失败回归");
  const [confidence, setConfidence] = useState<AiResult | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLoading(true);
    try {
      const result = await api.post<AiResult>("/ai/analyze", {
        input_text: inputText,
        context: { source: "ai-page" },
      });
      setConfidence(result);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Section title="AI" description="需求摘要、测试建议、风险分析和根因初判">
      <form className="inline-form" onSubmit={submit}>
        <div className="field-grid">
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
    </Section>
  );
}
