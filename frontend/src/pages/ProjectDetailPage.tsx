import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api, type Project } from "../lib/api";
import { PageState } from "../components/PageState";
import { Section } from "../components/Section";

export function ProjectDetailPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProject = async (cancelledRef?: { current: boolean }) => {
    setLoading(true);
    setError(null);
    setProject(null);

    if (!projectId) {
      if (!cancelledRef?.current) {
        setLoading(false);
      }
      return;
    }

    try {
      const data = await api.get<Project>(`/projects/${projectId}`);
      if (!cancelledRef?.current) {
        setProject(data);
      }
    } catch (err) {
      if (!cancelledRef?.current) {
        setError(err instanceof Error ? err.message : "Failed to load project detail");
      }
    } finally {
      if (!cancelledRef?.current) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    const cancelled = { current: false };

    void loadProject(cancelled);

    return () => {
      cancelled.current = true;
    };
  }, [projectId]);

  return (
    <Section
      title="项目详情"
      description="查看项目的基础定义和归属信息。"
      action={
        <Link className="badge" to="/projects">
          返回项目列表
        </Link>
      }
    >
      {loading ? <PageState kind="loading" message="Loading project detail..." /> : null}
      {
        error ? (
          <PageState
            kind="error"
            message={error}
            action={
              <button className="primary-button" onClick={() => void loadProject()} type="button">
                Retry
              </button>
            }
          />
        ) : null
      }
      {!loading && !project && !error ? <PageState kind="empty" message="Project not found." /> : null}
      {project ? (
        <div className="detail-grid">
          <div className="panel">
            <h4>基本信息</h4>
            <div className="kv">
              <div>
                <span>Project ID</span>
                <strong>{project.id}</strong>
              </div>
              <div>
                <span>Code</span>
                <strong>{project.code}</strong>
              </div>
              <div>
                <span>Name</span>
                <strong>{project.name}</strong>
              </div>
              <div>
                <span>Status</span>
                <strong>{project.status}</strong>
              </div>
              <div>
                <span>Owner</span>
                <strong>{project.owner_id ?? "-"}</strong>
              </div>
              <div>
                <span>Description</span>
                <strong>{project.description ?? "-"}</strong>
              </div>
            </div>
          </div>
        </div>
      ) : null}
    </Section>
  );
}
