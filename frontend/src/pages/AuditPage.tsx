import { useEffect, useState, type FormEvent } from "react";

import { api, type AuditLog } from "../lib/api";
import { Highlight } from "../components/Highlight";
import { Section } from "../components/Section";

export function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [search, setSearch] = useState("");
  const [action, setAction] = useState("");
  const [targetType, setTargetType] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 10;

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

    const load = async () => {
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
      query.set("page", String(page));
      query.set("page_size", String(pageSize));
      const data = await api.get<AuditLog[]>(`/audit?${query.toString()}`);
      if (!cancelled) {
        setLogs(data);
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
        <form className="inline-form" onSubmit={applySearch}>
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
        </form>
      }
    >
      <div className="list">
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
      <div className="page-actions" style={{ marginTop: 16 }}>
        <button className="badge" type="button" disabled={page <= 1} onClick={() => setPage((current) => Math.max(current - 1, 1))}>
          Previous
        </button>
        <span className="subtle">Page {page}</span>
        <button className="badge" type="button" disabled={logs.length < pageSize} onClick={() => setPage((current) => current + 1)}>
          Next
        </button>
      </div>
    </Section>
  );
}
