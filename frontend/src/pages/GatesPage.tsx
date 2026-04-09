import { useEffect, useState, type FormEvent } from "react";

import { api, type Execution, type GateResult, type GateRule } from "../lib/api";
import { Section } from "../components/Section";

function getMinSuccessRate(rule: GateRule) {
  const value = rule.config["min_success_rate"];
  return typeof value === "number" ? value : 95;
}

function getMinTaskCount(rule: GateRule) {
  const value = rule.config["min_task_count"];
  return typeof value === "number" ? value : 3;
}

function getExecutionSuccessRate(execution: Execution) {
  const value = execution.summary["success_rate"];
  return typeof value === "number" ? value : 0;
}

export function GatesPage() {
  const [rules, setRules] = useState<GateRule[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [evaluation, setEvaluation] = useState<GateResult | null>(null);
  const [projectId, setProjectId] = useState("");
  const [name, setName] = useState("");
  const [ruleType, setRuleType] = useState("success_rate");
  const [minSuccessRate, setMinSuccessRate] = useState("95");
  const [minTaskCount, setMinTaskCount] = useState("3");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const [ruleData, executionData] = await Promise.all([
        api.get<GateRule[]>("/gates/rules"),
        api.get<Execution[]>("/executions"),
      ]);

      if (!cancelled) {
        setRules(ruleData);
        setExecutions(executionData);
        setProjectId(executionData[0]?.project_id ?? "");
        setLoading(false);
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  const createRule = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);

    try {
      const created = await api.post<GateRule>("/gates/rules", {
        project_id: projectId,
        name,
        rule_type: ruleType,
        enabled: true,
        config: { min_success_rate: Number(minSuccessRate), min_task_count: Number(minTaskCount) },
      });
      setRules((current) => [created, ...current]);
      setName("");
    } finally {
      setSaving(false);
    }
  };

  const evaluateGate = async (executionId: string) => {
    const result = await api.post<GateResult>("/gates/evaluate", { execution_id: executionId });
    setEvaluation(result);
  };

  return (
    <Section
      title="门禁"
      description="规则配置与评估结果"
      action={
        <form className="inline-form" onSubmit={createRule}>
          <div className="page-actions">
            <div className="field">
              <label>Project</label>
              <input value={projectId} onChange={(event) => setProjectId(event.target.value)} placeholder="proj_demo" />
            </div>
            <div className="field">
              <label>Name</label>
              <input value={name} onChange={(event) => setName(event.target.value)} placeholder="成功率门禁" />
            </div>
            <div className="field">
              <label>Rule Type</label>
              <select value={ruleType} onChange={(event) => setRuleType(event.target.value)}>
                <option value="success_rate">success_rate</option>
              </select>
            </div>
            <div className="field">
              <label>Min Success Rate</label>
              <input value={minSuccessRate} onChange={(event) => setMinSuccessRate(event.target.value)} placeholder="95" />
            </div>
            <div className="field">
              <label>Min Task Count</label>
              <input value={minTaskCount} onChange={(event) => setMinTaskCount(event.target.value)} placeholder="3" />
            </div>
            <button className="primary-button" type="submit" disabled={saving || !projectId || !name}>
              {saving ? "Creating..." : "Create Rule"}
            </button>
          </div>
        </form>
      }
    >
      {loading ? <div className="subtle">Loading gates...</div> : null}
      <div className="list">
        {rules.map((rule) => (
          <div key={rule.id} className="list-item">
            <div>
              <div>{rule.name}</div>
              <div className="subtle">
                {rule.rule_type} · {rule.project_id} · success {String(getMinSuccessRate(rule))}% · tasks{" "}
                {String(getMinTaskCount(rule))}
              </div>
            </div>
            <span className={`badge ${rule.enabled ? "ok" : "warn"}`}>{rule.enabled ? "ENABLED" : "DISABLED"}</span>
          </div>
        ))}
      </div>

      <div className="panel soft" style={{ marginTop: 16 }}>
        <h4>快速评估</h4>
        <div className="list">
          {executions.map((execution) => (
            <div key={execution.id} className="list-item">
              <div>
                <div>{execution.id}</div>
                <div className="subtle">
                  {execution.status} · {String(getExecutionSuccessRate(execution))}%
                </div>
              </div>
              <button className="primary-button" type="button" onClick={() => evaluateGate(execution.id)}>
                Evaluate
              </button>
            </div>
          ))}
        </div>
        {evaluation ? (
          <div className="list-item" style={{ marginTop: 12 }}>
            <div>
              <div>{evaluation.execution_id}</div>
              <div className="subtle">{evaluation.reason}</div>
              <div className="subtle">
                tasks {evaluation.task_count} / failed {evaluation.failed_tasks} / threshold {evaluation.task_threshold}
              </div>
            </div>
            <span className={`badge ${evaluation.result === "PASS" ? "ok" : evaluation.result === "FAIL" ? "fail" : "warn"}`}>
              {evaluation.result}
            </span>
          </div>
        ) : null}
      </div>
    </Section>
  );
}
