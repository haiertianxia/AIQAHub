import { useEffect, useMemo, useState, type FormEvent } from "react";

import { api, type Environment, type Project } from "../lib/api";
import { PageState } from "../components/PageState";
import { Section } from "../components/Section";

export function EnvironmentsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [environments, setEnvironments] = useState<Environment[]>([]);
  const [projectId, setProjectId] = useState("");
  const [name, setName] = useState("");
  const [envType, setEnvType] = useState("sit");
  const [baseUrl, setBaseUrl] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const filteredEnvironments = useMemo(
    () => environments.filter((env) => (!projectId ? true : env.project_id === projectId)),
    [environments, projectId],
  );

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [projectData, envData] = await Promise.all([
        api.get<Project[]>("/projects"),
        api.get<Environment[]>("/environments"),
      ]);
      setProjects(projectData);
      setEnvironments(envData);
      setProjectId((current) => current || projectData[0]?.id || "");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to load environments");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const createEnvironment = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!projectId) {
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const created = await api.post<Environment>("/environments", {
        project_id: projectId,
        name: name || `Env ${envType.toUpperCase()}`,
        env_type: envType,
        base_url: baseUrl,
      });
      setEnvironments((current) => [created, ...current]);
      setName("");
      setBaseUrl("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to create environment");
    } finally {
      setSaving(false);
    }
  };

  const deleteEnvironment = async (env: Environment) => {
    setError(null);
    try {
      await api.delete<unknown>(`/environments/${encodeURIComponent(env.id)}`);
      setEnvironments((current) => current.filter((item) => item.id !== env.id));
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to delete environment");
    }
  };

  return (
    <Section
      title="环境"
      description="执行环境与连通性配置"
      action={
        <form className="inline-form" onSubmit={createEnvironment}>
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
              <label>Name</label>
              <input value={name} onChange={(event) => setName(event.target.value)} placeholder="SIT" />
            </div>
            <div className="field">
              <label>Type</label>
              <select value={envType} onChange={(event) => setEnvType(event.target.value)}>
                <option value="local">local</option>
                <option value="sit">sit</option>
                <option value="staging">staging</option>
                <option value="prod">prod</option>
              </select>
            </div>
            <div className="field">
              <label>Base URL</label>
              <input
                value={baseUrl}
                onChange={(event) => setBaseUrl(event.target.value)}
                placeholder="https://sit.example.com"
              />
            </div>
            <button className="primary-button" type="submit" disabled={saving || !projectId || !baseUrl}>
              {saving ? "Creating..." : "Create Environment"}
            </button>
          </div>
        </form>
      }
    >
      {loading ? <PageState kind="loading" message="Loading environments..." /> : null}
      {error ? <PageState kind="error" message={error} /> : null}
      {!loading && !error && filteredEnvironments.length === 0 ? <PageState kind="empty" message="No environments yet." /> : null}
      <div className="list">
        {filteredEnvironments.map((env) => (
          <div key={env.id} className="list-item">
            <div>
              <div>{env.name}</div>
              <div className="subtle">
                {env.env_type} · {env.base_url}
              </div>
              <div className="subtle">{env.project_id}</div>
            </div>
            <div className="page-actions">
              <span className={`badge ${env.enabled ? "ok" : "warn"}`}>{env.enabled ? "enabled" : "disabled"}</span>
              <button className="secondary-button" type="button" onClick={() => void deleteEnvironment(env)}>
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>
    </Section>
  );
}

