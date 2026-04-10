import { useEffect, useMemo, useState } from "react";

import { api, type ConnectorInfo, type Settings, type SettingsHistoryEntry } from "../lib/api";
import { PageState } from "../components/PageState";
import { Section } from "../components/Section";

const ENVIRONMENTS = ["local", "sit", "staging", "prod"] as const;

type EnvironmentKey = (typeof ENVIRONMENTS)[number];

export function SettingsPage() {
  const [selectedEnvironment, setSelectedEnvironment] = useState<EnvironmentKey>("local");
  const [settings, setSettings] = useState<Settings | null>(null);
  const [history, setHistory] = useState<SettingsHistoryEntry[]>([]);
  const [connectors, setConnectors] = useState<ConnectorInfo[]>([]);
  const [connectorStatus, setConnectorStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);
  const [rollBackMessage, setRollbackMessage] = useState<string | null>(null);
  const [appName, setAppName] = useState("");
  const [appVersion, setAppVersion] = useState("");
  const [logLevel, setLogLevel] = useState("");
  const [jenkinsUrl, setJenkinsUrl] = useState("");
  const [jenkinsUser, setJenkinsUser] = useState("");

  const settingsQuery = useMemo(() => `?environment=${encodeURIComponent(selectedEnvironment)}`, [selectedEnvironment]);

  const loadSettings = async (environment: EnvironmentKey) => {
    setLoading(true);
    setError(null);
    try {
      const [settingsData, connectorData] = await Promise.all([
        api.get<Settings>(`/settings?environment=${encodeURIComponent(environment)}`),
        api.get<ConnectorInfo[]>("/connectors"),
      ]);
      setSettings(settingsData);
      setConnectors(connectorData);
      setAppName(settingsData.app_name);
      setAppVersion(settingsData.app_version);
      setLogLevel(settingsData.log_level);
      setJenkinsUrl(settingsData.jenkins_url);
      setJenkinsUser(settingsData.jenkins_user);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async (environment: EnvironmentKey) => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const historyData = await api.get<SettingsHistoryEntry[]>(
        `/settings/history?environment=${encodeURIComponent(environment)}`,
      );
      setHistory(historyData);
    } catch (err) {
      setHistoryError(err instanceof Error ? err.message : "Failed to load settings history");
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    void loadSettings(selectedEnvironment);
    void loadHistory(selectedEnvironment);
    setConnectorStatus(null);
    setSaveMessage(null);
    setRollbackMessage(null);
  }, [selectedEnvironment]);

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
      const updated = await api.put<Settings>(`/settings${settingsQuery}`, {
        app_name: appName,
        app_version: appVersion,
        log_level: logLevel,
        jenkins_url: jenkinsUrl,
        jenkins_user: jenkinsUser,
      });
      setSettings(updated);
      setSaveMessage(`Settings saved for ${selectedEnvironment} (revision ${updated.revision_number})`);
      await loadHistory(selectedEnvironment);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const rollbackSettings = async (revisionNumber: number) => {
    setRollbackMessage(null);
    setError(null);
    try {
      const updated = await api.post<Settings>("/settings/rollback", {
        environment: selectedEnvironment,
        revision_number: revisionNumber,
      });
      setSettings(updated);
      setAppName(updated.app_name);
      setAppVersion(updated.app_version);
      setLogLevel(updated.log_level);
      setJenkinsUrl(updated.jenkins_url);
      setJenkinsUser(updated.jenkins_user);
      setRollbackMessage(`Rolled back ${selectedEnvironment} to revision ${revisionNumber}`);
      await loadHistory(selectedEnvironment);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to rollback settings");
    }
  };

  return (
    <Section title="配置" description="通知、连接器、环境和系统设置">
      <div className="page-actions" style={{ marginBottom: 16 }}>
        <div className="field">
          <label>Environment</label>
          <select value={selectedEnvironment} onChange={(event) => setSelectedEnvironment(event.target.value as EnvironmentKey)}>
            {ENVIRONMENTS.map((environment) => (
              <option key={environment} value={environment}>
                {environment}
              </option>
            ))}
          </select>
        </div>
        {settings ? <span className="badge ok">revision {settings.revision_number}</span> : null}
      </div>
      {loading ? <PageState kind="loading" message={`Loading settings for ${selectedEnvironment}...`} /> : null}
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
            {rollBackMessage ? <div className="subtle" style={{ marginBottom: 12 }}>{rollBackMessage}</div> : null}
            <div className="list">
              <div className="list-item">
                <div>
                  <div>Environment</div>
                  <div className="subtle">{settings.environment}</div>
                </div>
                <span className="badge ok">revision {settings.revision_number}</span>
              </div>
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
            <h4>版本历史</h4>
            {historyLoading ? <PageState kind="loading" message={`Loading ${selectedEnvironment} history...`} /> : null}
            {historyError ? <PageState kind="error" message={historyError} /> : null}
            {!historyLoading && !historyError && history.length === 0 ? (
              <PageState kind="empty" message="No settings history yet." />
            ) : null}
            <div className="list">
              {history.map((entry) => (
                <div className="list-item" key={`${entry.environment}-${entry.revision_number}`}>
                  <div>
                    <div>
                      #{entry.revision_number} · {entry.action}
                    </div>
                    <div className="subtle">
                      {entry.app_name} · {entry.app_version} · {entry.log_level}
                    </div>
                    <div className="subtle">
                      Jenkins: {entry.jenkins_url || "-"} / {entry.jenkins_user || "-"}
                    </div>
                    <div className="subtle">{entry.updated_at}</div>
                  </div>
                  <button
                    className="secondary-button"
                    type="button"
                    onClick={() => void rollbackSettings(entry.revision_number)}
                    disabled={entry.revision_number === settings.revision_number}
                  >
                    Rollback
                  </button>
                </div>
              ))}
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
                  <span className={`badge ${connector.ok ? "ok" : "fail"}`}>{connector.status}</span>
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
