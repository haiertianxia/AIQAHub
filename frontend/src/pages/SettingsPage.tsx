import { useEffect, useState } from "react";

import { api, type ConnectorInfo, type Settings } from "../lib/api";
import { PageState } from "../components/PageState";
import { Section } from "../components/Section";

export function SettingsPage() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [connectors, setConnectors] = useState<ConnectorInfo[]>([]);
  const [connectorStatus, setConnectorStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [appName, setAppName] = useState("");
  const [appVersion, setAppVersion] = useState("");
  const [logLevel, setLogLevel] = useState("");
  const [jenkinsUrl, setJenkinsUrl] = useState("");
  const [jenkinsUser, setJenkinsUser] = useState("");

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const [settingsData, connectorData] = await Promise.all([
          api.get<Settings>("/settings"),
          api.get<ConnectorInfo[]>("/connectors"),
        ]);
        if (!cancelled) {
          setSettings(settingsData);
          setConnectors(connectorData);
          setAppName(settingsData.app_name);
          setAppVersion(settingsData.app_version);
          setLogLevel(settingsData.log_level);
          setJenkinsUrl(settingsData.jenkins_url);
          setJenkinsUser(settingsData.jenkins_user);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load settings");
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

  const testJenkins = async () => {
    setConnectorStatus(null);
    const result = await api.post<ConnectorInfo>("/connectors/jenkins/test", {
      payload: {
        base_url: jenkinsUrl || settings?.jenkins_url || "",
        username: jenkinsUser || settings?.jenkins_user || "",
      },
    });
    setConnectorStatus(`${result.connector_type}: ${result.message}`);
  };

  const saveSettings = async () => {
    setSaving(true);
    setSaveMessage(null);
    setError(null);
    try {
      const updated = await api.put<Settings>("/settings", {
        app_name: appName,
        app_version: appVersion,
        log_level: logLevel,
        jenkins_url: jenkinsUrl,
        jenkins_user: jenkinsUser,
      });
      setSettings(updated);
      setSaveMessage("Settings saved");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Section title="配置" description="通知、连接器、环境和系统设置">
      {loading ? <PageState kind="loading" message="Loading settings..." /> : null}
      {error ? <PageState kind="error" message={error} /> : null}
      {!loading && !error && !settings ? <PageState kind="empty" message="No settings available." /> : null}
      {settings ? (
        <div className="panel-grid">
          <div className="panel">
            <h4>系统设置</h4>
            <div className="page-actions" style={{ marginBottom: 16 }}>
              <div className="field">
                <label>App Name</label>
                <input value={appName} onChange={(event) => setAppName(event.target.value)} />
              </div>
              <div className="field">
                <label>App Version</label>
                <input value={appVersion} onChange={(event) => setAppVersion(event.target.value)} />
              </div>
              <div className="field">
                <label>Log Level</label>
                <input value={logLevel} onChange={(event) => setLogLevel(event.target.value)} />
              </div>
              <div className="field">
                <label>Jenkins URL</label>
                <input value={jenkinsUrl} onChange={(event) => setJenkinsUrl(event.target.value)} />
              </div>
              <div className="field">
                <label>Jenkins User</label>
                <input value={jenkinsUser} onChange={(event) => setJenkinsUser(event.target.value)} />
              </div>
              <button className="primary-button" type="button" onClick={() => void saveSettings()} disabled={saving}>
                {saving ? "Saving..." : "Save Settings"}
              </button>
            </div>
            {saveMessage ? <div className="subtle" style={{ marginBottom: 12 }}>{saveMessage}</div> : null}
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
      ) : null}
    </Section>
  );
}
