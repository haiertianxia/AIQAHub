import { useEffect, useState } from "react";

import { api, type AuditLog } from "../lib/api";
import { Section } from "../components/Section";

export function AuditPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const data = await api.get<AuditLog[]>("/audit");
      if (!cancelled) {
        setLogs(data);
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Section title="审计" description="关键操作、执行链路和 AI 调用留痕">
      <div className="list">
        {logs.map((log) => (
          <div key={log.id} className="list-item">
            <div>
              <div>{log.action}</div>
              <div className="subtle">
                {log.actor_id ?? "-"} · {log.target_type} · {log.target_id}
              </div>
            </div>
            <span className="badge ok">{log.id}</span>
          </div>
        ))}
      </div>
    </Section>
  );
}
