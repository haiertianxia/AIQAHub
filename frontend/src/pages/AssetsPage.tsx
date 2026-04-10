import { useEffect, useState, type FormEvent } from "react";

import {
  api,
  type Asset,
  type AssetLink,
  type AssetRevision,
  type Execution,
  type GateRule,
  type Project,
  type ReportIndexItem,
  type TestSuite,
} from "../lib/api";
import { PageState } from "../components/PageState";
import { Section } from "../components/Section";

export function AssetsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [suites, setSuites] = useState<TestSuite[]>([]);
  const [rules, setRules] = useState<GateRule[]>([]);
  const [reports, setReports] = useState<ReportIndexItem[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [assets, setAssets] = useState<Asset[]>([]);
  const [selectedAssetId, setSelectedAssetId] = useState<string | null>(null);
  const [revisions, setRevisions] = useState<AssetRevision[]>([]);
  const [links, setLinks] = useState<AssetLink[]>([]);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [linkSaving, setLinkSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [projectId, setProjectId] = useState("proj_demo");
  const [assetType, setAssetType] = useState("suite");
  const [name, setName] = useState("");
  const [version, setVersion] = useState("");
  const [sourceRef, setSourceRef] = useState("");
  const [refType, setRefType] = useState("suite");
  const [refId, setRefId] = useState("suite_demo");
  const [refName, setRefName] = useState("API 回归套件");
  const [reason, setReason] = useState("used by regression suite");

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
          setSelectedAssetId((current) => current ?? assetData[0]?.id ?? null);
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

  useEffect(() => {
    let cancelled = false;

    const loadAssetDetails = async () => {
      if (!selectedAssetId) {
        setRevisions([]);
        setLinks([]);
        setDetailError(null);
        return;
      }

      setDetailLoading(true);
      try {
        const [revisionData, linkData] = await Promise.all([
          api.get<AssetRevision[]>(`/assets/${selectedAssetId}/revisions`),
          api.get<AssetLink[]>(`/assets/${selectedAssetId}/links`),
        ]);
        if (!cancelled) {
          setRevisions(revisionData);
          setLinks(linkData);
          setDetailError(null);
        }
      } catch (cause) {
        if (!cancelled) {
          setDetailError(cause instanceof Error ? cause.message : "Failed to load asset details.");
        }
      } finally {
        if (!cancelled) {
          setDetailLoading(false);
        }
      }
    };

    void loadAssetDetails();

    return () => {
      cancelled = true;
    };
  }, [selectedAssetId]);

  const refreshAssetDetails = async (assetId: string) => {
    const [revisionData, linkData] = await Promise.all([
      api.get<AssetRevision[]>(`/assets/${assetId}/revisions`),
      api.get<AssetLink[]>(`/assets/${assetId}/links`),
    ]);
    setRevisions(revisionData);
    setLinks(linkData);
  };

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
      setSelectedAssetId(created.id);
      setName("");
      setVersion("");
      setSourceRef("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to create asset");
    } finally {
      setSaving(false);
    }
  };

  const createLink = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!selectedAssetId) {
      return;
    }
    setLinkSaving(true);
    setError(null);

    try {
      const created = await api.post<AssetLink>(`/assets/${selectedAssetId}/links`, {
        ref_type: refType,
        ref_id: refId,
        ref_name: refName,
        reason,
      });
      setLinks((current) => [...current, created]);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to create asset link");
    } finally {
      setLinkSaving(false);
    }
  };

  const archiveAsset = async (asset: Asset) => {
    setError(null);
    try {
      const archived = await api.delete<Asset>(`/assets/${asset.id}`);
      setAssets((current) => current.map((item) => (item.id === archived.id ? archived : item)));
      setSelectedAssetId(archived.id);
      await refreshAssetDetails(archived.id);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to archive asset");
    }
  };

  const selectedAsset = selectedAssetId ? assets.find((asset) => asset.id === selectedAssetId) ?? null : null;

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
            <div
              key={asset.id}
              className="list-item"
              role="button"
              tabIndex={0}
              onClick={() => setSelectedAssetId(asset.id)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  setSelectedAssetId(asset.id);
                }
              }}
              style={{
                cursor: "pointer",
                border: selectedAssetId === asset.id ? "1px solid rgba(255,255,255,0.35)" : undefined,
              }}
            >
              <div>
                <div>{asset.name}</div>
                <div className="subtle">
                  {asset.asset_type} · {asset.project_id} · {asset.version ?? "-"} · {asset.source_ref ?? "-"}
                </div>
              </div>
              <div className="row">
                <span className={`badge ${asset.status === "active" ? "ok" : "warn"}`}>{asset.status}</span>
                <button className="secondary-button" type="button" onClick={() => setSelectedAssetId(asset.id)}>
                  Open
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel soft">
          <div className="row space-between">
            <h4 style={{ margin: 0 }}>Governance Detail</h4>
            {selectedAsset ? <span className="badge ok">{selectedAsset.version ?? "unversioned"}</span> : null}
          </div>
          {detailLoading ? <PageState kind="loading" message="Loading asset governance..." /> : null}
          {detailError ? <PageState kind="error" message={detailError} /> : null}
          {!detailLoading && !detailError && selectedAsset ? (
            <>
              <div className="panel" style={{ marginTop: 12 }}>
                <div className="row space-between">
                  <div>
                    <div className="metric">{selectedAsset.name}</div>
                    <div className="subtle">
                      {selectedAsset.asset_type} · {selectedAsset.project_id}
                    </div>
                  </div>
                  <button className="secondary-button" type="button" onClick={() => void archiveAsset(selectedAsset)}>
                    Archive
                  </button>
                </div>
                <div className="subtle" style={{ marginTop: 8 }}>
                  Source: {selectedAsset.source_ref ?? "-"}
                </div>
                <div className="subtle">Reference count: {links.length}</div>
              </div>

              <div className="panel" style={{ marginTop: 12 }}>
                <h4>References</h4>
                <form className="inline-form" onSubmit={createLink}>
                  <div className="page-actions">
                    <div className="field">
                      <label>Type</label>
                      <input value={refType} onChange={(event) => setRefType(event.target.value)} placeholder="suite" />
                    </div>
                    <div className="field">
                      <label>Ref ID</label>
                      <input value={refId} onChange={(event) => setRefId(event.target.value)} placeholder="suite_demo" />
                    </div>
                    <div className="field">
                      <label>Ref Name</label>
                      <input value={refName} onChange={(event) => setRefName(event.target.value)} placeholder="API 回归套件" />
                    </div>
                    <div className="field">
                      <label>Reason</label>
                      <input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="used by regression suite" />
                    </div>
                    <button className="primary-button" type="submit" disabled={linkSaving || !refType || !refId || !refName || !reason}>
                      {linkSaving ? "Linking..." : "Add Reference"}
                    </button>
                  </div>
                </form>
                <div className="list" style={{ marginTop: 12 }}>
                  {links.length === 0 ? <div className="subtle">No references yet.</div> : null}
                  {links.map((link) => (
                    <div key={link.id} className="list-item">
                      <div>
                        <div>
                          {link.ref_name} <span className="subtle">({link.ref_type})</span>
                        </div>
                        <div className="subtle">
                          {link.ref_id} · {link.reason}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : null}
          {!detailLoading && !detailError && !selectedAsset ? <PageState kind="empty" message="Select an asset to inspect governance details." /> : null}
        </div>

        <div className="panel soft">
          <h4>Revision History</h4>
          <div className="list">
            {revisions.length === 0 ? <div className="subtle">No revisions yet.</div> : null}
            {revisions.map((revision) => (
              <div key={revision.id} className="list-item">
                <div>
                  <div>
                    #{revision.revision_number} · {revision.version ?? "unversioned"}
                  </div>
                  <div className="subtle">{revision.change_summary ?? "updated"}</div>
                  <div className="subtle">Created: {revision.created_at ?? "-"}</div>
                </div>
                <span className="badge ok">{revision.snapshot.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </Section>
  );
}
