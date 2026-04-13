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
  const [aiProvider, setAiProvider] = useState("");
  const [aiModelName, setAiModelName] = useState("");
  const [notificationDefaultChannel, setNotificationDefaultChannel] = useState("");
  const [notificationEmailEnabled, setNotificationEmailEnabled] = useState(false);
  const [notificationEmailSmtpHost, setNotificationEmailSmtpHost] = useState("");
  const [notificationEmailSmtpPort, setNotificationEmailSmtpPort] = useState("25");
  const [notificationEmailFrom, setNotificationEmailFrom] = useState("");
  const [notificationEmailTo, setNotificationEmailTo] = useState("");
  const [notificationDingtalkEnabled, setNotificationDingtalkEnabled] = useState(false);
  const [notificationDingtalkWebhookUrl, setNotificationDingtalkWebhookUrl] = useState("");
  const [notificationWecomEnabled, setNotificationWecomEnabled] = useState(false);
  const [notificationWecomWebhookUrl, setNotificationWecomWebhookUrl] = useState("");
  const [notificationPoliciesText, setNotificationPoliciesText] = useState("[]");
  const [notificationTestMessage, setNotificationTestMessage] = useState("AIQAHub notification test");
  const [notificationTestProjectId, setNotificationTestProjectId] = useState("proj_demo");
  const [notificationTestEventType, setNotificationTestEventType] = useState("notification_test");
  const [notificationStatus, setNotificationStatus] = useState<string | null>(null);

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
      setAiProvider(settingsData.ai_provider);
      setAiModelName(settingsData.ai_model_name);
      setNotificationDefaultChannel(settingsData.notification_default_channel);
      setNotificationEmailEnabled(settingsData.notification_email_enabled);
      setNotificationEmailSmtpHost(settingsData.notification_email_smtp_host);
      setNotificationEmailSmtpPort(String(settingsData.notification_email_smtp_port));
      setNotificationEmailFrom(settingsData.notification_email_from);
      setNotificationEmailTo(settingsData.notification_email_to);
      setNotificationDingtalkEnabled(settingsData.notification_dingtalk_enabled);
      setNotificationDingtalkWebhookUrl(settingsData.notification_dingtalk_webhook_url);
      setNotificationWecomEnabled(settingsData.notification_wecom_enabled);
      setNotificationWecomWebhookUrl(settingsData.notification_wecom_webhook_url);
      setNotificationPoliciesText(JSON.stringify(settingsData.notification_policies ?? [], null, 2));
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
    setNotificationStatus(null);
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
      const parsedPolicies = JSON.parse(notificationPoliciesText || "[]") as Settings["notification_policies"];
      if (!Array.isArray(parsedPolicies)) {
        throw new Error("Notification policies must be a JSON array");
      }
      const updated = await api.put<Settings>(`/settings${settingsQuery}`, {
        app_name: appName,
        app_version: appVersion,
        log_level: logLevel,
        jenkins_url: jenkinsUrl,
        jenkins_user: jenkinsUser,
        ai_provider: aiProvider,
        ai_model_name: aiModelName,
        notification_default_channel: notificationDefaultChannel,
        notification_email_enabled: notificationEmailEnabled,
        notification_email_smtp_host: notificationEmailSmtpHost,
        notification_email_smtp_port: Number(notificationEmailSmtpPort || "25"),
        notification_email_from: notificationEmailFrom,
        notification_email_to: notificationEmailTo,
        notification_dingtalk_enabled: notificationDingtalkEnabled,
        notification_dingtalk_webhook_url: notificationDingtalkWebhookUrl,
        notification_wecom_enabled: notificationWecomEnabled,
        notification_wecom_webhook_url: notificationWecomWebhookUrl,
        notification_policies: parsedPolicies,
      });
      setSettings(updated);
      setSaveMessage(`Settings saved for ${selectedEnvironment} (revision ${updated.revision_number})`);
      setNotificationDefaultChannel(updated.notification_default_channel);
      setNotificationEmailEnabled(updated.notification_email_enabled);
      setNotificationEmailSmtpHost(updated.notification_email_smtp_host);
      setNotificationEmailSmtpPort(String(updated.notification_email_smtp_port));
      setNotificationEmailFrom(updated.notification_email_from);
      setNotificationEmailTo(updated.notification_email_to);
      setNotificationDingtalkEnabled(updated.notification_dingtalk_enabled);
      setNotificationDingtalkWebhookUrl(updated.notification_dingtalk_webhook_url);
      setNotificationWecomEnabled(updated.notification_wecom_enabled);
      setNotificationWecomWebhookUrl(updated.notification_wecom_webhook_url);
      setNotificationPoliciesText(JSON.stringify(updated.notification_policies ?? [], null, 2));
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
      setAiProvider(updated.ai_provider);
      setAiModelName(updated.ai_model_name);
      setNotificationDefaultChannel(updated.notification_default_channel);
      setNotificationEmailEnabled(updated.notification_email_enabled);
      setNotificationEmailSmtpHost(updated.notification_email_smtp_host);
      setNotificationEmailSmtpPort(String(updated.notification_email_smtp_port));
      setNotificationEmailFrom(updated.notification_email_from);
      setNotificationEmailTo(updated.notification_email_to);
      setNotificationDingtalkEnabled(updated.notification_dingtalk_enabled);
      setNotificationDingtalkWebhookUrl(updated.notification_dingtalk_webhook_url);
      setNotificationWecomEnabled(updated.notification_wecom_enabled);
      setNotificationWecomWebhookUrl(updated.notification_wecom_webhook_url);
      setNotificationPoliciesText(JSON.stringify(updated.notification_policies ?? [], null, 2));
      setRollbackMessage(`Rolled back ${selectedEnvironment} to revision ${revisionNumber}`);
      await loadHistory(selectedEnvironment);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Failed to rollback settings");
    }
  };

  const testNotification = async () => {
    setNotificationStatus(null);
    try {
      const result = await api.post<{ channel: string; status: string; message: string }>(
        `/notifications/test?environment=${encodeURIComponent(selectedEnvironment)}`,
        {
          channel: notificationDefaultChannel || undefined,
          subject: `AIQAHub ${selectedEnvironment} notification`,
          message: notificationTestMessage,
          target:
            notificationDefaultChannel === "email"
              ? notificationEmailTo
              : notificationDefaultChannel === "dingtalk"
                ? notificationDingtalkWebhookUrl
                : notificationWecomWebhookUrl,
          project_id: notificationTestProjectId || undefined,
          event_type: notificationTestEventType || undefined,
        },
      );
      setNotificationStatus(`${result.channel}: ${result.status}`);
    } catch (cause) {
      setNotificationStatus(cause instanceof Error ? cause.message : "Failed to send notification");
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
              <div className="field">
                <label>AI Provider</label>
                <input value={aiProvider} onChange={(event) => setAiProvider(event.target.value)} />
              </div>
              <div className="field">
                <label>AI Model</label>
                <input value={aiModelName} onChange={(event) => setAiModelName(event.target.value)} />
              </div>
              <div className="field">
                <label>Notification Channel</label>
                <input value={notificationDefaultChannel} onChange={(event) => setNotificationDefaultChannel(event.target.value)} />
              </div>
              <div className="field">
                <label>Enable Email</label>
                <input
                  checked={notificationEmailEnabled}
                  onChange={(event) => setNotificationEmailEnabled(event.target.checked)}
                  type="checkbox"
                />
              </div>
              <div className="field">
                <label>Email SMTP Host</label>
                <input value={notificationEmailSmtpHost} onChange={(event) => setNotificationEmailSmtpHost(event.target.value)} />
              </div>
              <div className="field">
                <label>Email SMTP Port</label>
                <input value={notificationEmailSmtpPort} onChange={(event) => setNotificationEmailSmtpPort(event.target.value)} />
              </div>
              <div className="field">
                <label>Email From</label>
                <input value={notificationEmailFrom} onChange={(event) => setNotificationEmailFrom(event.target.value)} />
              </div>
              <div className="field">
                <label>Email To</label>
                <input value={notificationEmailTo} onChange={(event) => setNotificationEmailTo(event.target.value)} />
              </div>
              <div className="field">
                <label>Enable DingTalk</label>
                <input
                  checked={notificationDingtalkEnabled}
                  onChange={(event) => setNotificationDingtalkEnabled(event.target.checked)}
                  type="checkbox"
                />
              </div>
              <div className="field">
                <label>DingTalk Webhook</label>
                <input value={notificationDingtalkWebhookUrl} onChange={(event) => setNotificationDingtalkWebhookUrl(event.target.value)} />
              </div>
              <div className="field">
                <label>Enable WeCom</label>
                <input
                  checked={notificationWecomEnabled}
                  onChange={(event) => setNotificationWecomEnabled(event.target.checked)}
                  type="checkbox"
                />
              </div>
              <div className="field">
                <label>WeCom Webhook</label>
                <input value={notificationWecomWebhookUrl} onChange={(event) => setNotificationWecomWebhookUrl(event.target.value)} />
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
              <div className="list-item">
                <div>
                  <div>AI Provider</div>
                  <div className="subtle">{settings.ai_provider}</div>
                </div>
                <span className="badge ok">{settings.ai_model_name}</span>
              </div>
              <div className="list-item">
                <div>
                  <div>AI Fallback Policy</div>
                  <div className="subtle">OpenAI-compatible failures fall back to mock provider</div>
                </div>
                <span className="badge warn">enabled</span>
              </div>
              <div className="list-item">
                <div>
                  <div>Notification Channel</div>
                  <div className="subtle">{settings.notification_default_channel}</div>
                </div>
                <span className="badge ok">{settings.notification_default_channel}</span>
              </div>
              <div className="list-item">
                <div>
                  <div>Notification Targets</div>
                  <div className="subtle">
                    Email: {settings.notification_email_to || "-"} · DingTalk: {settings.notification_dingtalk_webhook_url || "-"} · WeCom:{" "}
                    {settings.notification_wecom_webhook_url || "-"}
                  </div>
                </div>
                <span className="badge ok">configured</span>
              </div>
            </div>
            <div className="field" style={{ marginTop: 16 }}>
              <label>Notification Policies (JSON array)</label>
              <textarea
                rows={10}
                value={notificationPoliciesText}
                onChange={(event) => setNotificationPoliciesText(event.target.value)}
                style={{ width: "100%", fontFamily: "monospace" }}
              />
              <div className="subtle">Global/default policies should use scope_type=global; project overrides use scope_type=project.</div>
            </div>
            <div className="page-actions" style={{ marginTop: 16 }}>
              <div className="field" style={{ flex: 1 }}>
                <label>Notification Test Message</label>
                <input value={notificationTestMessage} onChange={(event) => setNotificationTestMessage(event.target.value)} />
              </div>
              <div className="field">
                <label>Test Project</label>
                <input value={notificationTestProjectId} onChange={(event) => setNotificationTestProjectId(event.target.value)} />
              </div>
              <div className="field">
                <label>Test Event</label>
                <input value={notificationTestEventType} onChange={(event) => setNotificationTestEventType(event.target.value)} />
              </div>
              <button className="primary-button" type="button" onClick={() => void testNotification()}>
                Test Notification
              </button>
            </div>
            {notificationStatus ? <div className="subtle" style={{ marginTop: 12 }}>{notificationStatus}</div> : null}
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
                    <div className="subtle">
                      AI: {entry.ai_provider} / {entry.ai_model_name}
                    </div>
                    <div className="subtle">
                      Notify: {entry.notification_default_channel} · email={entry.notification_email_enabled ? "on" : "off"} · dingtalk=
                      {entry.notification_dingtalk_enabled ? "on" : "off"} · wecom={entry.notification_wecom_enabled ? "on" : "off"}
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
