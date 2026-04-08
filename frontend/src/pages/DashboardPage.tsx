import { useEffect, useState } from "react";

import { api, type Execution, type Project } from "../lib/api";
import { Section } from "../components/Section";

export function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const [projectData, executionData] = await Promise.all([
        api.get<Project[]>("/projects"),
        api.get<Execution[]>("/executions"),
      ]);
      if (!cancelled) {
        setProjects(projectData);
        setExecutions(executionData);
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  const successCount = executions.filter((item) => item.status === "success").length;
  const successRate = executions.length > 0 ? `${Math.round((successCount / executions.length) * 100)}%` : "0%";
  const riskCount = executions.filter((item) => item.status !== "success").length;
  const gateFailures = executions.filter((item) => item.status === "failed").length;
  const metrics = [
    { label: "项目数", value: String(projects.length), tone: "ok" as const },
    { label: "执行数", value: String(executions.length), tone: "ok" as const },
    { label: "成功率", value: successRate, tone: "ok" as const },
    { label: "风险项", value: String(riskCount + gateFailures), tone: "warn" as const },
  ];

  return (
    <>
      <div className="hero">
        <h2>质量控制台</h2>
        <p>
          统一接入项目、测试套件、执行记录、AI 分析和质量门禁。先以控制面、执行面和报告面闭环，
          再逐步接入更多域能力。
        </p>
        <div className="grid cols-4">
          {metrics.map((metric) => (
            <div key={metric.label} className="panel soft">
              <div className={`badge ${metric.tone ?? ""}`.trim()}>{metric.label}</div>
              <div className="metric" style={{ marginTop: 12 }}>
                {metric.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid cols-3">
        <Section title="最近门禁" description="执行后的质量判定结果">
          <div className="list">
            {executions.slice(0, 4).map((execution) => (
              <div key={execution.id} className="list-item">
                <div>
                  <div>{execution.id}</div>
                  <div className="subtle">最新一次执行结果</div>
                </div>
                <span className={`badge ${execution.status === "success" ? "ok" : "warn"}`}>
                  {execution.status.toUpperCase()}
                </span>
              </div>
            ))}
          </div>
        </Section>

        <Section title="AI 结论" description="对最新执行的摘要和风险分析">
          <div className="list">
            <div className="list-item">
              <div>
                <div>失败聚类</div>
                <div className="subtle">登录链路占比上升</div>
              </div>
              <span className="badge warn">72</span>
            </div>
            <div className="list-item">
              <div>
                <div>根因初判</div>
                <div className="subtle">疑似 token 过期</div>
              </div>
              <span className="badge ok">0.84</span>
            </div>
          </div>
        </Section>

        <Section title="执行趋势" description="近七天质量波动">
          <div className="list">
            <div className="list-item">
              <div>
                <div>回归成功率</div>
                <div className="subtle">稳定在 95% 以上</div>
              </div>
              <span className="badge ok">+1.8%</span>
            </div>
            <div className="list-item">
              <div>
                <div>平均时长</div>
                <div className="subtle">较上周下降</div>
              </div>
              <span className="badge ok">-12%</span>
            </div>
          </div>
        </Section>
      </div>
    </>
  );
}
