import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { api, type ReportIndexItem } from "../lib/api";
import { Highlight } from "../components/Highlight";
import { Section } from "../components/Section";

export function ReportsPage() {
  const [reports, setReports] = useState<ReportIndexItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [completionSource, setCompletionSource] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const downloadReports = async () => {
    const query = new URLSearchParams();
    if (search) {
      query.set("search", search);
    }
    if (status) {
      query.set("status", status);
    }
    if (completionSource) {
      query.set("completion_source", completionSource);
    }
    const blob = await api.download(`/reports/export?${query.toString()}`);
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "reports-export.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const query = new URLSearchParams();
        if (search) {
          query.set("search", search);
        }
        if (status) {
          query.set("status", status);
        }
        if (completionSource) {
          query.set("completion_source", completionSource);
        }
        query.set("page", String(page));
        query.set("page_size", String(pageSize));
        const data = await api.get<ReportIndexItem[]>(`/reports?${query.toString()}`);
        if (!cancelled) {
          setReports(data);
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
  }, [search, status, completionSource, page]);

  const applySearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPage(1);
  };

  return (
    <Section
      title="报告"
      description="统一展示原始报告、摘要和趋势"
      action={
        <form className="inline-form" onSubmit={applySearch}>
          <div className="page-actions">
            <div className="field">
              <label>Search</label>
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="execution id" />
            </div>
            <div className="field">
              <label>Status</label>
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                <option value="">all</option>
                <option value="queued">queued</option>
                <option value="running">running</option>
                <option value="success">success</option>
                <option value="failed">failed</option>
                <option value="timeout">timeout</option>
              </select>
            </div>
            <div className="field">
              <label>Source</label>
              <select value={completionSource} onChange={(event) => setCompletionSource(event.target.value)}>
                <option value="">all</option>
                <option value="callback">callback</option>
                <option value="poller_success">poller_success</option>
                <option value="poller_exhausted">poller_exhausted</option>
                <option value="trigger">trigger</option>
                <option value="timeout_sweeper">timeout_sweeper</option>
              </select>
            </div>
            <button className="primary-button" type="submit">
              Filter
            </button>
            <button className="badge" type="button" onClick={downloadReports}>
              Export CSV
            </button>
            <button
              className="badge"
              type="button"
              onClick={() => {
                setSearch("");
                setStatus("");
                setCompletionSource("");
                setPage(1);
              }}
            >
              Reset
            </button>
          </div>
        </form>
      }
    >
      {loading ? <div className="subtle">Loading reports...</div> : null}
      <div className="list">
        {reports.length === 0 && !loading ? <div className="subtle">No reports yet.</div> : null}
        {reports.map((report) => (
          <Link key={report.execution_id} className="list-item" to={`/executions/${report.execution_id}`}>
            <div>
              <div>{report.execution_id}</div>
              <div className="subtle">
                总数 {String(report.summary.total ?? 0)} / 通过 {String(report.summary.passed ?? 0)} / 失败{" "}
                {String(report.summary.failed ?? 0)} · 任务 {String(report.task_count ?? 0)}
              </div>
              <div className="subtle">
                状态 {report.status} · 来源 {report.completion_source ?? "-"} · 开始 {report.started_at ?? "-"} · 完成{" "}
                {report.completed_at ?? "-"}
              </div>
              <div className="subtle">
                <Highlight text={report.execution_id} query={search} />
              </div>
              {report.tasks.length > 0 ? (
                <div className="subtle">
                  {report.tasks
                    .slice(0, 2)
                    .map((task) => `${String(task.task_key)}:${String(task.status)}`)
                    .join(" · ")}
                </div>
              ) : null}
            </div>
            <span className={`badge ${report.status === "success" ? "ok" : "warn"}`}>
              {String(report.summary.success_rate ?? 0)}%
            </span>
          </Link>
        ))}
      </div>
      <div className="page-actions" style={{ marginTop: 16 }}>
        <button className="badge" type="button" disabled={page <= 1} onClick={() => setPage((current) => Math.max(current - 1, 1))}>
          Previous
        </button>
        <span className="subtle">Page {page}</span>
        <button className="badge" type="button" disabled={reports.length < pageSize} onClick={() => setPage((current) => current + 1)}>
          Next
        </button>
      </div>
    </Section>
  );
}
