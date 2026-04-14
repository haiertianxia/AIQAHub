import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { PlaywrightSummaryCard } from "../components/PlaywrightSummaryCard";
import { api, type GateResult, type ReportSummary } from "../lib/api";
import { PageState } from "../components/PageState";
import { Section } from "../components/Section";
import { getRawPlaywrightSummary } from "../lib/playwright";

function formatValue(value: unknown) {
  if (value === null || value === undefined) {
    return "-";
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  return JSON.stringify(value, null, 2);
}

export function ReportDetailPage() {
  const { executionId } = useParams();
  const [report, setReport] = useState<ReportSummary | null>(null);
  const [gateResult, setGateResult] = useState<GateResult | null>(null);
  const [expandedArtifacts, setExpandedArtifacts] = useState<Record<string, boolean>>({});
  const [expandedTasks, setExpandedTasks] = useState<Record<string, boolean>>({});
  const [loading, setLoading] = useState(true);
  const [reportError, setReportError] = useState<string | null>(null);
  const [gateError, setGateError] = useState<string | null>(null);
  const playwrightSummary = report ? getRawPlaywrightSummary(report.summary.playwright) : null;

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      if (!executionId) {
        setLoading(false);
        return;
      }

      setReport(null);
      setGateResult(null);
      setReportError(null);
      setGateError(null);
      setExpandedArtifacts({});
      setExpandedTasks({});

      try {
        const [reportOutcome, gateOutcome] = await Promise.allSettled([
          api.get<ReportSummary>(`/reports/${executionId}`),
          api.post<GateResult>("/gates/evaluate", { execution_id: executionId }),
        ]);
        if (!cancelled) {
          if (reportOutcome.status === "fulfilled") {
            setReport(reportOutcome.value);
            setReportError(null);
            setExpandedArtifacts({});
            setExpandedTasks({});
          } else {
            setReportError(reportOutcome.reason instanceof Error ? reportOutcome.reason.message : "Failed to load report.");
          }

          if (gateOutcome.status === "fulfilled") {
            setGateResult(gateOutcome.value);
            setGateError(null);
          } else {
            setGateError(gateOutcome.reason instanceof Error ? gateOutcome.reason.message : "Failed to load gate result.");
          }
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
  }, [executionId]);

  return (
    <Section
      title="报告详情"
      description="查看报告摘要、任务、产物和门禁结果。"
      action={
        <div className="page-actions">
          <Link className="badge" to="/reports">
            返回报告列表
          </Link>
          {executionId ? (
            <Link className="badge" to={`/executions/${executionId}`}>
              查看执行详情
            </Link>
          ) : null}
        </div>
      }
    >
      {loading ? <PageState kind="loading" message="Loading report detail..." /> : null}
      {reportError ? <PageState kind="error" message={reportError} /> : null}
      {!loading && !report && !reportError ? <PageState kind="empty" message="Report not found." /> : null}
      {report ? (
        <div className="detail-grid">
          <div className="panel">
            <h4>Summary</h4>
            <div className="kv">
              <div>
                <span>Execution</span>
                <strong>{report.execution_id}</strong>
              </div>
              <div>
                <span>Status</span>
                <strong>{report.status}</strong>
              </div>
              <div>
                <span>Completion</span>
                <strong>{report.completion_source ?? "-"}</strong>
              </div>
              <div>
                <span>Started</span>
                <strong>{report.started_at ?? "-"}</strong>
              </div>
              <div>
                <span>Completed</span>
                <strong>{report.completed_at ?? "-"}</strong>
              </div>
              <div>
                <span>Task Count</span>
                <strong>{String(report.task_count)}</strong>
              </div>
            </div>
          </div>
          {playwrightSummary ? (
            <PlaywrightSummaryCard
              summary={playwrightSummary}
              artifacts={report.artifacts.map((artifact) => ({
                id: `${String(artifact.name ?? "-")}-${String(artifact.uri ?? "-")}`,
                execution_id: report.execution_id,
                artifact_type: String(artifact.type ?? ""),
                name: String(artifact.name ?? "-"),
                storage_uri: String(artifact.uri ?? ""),
              }))}
              showArtifacts={false}
            />
          ) : null}
          <div className="panel">
            <h4>Gate Result</h4>
            {gateError ? <PageState kind="error" message={gateError} /> : null}
            {gateResult ? (
              <div className="kv">
                <div>
                  <span>Result</span>
                  <strong>{gateResult.result}</strong>
                </div>
                <div>
                  <span>Score</span>
                  <strong>{String(gateResult.score)}</strong>
                </div>
                <div>
                  <span>Failed Tasks</span>
                  <strong>{String(gateResult.failed_tasks)}</strong>
                </div>
                <div>
                  <span>Completion</span>
                  <strong>{gateResult.completion_source ?? "-"}</strong>
                </div>
                <div>
                  <span>Reason</span>
                  <strong>{gateResult.reason}</strong>
                </div>
              </div>
            ) : !gateError ? (
              <PageState kind="empty" message="No gate result yet." />
            ) : null}
          </div>
          <div className="panel">
            <h4>Artifacts</h4>
            {report.artifacts.length === 0 ? <PageState kind="empty" message="No artifacts yet." /> : null}
            <div className="list">
              {report.artifacts.map((artifact) => (
                <div key={`${artifact.name}-${artifact.uri}`} className="list-item" style={{ display: "block" }}>
                  <div>
                    <div className="page-actions" style={{ justifyContent: "space-between" }}>
                      <div>
                        <div>{String(artifact.name ?? "-")}</div>
                        <div className="subtle">{String(artifact.type ?? "-")}</div>
                      </div>
                      <button
                        className="badge"
                        type="button"
                        onClick={() =>
                          setExpandedArtifacts((current) => ({
                            ...current,
                            [`${artifact.name}-${artifact.uri}`]: !current[`${artifact.name}-${artifact.uri}`],
                          }))
                        }
                      >
                        {expandedArtifacts[`${artifact.name}-${artifact.uri}`] ? "Collapse" : "Expand"}
                      </button>
                    </div>
                    {expandedArtifacts[`${artifact.name}-${artifact.uri}`] ? (
                      <pre className="code-block" style={{ marginTop: 8 }}>
                        {formatValue(artifact)}
                      </pre>
                    ) : (
                      <div className="subtle" style={{ marginTop: 6 }}>
                        {String(artifact.uri ?? "-")}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="panel">
            <h4>Tasks</h4>
            {report.tasks.length === 0 ? <PageState kind="empty" message="No tasks yet." /> : null}
            <div className="list">
              {report.tasks.map((task) => (
                <div key={`${task.id ?? task.task_key}`} className="list-item" style={{ display: "block" }}>
                  <div>
                    <div className="page-actions" style={{ justifyContent: "space-between" }}>
                      <div>
                        <div>{String(task.task_name ?? task.task_key ?? "-")}</div>
                        <div className="subtle">
                          {String(task.task_key ?? "-")} · {String(task.status ?? "-")}
                        </div>
                      </div>
                      <button
                        className="badge"
                        type="button"
                        onClick={() =>
                          setExpandedTasks((current) => ({
                            ...current,
                            [String(task.id ?? task.task_key ?? "")]: !current[String(task.id ?? task.task_key ?? "")],
                          }))
                        }
                      >
                        {expandedTasks[String(task.id ?? task.task_key ?? "")] ? "Collapse" : "Expand"}
                      </button>
                    </div>
                    {expandedTasks[String(task.id ?? task.task_key ?? "")] ? (
                      <>
                        <pre className="code-block" style={{ marginTop: 8 }}>
                          {formatValue(task.input)}
                        </pre>
                        <pre className="code-block" style={{ marginTop: 8 }}>
                          {formatValue(task.output)}
                        </pre>
                      </>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div className="panel">
            <h4>Raw</h4>
            <pre className="code-block">{formatValue(report)}</pre>
          </div>
        </div>
      ) : null}
    </Section>
  );
}
