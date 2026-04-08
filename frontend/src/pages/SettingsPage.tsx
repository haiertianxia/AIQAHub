import { useEffect, useState } from "react";

import { api, type Settings } from "../lib/api";
import { Section } from "../components/Section";

export function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const data = await api.get<Settings>("/settings");
      if (!cancelled) {
        setSettings(data);
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <Section title="配置" description="通知、连接器、环境和系统设置">
      {settings ? (
        <div className="list">
          <div className="list-item">
            <div>
              <div>App Name</div>
              <div className="subtle">{settings.app_name}</div>
            </div>
            <span className="badge ok">{settings.app_version}</span>
          </div>
          <div className="list-item">
            <div>
              <div>Log Level</div>
              <div className="subtle">{settings.log_level}</div>
            </div>
            <span className="badge ok">{settings.database_url}</span>
          </div>
          <div className="list-item">
            <div>
              <div>Redis</div>
              <div className="subtle">{settings.redis_url}</div>
            </div>
            <span className="badge ok">connected</span>
          </div>
        </div>
      ) : (
        <div className="subtle">Loading settings...</div>
      )}
    </Section>
  );
}
