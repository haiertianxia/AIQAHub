import { useEffect, useMemo, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { api, type Environment, type Execution, type Project, type TestSuite } from "../lib/api";
import { Section } from "../components/Section";

function statusTone(status: string) {
  if (status === "success") {
    return "ok";
  }
  if (status === "failed") {
    return "fail";
  }
  return "warn";
}

export function ExecutionsPage() {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [suites, setSuites] = useState<TestSuite[]>([]);
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [projectId, setProjectId] = useState("");
  const [suiteId, setSuiteId] = useState("");
  const [envId, setEnvId] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [triggerType, setTriggerType] = useState("manual");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const query = new URLSearchParams();
        if (statusFilter) {
          query.set("status", statusFilter);
        }
        query.set("page", String(page));
        query.set("page_size", "10");
        const [executionData, projectData, suiteData, envData] = await Promise.all([
          api.get<Execution[]>(`/executions?${query.toString()}`),
          api.get<Project[]>("/projects"),
          api.get<TestSuite[]>("/suites"),
          api.get<Environment[]>("/environments"),
        ]);

        if (!cancelled) {
          setExecutions(executionData);
          setProjects(projectData);
          setSuites(suiteData);
          setEnvironments(envData);
          setProjectId((current) => current || projectData[0]?.id || "");
          setSuiteId((current) => current || suiteData[0]?.id || "");
          setEnvId((current) => current || envData[0]?.id || "");
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
  }, [page, statusFilter]);

  const filteredSuites = useMemo(
    () => suites.filter((suite) => suite.project_id === projectId),
    [projectId, suites],
  );
  const filteredEnvironments = useMemo(
    () => environments.filter((environment) => environment.project_id === projectId),
    [environments, projectId],
  );

  useEffect(() => {
    if (filteredSuites.length > 0 && !filteredSuites.some((suite) => suite.id === suiteId)) {
      setSuiteId(filteredSuites[0].id);
    }
  }, [filteredSuites, suiteId]);

  useEffect(() => {
    if (filteredEnvironments.length > 0 && !filteredEnvironments.some((env) => env.id === envId)) {
      setEnvId(filteredEnvironments[0].id);
    }
  }, [envId, filteredEnvironments]);

  const createExecution = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const created = await api.post<Execution>("/executions", {
        project_id: projectId,
        suite_id: suiteId,
        env_id: envId,
        trigger_type: triggerType,
        request_params: {},
      });
      setExecutions((current) => [created, ...current]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create execution");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Section
      title="执行"
      description="触发、排队、执行、取消和重试"
      action={
        <form className="inline-form" onSubmit={createExecution}>
          <div className="page-actions">
            <div className="field">
              <label>Project</label>
              <select value={projectId} onChange={(event) => setProjectId(event.target.value)}>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Suite</label>
              <select value={suiteId} onChange={(event) => setSuiteId(event.target.value)}>
                {filteredSuites.map((suite) => (
                  <option key={suite.id} value={suite.id}>
                    {suite.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Environment</label>
              <select value={envId} onChange={(event) => setEnvId(event.target.value)}>
                {filteredEnvironments.map((environment) => (
                  <option key={environment.id} value={environment.id}>
                    {environment.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Trigger</label>
              <select value={triggerType} onChange={(event) => setTriggerType(event.target.value)}>
                <option value="manual">manual</option>
                <option value="scheduled">scheduled</option>
                <option value="webhook">webhook</option>
              </select>
            </div>
            <div className="field">
              <label>Status</label>
              <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
                <option value="">all</option>
                <option value="queued">queued</option>
                <option value="running">running</option>
                <option value="success">success</option>
                <option value="failed">failed</option>
                <option value="timeout">timeout</option>
              </select>
            </div>
            <button
              className="primary-button"
              type="submit"
              disabled={saving || !projectId || !suiteId || !envId}
            >
              {saving ? "Creating..." : "Create Execution"}
            </button>
          </div>
          {error ? <div className="login-error">{error}</div> : null}
        </form>
      }
    >
      {loading ? <div className="subtle">Loading executions...</div> : null}
      <div className="list">
        {executions.map((execution) => (
          <Link key={execution.id} className="list-item" to={`/executions/${execution.id}`}>
            <div>
              <div>{execution.id}</div>
              <div className="subtle">
                {execution.status} · {execution.suite_id} · {execution.env_id}
              </div>
              <div className="subtle">
                {execution.completion_source ?? "-"} · {execution.started_at ?? "-"} · {execution.completed_at ?? "-"}
              </div>
            </div>
            <span className={`badge ${statusTone(execution.status)}`}>{execution.status}</span>
          </Link>
        ))}
      </div>
      <div className="page-actions" style={{ marginTop: 16 }}>
        <button className="badge" type="button" disabled={page <= 1} onClick={() => setPage((current) => Math.max(current - 1, 1))}>
          Previous
        </button>
        <span className="subtle">Page {page}</span>
        <button className="badge" type="button" onClick={() => setPage((current) => current + 1)}>
          Next
        </button>
      </div>
    </Section>
  );
}
