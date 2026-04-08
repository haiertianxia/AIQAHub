import { useEffect, useState } from "react";

import { api, type Execution, type GateRule, type Project, type ReportIndexItem, type TestSuite } from "../lib/api";
import { Section } from "../components/Section";

export function AssetsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [suites, setSuites] = useState<TestSuite[]>([]);
  const [rules, setRules] = useState<GateRule[]>([]);
  const [reports, setReports] = useState<ReportIndexItem[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const [projectData, suiteData, ruleData, reportData, executionData] = await Promise.all([
        api.get<Project[]>("/projects"),
        api.get<TestSuite[]>("/suites"),
        api.get<GateRule[]>("/gates/rules"),
        api.get<ReportIndexItem[]>("/reports"),
        api.get<Execution[]>("/executions"),
      ]);

      if (!cancelled) {
        setProjects(projectData);
        setSuites(suiteData);
        setRules(ruleData);
        setReports(reportData);
        setExecutions(executionData);
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Section title="资产中心" description="项目、套件、规则、报告和执行构成的平台资产视图">
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
    </Section>
  );
}
