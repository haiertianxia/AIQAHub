import { useEffect, useState } from "react";

import { api, type ConnectorInfo, type Settings } from "../lib/api";
import { Section } from "../components/Section";

export function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [connectors, setConnectors] = useState<ConnectorInfo[]>([]);
  const [connectorStatus, setConnectorStatus] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      const [settingsData, connectorData] = await Promise.all([
        api.get<Settings>("/settings"),
        api.get<ConnectorInfo[]>("/connectors"),
      ]);
      if (!cancelled) {
        setSettings(settingsData);
        setConnectors(connectorData);
      }
    };

    void load();

    return () => {
      cancelled = true;
    };
  }, []);

  const testJenkins = async () => {
    setConnectorStatus(null);
    const result = await api.post<ConnectorInfo>("/connectors/jenkins/test", {
      payload: {
        base_url: settings?.jenkins_url ?? "",
        username: settings?.jenkins_user ?? "",
      },
    });
    setConnectorStatus(`${result.connector_type}: ${result.message}`);
  };

  return (
    <Section title="配置" description="通知、连接器、环境和系统设置">
      {settings ? (
        <div className="panel-grid">
          <div className="panel">
            <h4>系统设置</h4>
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
              <div className="list-item">
                <div>
                  <div>Jenkins</div>
                  <div className="subtle">{settings.jenkins_url || "not configured"}</div>
                </div>
                <span className={`badge ${settings.jenkins_url ? "ok" : "warn"}`}>{settings.jenkins_user || "-"}</span>
              </div>
            </div>
          </div>
          <div className="panel">
            <h4>连接器</h4>
            <div className="list">
              {connectors.map((connector) => (
                <div className="list-item" key={connector.connector_type}>
                  <div>
                    <div>{connector.connector_type}</div>
                    <div className="subtle">{connector.message}</div>
                  </div>
                  <span className={`badge ${connector.ok ? "ok" : "fail"}`}>{connector.ok ? "ok" : "off"}</span>
                </div>
              ))}
            </div>
            <div className="page-actions" style={{ marginTop: 16 }}>
              <button className="primary-button" type="button" onClick={() => void testJenkins()}>
                Test Jenkins
              </button>
            </div>
            {connectorStatus ? <div className="subtle" style={{ marginTop: 12 }}>{connectorStatus}</div> : null}
          </div>
        </div>
      ) : (
        <div className="subtle">Loading settings...</div>
      )}
    </Section>
  );
}
