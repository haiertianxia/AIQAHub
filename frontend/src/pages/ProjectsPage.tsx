import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { api, type Project } from "../lib/api";
import { Section } from "../components/Section";

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await api.get<Project[]>("/projects");
        if (!cancelled) {
          setProjects(data);
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

  const createProject = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const created = await api.post<Project>("/projects", {
        code,
        name,
        description: description || null,
      });
      setProjects((current) => [created, ...current]);
      setCode("");
      setName("");
      setDescription("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Section
      title="项目"
      description="平台管理的测试项目集合"
      action={
        <form className="inline-form" onSubmit={createProject}>
          <div className="page-actions">
            <div className="field">
              <label>Code</label>
              <input value={code} onChange={(event) => setCode(event.target.value)} placeholder="omni" />
            </div>
            <div className="field">
              <label>Name</label>
              <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Omnichannel" />
            </div>
            <div className="field">
              <label>Description</label>
              <input
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="测试项目说明"
              />
            </div>
            <button className="primary-button" type="submit" disabled={saving || !code || !name}>
              {saving ? "Creating..." : "Create Project"}
            </button>
          </div>
          {error ? <div className="login-error">{error}</div> : null}
        </form>
      }
    >
      {loading ? <div className="subtle">Loading projects...</div> : null}
      <div className="list">
        {projects.map((project) => (
          <Link key={project.id} className="list-item" to={`/projects/${project.id}`}>
            <div>
              <div>{project.name}</div>
              <div className="subtle">
                {project.code}
                {project.description ? ` · ${project.description}` : ""}
              </div>
            </div>
            <span className="badge ok">{project.status}</span>
          </Link>
        ))}
      </div>
    </Section>
  );
}
