import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { PlaywrightSummaryCard } from "../components/PlaywrightSummaryCard";
import {
  api,
  type Execution,
  type ExecutionArtifact,
  type ExecutionTask,
  type ExecutionTimelineEntry,
} from "../lib/api";
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

function getSummaryValue(summary: Record<string, unknown>, key: string) {
  const value = summary[key];
  return value === undefined || value === null ? "-" : String(value);
}

function getJenkinsSummary(summary: Record<string, unknown>) {
  const value = summary["jenkins"];
  return typeof value === "object" && value !== null ? (value as Record<string, unknown>) : {};
}

export function ExecutionDetailPage() {
  const { executionId } = useParams();
  const [execution, setExecution] = useState<Execution | null>(null);
  const [artifacts, setArtifacts] = useState<ExecutionArtifact[]>([]);
  const [tasks, setTasks] = useState<ExecutionTask[]>([]);
  const [timeline, setTimeline] = useState<ExecutionTimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const jenkinsSummary = execution ? getJenkinsSummary(execution.summary) : {};
  const playwrightSummary = execution ? getRawPlaywrightSummary(execution.summary.playwright) : null;

  const loadExecution = async (cancelledRef?: { current: boolean }) => {
    setLoading(true);
    setLoadError(null);
    setExecution(null);
    setArtifacts([]);
    setTasks([]);
    setTimeline([]);

    if (!executionId) {
      if (!cancelledRef?.current) {
        setLoading(false);
      }
      return;
    }

    try {
      const [executionData, artifactData, taskData, timelineData] = await Promise.all([
        api.get<Execution>(`/executions/${executionId}`),
        api.get<ExecutionArtifact[]>(`/executions/${executionId}/artifacts`),
        api.get<ExecutionTask[]>(`/executions/${executionId}/tasks`),
        api.get<ExecutionTimelineEntry[]>(`/executions/${executionId}/timeline`),
      ]);
      if (!cancelledRef?.current) {
        setExecution(executionData);
        setArtifacts(artifactData);
        setTasks(taskData);
        setTimeline(timelineData);
      }
    } catch (error) {
      if (!cancelledRef?.current) {
        setLoadError(error instanceof Error ? error.message : "Failed to load execution detail");
      }
    } finally {
      if (!cancelledRef?.current) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    const cancelled = { current: false };

    void loadExecution(cancelled);

    return () => {
      cancelled.current = true;
    };
  }, [executionId]);

  return (
    <Section
      title="执行详情"
      description="查看一次执行的基础信息、请求参数和归一化摘要。"
      action={
        <div className="page-actions">
          <Link className="badge" to="/executions">
            返回执行列表
          </Link>
        </div>
      }
    >
      {loading ? <PageState kind="loading" message="Loading execution detail..." /> : null}
      {
        loadError ? (
          <PageState
            kind="error"
            message={loadError}
            action={
              <button className="primary-button" onClick={() => void loadExecution()} type="button">
                Retry
              </button>
            }
          />
        ) : null
      }
      {!loading && !execution && !loadError ? <PageState kind="empty" message="Execution not found." /> : null}
      {execution ? (
        <>
          <div className="detail-grid">
            <div className="panel">
              <h4>基本信息</h4>
              <div className="kv">
                <div>
                  <span>Execution ID</span>
                  <strong>{execution.id}</strong>
                </div>
                <div>
                  <span>Status</span>
                  <strong>{execution.status}</strong>
                </div>
                <div>
                  <span>Project</span>
                  <strong>{execution.project_id}</strong>
                </div>
                <div>
                  <span>Suite</span>
                  <strong>{execution.suite_id}</strong>
                </div>
                <div>
                  <span>Environment</span>
                  <strong>{execution.env_id}</strong>
                </div>
                <div>
                  <span>Trigger</span>
                  <strong>{execution.trigger_type}</strong>
                </div>
                <div>
                  <span>Completion</span>
                  <strong>{execution.completion_source ?? getSummaryValue(execution.summary, "completion_source")}</strong>
                </div>
                <div>
                  <span>Started At</span>
                  <strong>{execution.started_at ?? getSummaryValue(execution.summary, "started_at")}</strong>
                </div>
                <div>
                  <span>Completed At</span>
                  <strong>{execution.completed_at ?? getSummaryValue(execution.summary, "completed_at")}</strong>
                </div>
                <div>
                  <span>Jenkins Build</span>
                  <strong>{String(jenkinsSummary["build_number"] ?? "-")}</strong>
                </div>
                <div>
                  <span>Jenkins Source</span>
                  <strong>{String(jenkinsSummary["completion_source"] ?? "-")}</strong>
                </div>
                <div>
                  <span>Poll Count</span>
                  <strong>{String(jenkinsSummary["poll_count"] ?? "-")}</strong>
                </div>
              </div>
            </div>
            <div className="panel">
              <h4>请求参数</h4>
              <pre className="code-block">{formatValue(execution.request_params)}</pre>
            </div>
            <div className="panel">
              <h4>执行摘要</h4>
              <pre className="code-block">{formatValue(execution.summary)}</pre>
              <div className="subtle" style={{ marginTop: 8 }}>
                状态 {execution.status} · 来源 {execution.completion_source ?? getSummaryValue(execution.summary, "completion_source")}
              </div>
              {typeof jenkinsSummary["build_url"] === "string" && jenkinsSummary["build_url"] ? (
                <div style={{ marginTop: 8 }}>
                  <a className="badge" href={String(jenkinsSummary["build_url"])} target="_blank" rel="noreferrer">
                    Open Jenkins Build
                  </a>
                </div>
              ) : null}
            </div>
            {playwrightSummary ? <PlaywrightSummaryCard summary={playwrightSummary} artifacts={artifacts} /> : null}
            <div className="panel">
              <h4>时间线</h4>
              <div className="list">
                {timeline.map((item) => (
                  <div key={`${item.stage}-${item.status}`} className="list-item">
                    <div>
                      <div>{item.stage}</div>
                      <div className="subtle">{item.message}</div>
                    </div>
                    <span className="badge">{item.status}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="panel">
              <h4>任务</h4>
              <div className="list">
                {tasks.length > 0 ? (
                  tasks.map((task) => (
                    <div key={task.id} className="list-item">
                      <div>
                        <div>{task.task_name}</div>
                        <div className="subtle">
                          {task.task_key} · {task.error_message ?? "no error"}
                        </div>
                        <pre className="code-block" style={{ marginTop: 8 }}>
                          {formatValue(task.input)}
                        </pre>
                        <pre className="code-block" style={{ marginTop: 8 }}>
                          {formatValue(task.output)}
                        </pre>
                      </div>
                      <span className={`badge ${task.status === "success" ? "ok" : task.status === "failed" ? "fail" : "warn"}`}>
                        {task.status}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="subtle">No execution tasks yet.</div>
                )}
              </div>
            </div>
            <div className="panel">
              <h4>产物</h4>
              <div className="list">
                {artifacts.length > 0 ? (
                  artifacts.map((artifact) => (
                    <div key={artifact.id} className="list-item">
                      <div>
                        <div>{artifact.name}</div>
                        <div className="subtle">
                          {artifact.artifact_type} · {artifact.storage_uri}
                        </div>
                      </div>
                      <span className="badge ok">{artifact.artifact_type}</span>
                    </div>
                  ))
                ) : (
                  <div className="subtle">No artifacts yet.</div>
                )}
              </div>
            </div>
          </div>
        </>
      ) : null}
    </Section>
  );
}
