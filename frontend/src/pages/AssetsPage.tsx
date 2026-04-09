import { useEffect, useState, type FormEvent } from "react";

import { api, type Asset, type Execution, type GateRule, type Project, type ReportIndexItem, type TestSuite } from "../lib/api";
import { PageState } from "../components/PageState";
import { Section } from "../components/Section";

export function AssetsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [suites, setSuites] = useState<TestSuite[]>([]);
  const [rules, setRules] = useState<GateRule[]>([]);
  const [reports, setReports] = useState<ReportIndexItem[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projectId, setProjectId] = useState("proj_demo");
  const [assetType, setAssetType] = useState("suite");
  const [name, setName] = useState("");
  const [version, setVersion] = useState("");
  const [sourceRef, setSourceRef] = useState("");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const [projectData, suiteData, ruleData, reportData, executionData, assetData] = await Promise.all([
          api.get<Project[]>("/projects"),
          api.get<TestSuite[]>("/suites"),
          api.get<GateRule[]>("/gates/rules"),
          api.get<ReportIndexItem[]>("/reports"),
          api.get<Execution[]>("/executions"),
          api.get<Asset[]>("/assets"),
        ]);

        if (!cancelled) {
          setProjects(projectData);
          setSuites(suiteData);
          setRules(ruleData);
          setReports(reportData);
          setExecutions(executionData);
          setAssets(assetData);
          setError(null);
        }
      } catch (cause) {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Failed to load assets.");
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

  const createAsset = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaving(true);
    setError(null);

    try {
      const created = await api.post<Asset>("/assets", {
        project_id: projectId,
        asset_type: assetType,
        name,
        version: version || null,
        source_ref: sourceRef || null,
        metadata: { created_from: "assets_page" },
      });
      setAssets((current) => [created, ...current]);
      setName("");
      setVersion("");
      setSourceRef("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to create asset");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Section
      title="资产中心"
      description="项目、套件、规则、报告和执行构成的平台资产视图"
      action={
        <form className="inline-form" onSubmit={createAsset}>
          <div className="page-actions">
            <div className="field">
              <label>Project</label>
              <input value={projectId} onChange={(event) => setProjectId(event.target.value)} placeholder="proj_demo" />
            </div>
            <div className="field">
              <label>Asset Type</label>
              <input value={assetType} onChange={(event) => setAssetType(event.target.value)} placeholder="suite" />
            </div>
            <div className="field">
              <label>Name</label>
              <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Prompt Template" />
            </div>
            <div className="field">
              <label>Version</label>
              <input value={version} onChange={(event) => setVersion(event.target.value)} placeholder="v1" />
            </div>
            <div className="field">
              <label>Source Ref</label>
              <input value={sourceRef} onChange={(event) => setSourceRef(event.target.value)} placeholder="repo/job/ref" />
            </div>
            <button className="primary-button" type="submit" disabled={saving || !projectId || !assetType || !name}>
              {saving ? "Creating..." : "Create Asset"}
            </button>
          </div>
          {error ? <div className="login-error">{error}</div> : null}
        </form>
      }
    >
      {loading ? <PageState kind="loading" message="Loading assets..." /> : null}
      {error ? <PageState kind="error" message={error} /> : null}
      {!loading && !error && assets.length === 0 ? <PageState kind="empty" message="No assets yet." /> : null}
      <div className="grid cols-3">
        <div className="panel">
          <h4>Projects</h4>
          <div className="metric">{projects.length}</div>
          <div className="subtle">Registered projects</div>
        </div>
        <div className="panel">
          <h4>Suites</h4>
          <div className="metric">{suites.length}</div>
          <div className="subtle">Executable suites</div>
        </div>
        <div className="panel">
          <h4>Rules</h4>
          <div className="metric">{rules.length}</div>
          <div className="subtle">Quality gates</div>
        </div>
      </div>

      <div className="grid cols-2">
        <div className="panel soft">
          <h4>Recent Reports</h4>
          <div className="list">
            {reports.slice(0, 5).map((report) => (
              <div key={report.execution_id} className="list-item">
                <div>
                  <div>{report.execution_id}</div>
                  <div className="subtle">success rate {String(report.summary.success_rate ?? 0)}%</div>
                </div>
                <span className="badge ok">{report.status}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="panel soft">
          <h4>Recent Executions</h4>
          <div className="list">
            {executions.slice(0, 5).map((execution) => (
              <div key={execution.id} className="list-item">
                <div>
                  <div>{execution.id}</div>
                  <div className="subtle">
                    {execution.project_id} · {execution.suite_id}
                  </div>
                </div>
                <span className={`badge ${execution.status === "success" ? "ok" : "warn"}`}>{execution.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="panel soft" style={{ marginTop: 16 }}>
        <h4>Assets</h4>
        <div className="list">
          {assets.slice(0, 8).map((asset) => (
            <div key={asset.id} className="list-item">
              <div>
                <div>{asset.name}</div>
                <div className="subtle">
                  {asset.asset_type} · {asset.project_id} · {asset.version ?? "-"} · {asset.source_ref ?? "-"}
                </div>
              </div>
              <span className={`badge ${asset.status === "active" ? "ok" : "warn"}`}>{asset.status}</span>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}
