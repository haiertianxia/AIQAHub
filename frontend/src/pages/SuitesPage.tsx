import { useEffect, useState } from "react";

import { api, type TestSuite } from "../lib/api";
import { Section } from "../components/Section";

export function SuitesPage() {
  const [suites, setSuites] = useState<TestSuite[]>([]);

  useEffect(() => {
    let cancelled = false;
    const load = async () => {
      const data = await api.get<TestSuite[]>("/suites");
      if (!cancelled) {
        setSuites(data);
      }
    };
    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Section title="套件" description="注册到平台的测试套件和入口">
      <div className="list">
        {suites.map((suite) => (
          <div key={suite.id} className="list-item">
            <div>
              <div>{suite.name}</div>
              <div className="subtle">
                {suite.suite_type} · {suite.source_type} · {suite.source_ref}
              </div>
              <div className="subtle">Default env: {suite.default_env_id ?? "-"}</div>
            </div>
            <span className="badge ok">{suite.source_type}</span>
          </div>
        ))}
      </div>
    </Section>
  );
}
