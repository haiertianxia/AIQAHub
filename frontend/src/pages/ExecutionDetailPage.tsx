import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  api,
  type Execution,
  type ExecutionArtifact,
  type ExecutionDispatchResult,
  type ExecutionTask,
  type ExecutionTimelineEntry,
} from "../lib/api";
import { Section } from "../components/Section";

function formatValue(value: unknown) {
  if (value === null || value === undefined) {
    return "-";
  }

  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  return JSON.stringify(value, null, 2);
}

export function ExecutionDetailPage() {
  const { executionId } = useParams();
  const [execution, setExecution] = useState<Execution | null>(null);
  const [artifacts, setArtifacts] = useState<ExecutionArtifact[]>([]);
  const [tasks, setTasks] = useState<ExecutionTask[]>([]);
  const [timeline, setTimeline] = useState<ExecutionTimelineEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [dispatching, setDispatching] = useState(false);
  const [dispatchResult, setDispatchResult] = useState<ExecutionDispatchResult | null>(null);
  const [dispatchError, setDispatchError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    setLoading(true);
    setExecution(null);
    setArtifacts([]);
    setTasks([]);
    setTimeline([]);
    setDispatchResult(null);
    setDispatchError(null);

    const load = async () => {
      if (!executionId) {
        setLoading(false);
        return;
      }

      try {
        const [executionData, artifactData, taskData, timelineData] = await Promise.all([
          api.get<Execution>(`/executions/${executionId}`),
          api.get<ExecutionArtifact[]>(`/executions/${executionId}/artifacts`),
          api.get<ExecutionTask[]>(`/executions/${executionId}/tasks`),
          api.get<ExecutionTimelineEntry[]>(`/executions/${executionId}/timeline`),
        ]);
        if (!cancelled) {
          setExecution(executionData);
          setArtifacts(artifactData);
          setTasks(taskData);
          setTimeline(timelineData);
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

  const runExecution = async () => {
    if (!executionId) {
      return;
    }

    setDispatching(true);
    setDispatchError(null);
    try {
      const result = await api.post<ExecutionDispatchResult>(`/executions/${executionId}/run`);
      setDispatchResult(result);

      const [executionData, artifactData, taskData, timelineData] = await Promise.all([
        api.get<Execution>(`/executions/${executionId}`),
        api.get<ExecutionArtifact[]>(`/executions/${executionId}/artifacts`),
        api.get<ExecutionTask[]>(`/executions/${executionId}/tasks`),
        api.get<ExecutionTimelineEntry[]>(`/executions/${executionId}/timeline`),
      ]);
      setExecution(executionData);
      setArtifacts(artifactData);
      setTasks(taskData);
      setTimeline(timelineData);
    } catch (error) {
      setDispatchError(error instanceof Error ? error.message : "Failed to run execution");
    } finally {
      setDispatching(false);
    }
  };

  return (
    <Section
      title="执行详情"
      description="查看一次执行的基础信息、请求参数和归一化摘要。"
      action={
        <div className="page-actions">
          <button
            className="primary-button"
            type="button"
            onClick={runExecution}
            disabled={dispatching || execution?.status !== "queued"}
          >
            {dispatching ? "Running..." : "Run Execution"}
          </button>
          <Link className="badge" to="/executions">
            返回执行列表
          </Link>
        </div>
      }
    >
      {dispatchResult ? (
        <div className="panel soft" style={{ marginBottom: 16 }}>
          <h4>Dispatch Result</h4>
          <div className="subtle">
            Task {dispatchResult.task_id} · Status {dispatchResult.status}
          </div>
        </div>
      ) : null}
      {dispatchError ? <div className="login-error">{dispatchError}</div> : null}
      {loading ? <div className="subtle">Loading execution detail...</div> : null}
      {!loading && !execution ? <div className="subtle">Execution not found.</div> : null}
      {execution ? (
        <>
          {execution.status !== "queued" ? (
            <div className="subtle" style={{ marginBottom: 12 }}>
              Only queued executions can be dispatched from this view.
            </div>
          ) : null}
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
            </div>
          </div>
          <div className="panel">
            <h4>请求参数</h4>
            <pre className="code-block">{formatValue(execution.request_params)}</pre>
          </div>
          <div className="panel">
            <h4>执行摘要</h4>
            <pre className="code-block">{formatValue(execution.summary)}</pre>
          </div>
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
