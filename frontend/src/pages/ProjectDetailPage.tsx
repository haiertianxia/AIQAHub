import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api, type Project } from "../lib/api";
import { Section } from "../components/Section";

export function ProjectDetailPage() {
  const { projectId } = useParams();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      if (!projectId) {
        setLoading(false);
        return;
      }

      try {
        const data = await api.get<Project>(`/projects/${projectId}`);
        if (!cancelled) {
          setProject(data);
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
      {loading ? <div className="subtle">Loading project detail...</div> : null}
      {!loading && !project ? <div className="subtle">Project not found.</div> : null}
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
