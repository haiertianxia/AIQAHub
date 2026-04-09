import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api, type ReportIndexItem } from "../lib/api";
import { Section } from "../components/Section";

export function ReportsPage() {
  const [reports, setReports] = useState<ReportIndexItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const data = await api.get<ReportIndexItem[]>("/reports");
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
  }, []);

  return (
    <Section title="报告" description="统一展示原始报告、摘要和趋势">
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
    </Section>
  );
}
