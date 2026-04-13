import { useEffect, useState, type FormEvent } from "react";

import { api, type AuditLog, type AuditOverview } from "../lib/api";
import { Highlight } from "../components/Highlight";
import { PaginationControls } from "../components/PaginationControls";
import { QueryToolbar } from "../components/QueryToolbar";
import { PageState } from "../components/PageState";
import { Section } from "../components/Section";

export function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [overview, setOverview] = useState<AuditOverview | null>(null);
  const [search, setSearch] = useState("");
  const [action, setAction] = useState("");
  const [targetType, setTargetType] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 10;
  const [loading, setLoading] = useState(true);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [overviewError, setOverviewError] = useState<string | null>(null);

  const downloadAudit = async () => {
    const query = new URLSearchParams();
    if (search) {
      query.set("search", search);
    }
    if (action) {
      query.set("action", action);
    }
    if (targetType) {
      query.set("target_type", targetType);
    }
    query.set("sort", "-id");
    const blob = await api.download(`/audit/export?${query.toString()}`);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "audit-logs.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    let cancelled = false;

    const loadOverview = async () => {
      setOverviewLoading(true);
      try {
        const data = await api.get<AuditOverview>("/audit/overview");
        if (!cancelled) {
          setOverview(data);
          setOverviewError(null);
        }
      } catch (cause) {
        if (!cancelled) {
          setOverviewError(cause instanceof Error ? cause.message : "Failed to load audit overview.");
        }
      } finally {
        if (!cancelled) {
          setOverviewLoading(false);
        }
      }
    };

    void loadOverview();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      try {
        const query = new URLSearchParams();
        if (search) {
          query.set("search", search);
        }
        if (action) {
          query.set("action", action);
        }
        if (targetType) {
          query.set("target_type", targetType);
        }
        query.set("sort", "-id");
        query.set("page", String(page));
        query.set("page_size", String(pageSize));
        const data = await api.get<AuditLog[]>(`/audit?${query.toString()}`);
        if (!cancelled) {
          setLogs(data);
          setError(null);
        }
      } catch (cause) {
        if (!cancelled) {
          setError(cause instanceof Error ? cause.message : "Failed to load audit logs.");
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
  }, [search, action, targetType, page]);

  const applySearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPage(1);
  };

  return (
    <Section
      title="审计"
      description="关键操作、执行链路和 AI 调用留痕"
      action={
        <QueryToolbar onSubmit={applySearch}>
          <div className="page-actions">
            <div className="field">
              <label>Search</label>
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="action or target" />
            </div>
            <div className="field">
              <label>Action</label>
              <input value={action} onChange={(event) => setAction(event.target.value)} placeholder="create_execution" />
            </div>
            <div className="field">
              <label>Target Type</label>
              <input value={targetType} onChange={(event) => setTargetType(event.target.value)} placeholder="execution" />
            </div>
            <button className="primary-button" type="submit">
              Filter
            </button>
            <button className="badge" type="button" onClick={downloadAudit}>
              Export CSV
            </button>
            <button
              className="badge"
              type="button"
              onClick={() => {
                setSearch("");
                setAction("");
                setTargetType("");
                setPage(1);
              }}
              >
              Reset
            </button>
          </div>
        </QueryToolbar>
      }
    >
      {overviewLoading ? <PageState kind="loading" message="Loading audit overview..." /> : null}
      {overviewError ? <PageState kind="error" message={overviewError} /> : null}
      {overview ? (
        <div className="grid cols-3">
          <div className="panel">
            <h4>Audit Logs</h4>
            <div className="metric">{overview.audit_log_count}</div>
            <div className="subtle">Recorded actions</div>
          </div>
          <div className="panel">
            <h4>Gate Changes</h4>
            <div className="metric">{overview.gate_change_count}</div>
            <div className="subtle">Quality rule changes</div>
          </div>
          <div className="panel">
            <h4>Settings Revisions</h4>
            <div className="metric">{overview.settings_revision_count}</div>
            <div className="subtle">Configuration rollbacks and updates</div>
          </div>
        </div>
      ) : null}
      {overview ? (
        <div className="grid cols-2" style={{ marginTop: 16 }}>
          <div className="panel soft">
            <h4>Connector Status</h4>
            <div className="list">
              {overview.connectors.map((connector) => (
                <div className="list-item" key={connector.connector_type}>
                  <div>
                    <div>{connector.connector_type}</div>
                    <div className="subtle">{connector.message}</div>
                  </div>
                  <span className={`badge ${connector.ok ? "ok" : "fail"}`}>{connector.status}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="panel soft">
            <h4>Recent Gate Changes</h4>
            <div className="list">
              {overview.recent_gate_changes.length === 0 ? <div className="subtle">No gate changes yet.</div> : null}
              {overview.recent_gate_changes.map((log) => (
                <div key={log.id} className="list-item">
                  <div>
                    <div>
                      <Highlight text={`${log.action} · ${log.target_id}`} query={search || action || targetType} />
                    </div>
                    <div className="subtle">{log.target_type}</div>
                  </div>
                  <span className="badge ok">{log.id}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
      {overview ? (
        <div className="grid cols-2" style={{ marginTop: 16 }}>
          <div className="panel soft">
            <h4>Settings History</h4>
            <div className="list">
              {overview.recent_settings_history.length === 0 ? <div className="subtle">No settings history yet.</div> : null}
              {overview.recent_settings_history.map((entry) => (
                <div key={`${entry.environment}-${entry.revision_number}`} className="list-item">
                  <div>
                    <div>
                      {entry.environment} · #{entry.revision_number} · {entry.action}
                    </div>
                    <div className="subtle">
                      {entry.app_name} · {entry.app_version} · {entry.log_level}
                    </div>
                    <div className="subtle">{entry.updated_at}</div>
                  </div>
                  <span className="badge ok">{entry.jenkins_user || "-"}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="panel soft">
            <h4>Asset Revisions</h4>
            <div className="list">
              {overview.recent_asset_revisions.length === 0 ? <div className="subtle">No asset revisions yet.</div> : null}
              {overview.recent_asset_revisions.map((revision) => (
                <div key={revision.id} className="list-item">
                  <div>
                    <div>
                      {revision.asset_id} · #{revision.revision_number}
                    </div>
                    <div className="subtle">
                      {revision.change_summary ?? "updated"} · {revision.version ?? "unversioned"}
                    </div>
                    <div className="subtle">{revision.created_at ?? "-"}</div>
                  </div>
                  <span className="badge ok">{revision.snapshot.status}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : null}
      {loading ? <PageState kind="loading" message="Loading audit logs..." /> : null}
      {error ? <PageState kind="error" message={error} /> : null}
      <div className="list">
        {logs.length === 0 && !loading && !error ? <PageState kind="empty" message="No audit logs yet." /> : null}
        {logs.map((log) => (
          <div key={log.id} className="list-item">
            <div>
              <div>{log.action}</div>
              <div className="subtle">
                <Highlight text={`${log.actor_id ?? "-"} · ${log.target_type} · ${log.target_id}`} query={search || action || targetType} />
              </div>
            </div>
            <span className="badge ok">{log.id}</span>
          </div>
        ))}
      </div>
      <PaginationControls
        page={page}
        pageSize={pageSize}
        itemCount={logs.length}
        onPrevious={() => setPage((current) => Math.max(current - 1, 1))}
        onNext={() => setPage((current) => current + 1)}
      />
    </Section>
  );
}
