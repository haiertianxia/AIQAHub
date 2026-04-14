import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { Highlight } from "../components/Highlight";
import { PageState } from "../components/PageState";
import { PaginationControls } from "../components/PaginationControls";
import { QueryToolbar } from "../components/QueryToolbar";
import { Section } from "../components/Section";
import {
  api,
  type GovernanceEvent,
  type GovernanceEventDetail,
  type GovernanceEventKind,
  type GovernanceOverview,
} from "../lib/api";

const governanceKinds: Array<{ label: string; value: GovernanceEventKind | "" }> = [
  { label: "All types", value: "" },
  { label: "Asset change", value: "asset_change" },
  { label: "Asset block", value: "asset_block" },
  { label: "Gate change", value: "gate_change" },
  { label: "Gate fail", value: "gate_fail" },
  { label: "Settings update", value: "settings_update" },
  { label: "Settings rollback", value: "settings_rollback" },
  { label: "Connector status", value: "connector_status" },
  { label: "Notification send", value: "notification_send" },
  { label: "Notification test", value: "notification_test" },
  { label: "Notification skip", value: "notification_skip" },
  { label: "Notification fallback", value: "notification_fallback" },
  { label: "Audit event", value: "audit_event" },
];

const notificationKinds: Array<{ label: string; value: GovernanceEventKind | "" }> = [
  { label: "All notification", value: "" },
  { label: "Send", value: "notification_send" },
  { label: "Test", value: "notification_test" },
  { label: "Skip", value: "notification_skip" },
  { label: "Fallback", value: "notification_fallback" },
];

const notificationStatusKinds: Array<{ label: string; value: string }> = [
  { label: "All status", value: "" },
  { label: "Success", value: "success" },
  { label: "Failed", value: "failed" },
  { label: "Skipped", value: "skipped" },
];

function severityTone(severity: GovernanceEvent["severity"]) {
  if (severity === "error" || severity === "blocked") {
    return "fail";
  }
  if (severity === "warn") {
    return "warn";
  }
  return "ok";
}

function relatedPage(event: GovernanceEventDetail): string | null {
  switch (event.kind) {
    case "asset_change":
    case "asset_block":
      return "/assets";
    case "gate_change":
    case "gate_fail":
      return "/gates";
    case "settings_update":
    case "settings_rollback":
      return "/settings";
    case "connector_status":
      return "/settings";
    case "audit_event":
      return "/audit";
    default:
      return null;
  }
}

function eventSummary(event: GovernanceEvent): string {
  const parts = [event.target_type ?? event.source_type, event.target_id ?? event.source_id];
  if (event.project_id) {
    parts.push(event.project_id);
  }
  if (event.environment) {
    parts.push(event.environment);
  }
  if (event.channel) {
    parts.push(`channel=${event.channel}`);
  }
  return parts.filter(Boolean).join(" · ");
}

function asRecord(value: unknown): Record<string, unknown> {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}

function extractJumpLinks(event: GovernanceEventDetail): Array<{ label: string; to: string }> {
  const links: Array<{ label: string; to: string }> = [];
  const addLink = (label: string, to: string) => {
    if (!links.some((item) => item.label === label && item.to === to)) {
      links.push({ label, to });
    }
  };

  const raw = asRecord(event.raw);
  const requestJson = asRecord(raw.request_json);
  const responseJson = asRecord(raw.response_json);
  const requestMeta = asRecord(requestJson.metadata);
  const responseMeta = asRecord(responseJson.metadata);
  const metadataKind = String(requestMeta.kind ?? responseMeta.kind ?? "").trim().toLowerCase();
  const metadataExecutionId =
    metadataKind === "execution_failure" || metadataKind === "gate_failure"
      ? String(requestMeta.execution_id ?? responseMeta.execution_id ?? "").trim()
      : "";
  const directExecutionId = event.target_type === "execution" ? String(event.target_id ?? "").trim() : "";
  const executionId = directExecutionId || metadataExecutionId;
  const policyScopeType = String(event.policy_scope_type ?? "").trim().toLowerCase();
  const settingsPath = event.environment
    ? `/settings?environment=${encodeURIComponent(event.environment)}`
    : "/settings";

  if (executionId) {
    addLink("Open execution", `/executions/${executionId}`);
  }
  if (event.target_type === "quality_rule" || metadataKind === "gate_failure") {
    addLink("Open gates", "/gates");
  }
  if (event.target_type === "settings" || policyScopeType) {
    addLink("Open settings", settingsPath);
  }

  const pageLink = relatedPage(event);
  if (pageLink) {
    addLink("Open related page", pageLink);
  }

  return links;
}

export function GovernancePage() {
  const [overview, setOverview] = useState<GovernanceOverview | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(true);
  const [overviewError, setOverviewError] = useState<string | null>(null);

  const [events, setEvents] = useState<GovernanceEvent[]>([]);
  const [eventsLoading, setEventsLoading] = useState(true);
  const [eventsError, setEventsError] = useState<string | null>(null);

  const [aiEvents, setAiEvents] = useState<GovernanceEvent[]>([]);
  const [aiEventsLoading, setAiEventsLoading] = useState(true);
  const [aiEventsError, setAiEventsError] = useState<string | null>(null);

  const [notificationEvents, setNotificationEvents] = useState<GovernanceEvent[]>([]);
  const [notificationEventsLoading, setNotificationEventsLoading] = useState(true);
  const [notificationEventsError, setNotificationEventsError] = useState<string | null>(null);

  const [detail, setDetail] = useState<GovernanceEventDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const [kind, setKind] = useState<GovernanceEventKind | "">("");
  const [search, setSearch] = useState("");
  const [projectId, setProjectId] = useState("");
  const [environment, setEnvironment] = useState("");
  const [status, setStatus] = useState("");
  const [targetType, setTargetType] = useState("");
  const [channel, setChannel] = useState("");
  const [provider, setProvider] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const [notificationKind, setNotificationKind] = useState<GovernanceEventKind | "">("");
  const [notificationChannel, setNotificationChannel] = useState("");
  const [notificationProvider, setNotificationProvider] = useState("");
  const [notificationStatus, setNotificationStatus] = useState("");
  const [notificationSearch, setNotificationSearch] = useState("");
  const [notificationPage, setNotificationPage] = useState(1);
  const notificationPageSize = 8;

  useEffect(() => {
    let cancelled = false;
    const loadOverview = async () => {
      setOverviewLoading(true);
      try {
        const data = await api.get<GovernanceOverview>("/governance/overview");
        if (!cancelled) {
          setOverview(data);
          setOverviewError(null);
        }
      } catch (cause) {
        if (!cancelled) {
          setOverviewError(cause instanceof Error ? cause.message : "Failed to load governance overview.");
        }
      } finally {
        if (!cancelled) {
          setOverviewLoading(false);
        }
      }
    };
    void loadOverview();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    const loadEvents = async () => {
      setEventsLoading(true);
      try {
        const query = new URLSearchParams();
        if (kind) query.set("kind", kind);
        if (search) query.set("search", search);
        if (projectId) query.set("project_id", projectId);
        if (environment) query.set("environment", environment);
        if (status) query.set("status", status);
        if (targetType) query.set("target_type", targetType);
        if (channel) query.set("channel", channel);
        if (provider) query.set("provider", provider);
        query.set("page", String(page));
        query.set("page_size", String(pageSize));
        const data = await api.get<GovernanceEvent[]>(`/governance/events?${query.toString()}`);
        if (!cancelled) {
          setEvents(data);
          setEventsError(null);
        }
      } catch (cause) {
        if (!cancelled) {
          setEventsError(cause instanceof Error ? cause.message : "Failed to load governance events.");
        }
      } finally {
        if (!cancelled) {
          setEventsLoading(false);
        }
      }
    };
    void loadEvents();
    return () => {
      cancelled = true;
    };
  }, [kind, search, projectId, environment, status, targetType, channel, provider, page]);

  useEffect(() => {
    let cancelled = false;
    const loadNotificationEvents = async () => {
      setNotificationEventsLoading(true);
      try {
        const query = new URLSearchParams();
        if (notificationKind) {
          query.set("kind", notificationKind);
        } else {
          query.set("kind_prefix", "notification_");
        }
        if (notificationSearch) query.set("search", notificationSearch);
        if (notificationChannel) query.set("channel", notificationChannel);
        if (notificationProvider) query.set("provider", notificationProvider);
        if (notificationStatus) query.set("status", notificationStatus);
        query.set("page", String(notificationPage));
        query.set("page_size", String(notificationPageSize));
        const data = await api.get<GovernanceEvent[]>(`/governance/events?${query.toString()}`);
        if (!cancelled) {
          setNotificationEvents(data);
          setNotificationEventsError(null);
        }
      } catch (cause) {
        if (!cancelled) {
          setNotificationEventsError(cause instanceof Error ? cause.message : "Failed to load notification events.");
        }
      } finally {
        if (!cancelled) {
          setNotificationEventsLoading(false);
        }
      }
    };
    void loadNotificationEvents();
    return () => {
      cancelled = true;
    };
  }, [notificationKind, notificationSearch, notificationChannel, notificationProvider, notificationStatus, notificationPage]);

  useEffect(() => {
    let cancelled = false;
    const loadAiEvents = async () => {
      setAiEventsLoading(true);
      try {
        const query = new URLSearchParams();
        query.set("kind", "audit_event");
        query.set("target_type", "ai_insight");
        query.set("page", "1");
        query.set("page_size", "5");
        const data = await api.get<GovernanceEvent[]>(`/governance/events?${query.toString()}`);
        if (!cancelled) {
          setAiEvents(data);
          setAiEventsError(null);
        }
      } catch (cause) {
        if (!cancelled) {
          setAiEventsError(cause instanceof Error ? cause.message : "Failed to load AI governance events.");
        }
      } finally {
        if (!cancelled) {
          setAiEventsLoading(false);
        }
      }
    };
    void loadAiEvents();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const combined = [...notificationEvents, ...events, ...aiEvents];
    if (combined.length === 0) {
      setSelectedEventId(null);
      setDetail(null);
      return;
    }
    if (!selectedEventId || !combined.some((event) => event.id === selectedEventId)) {
      setSelectedEventId(combined[0].id);
    }
  }, [events, aiEvents, notificationEvents, selectedEventId]);

  useEffect(() => {
    if (!selectedEventId) {
      setDetail(null);
      setDetailError(null);
      return;
    }
    let cancelled = false;
    const loadDetail = async () => {
      setDetailLoading(true);
      try {
        const data = await api.get<GovernanceEventDetail>(`/governance/events/${selectedEventId}`);
        if (!cancelled) {
          setDetail(data);
          setDetailError(null);
        }
      } catch (cause) {
        if (!cancelled) {
          setDetailError(cause instanceof Error ? cause.message : "Failed to load governance event detail.");
          setDetail(null);
        }
      } finally {
        if (!cancelled) {
          setDetailLoading(false);
        }
      }
    };
    void loadDetail();
    return () => {
      cancelled = true;
    };
  }, [selectedEventId]);

  const applyFilters = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPage(1);
  };

  const clearFilters = () => {
    setKind("");
    setSearch("");
    setProjectId("");
    setEnvironment("");
    setStatus("");
    setTargetType("");
    setChannel("");
    setProvider("");
    setPage(1);
  };

  const applyNotificationFilters = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setNotificationPage(1);
  };

  const clearNotificationFilters = () => {
    setNotificationKind("");
    setNotificationSearch("");
    setNotificationChannel("");
    setNotificationProvider("");
    setNotificationStatus("");
    setNotificationPage(1);
  };

  const selectedEvent = detail ?? null;

  return (
    <Section
      title="治理中心"
      description="统一查看资产、门禁、配置、连接器、通知和审计信号"
      action={
        <div className="page-actions">
          <Link className="badge" to="/audit">
            Audit
          </Link>
          <button className="badge" type="button" onClick={clearFilters}>
            Reset
          </button>
        </div>
      }
    >
      {overviewLoading ? <PageState kind="loading" message="Loading governance overview..." /> : null}
      {overviewError ? <PageState kind="error" message={overviewError} /> : null}

      {overview ? (
        <div className="grid cols-3">
          {[
            { label: "AI Provider", value: `${overview.ai_provider} / ${overview.ai_model_name}`, tone: "ok" },
            { label: "AI Fallbacks", value: overview.ai_fallback_count, tone: overview.ai_fallback_count > 0 ? "warn" : "ok" },
            { label: "Notification Send", value: overview.notification_send_count, tone: "ok", kind: "notification_send" as GovernanceEventKind },
            { label: "Notification Fail", value: overview.notification_failed_count, tone: overview.notification_failed_count > 0 ? "fail" : "ok", status: "failed" },
            { label: "Notification Skip", value: overview.notification_skip_count, tone: "warn", kind: "notification_skip" as GovernanceEventKind },
            { label: "Notification Fallback", value: overview.notification_fallback_count, tone: "warn", kind: "notification_fallback" as GovernanceEventKind },
            { label: "Asset Blocks", value: overview.asset_block_count, tone: "warn", kind: "asset_block" as GovernanceEventKind },
            { label: "Gate Fails", value: overview.gate_fail_count, tone: "fail", kind: "gate_fail" as GovernanceEventKind },
            { label: "Settings Rollbacks", value: overview.settings_rollback_count, tone: "warn", kind: "settings_rollback" as GovernanceEventKind },
            { label: "Connector Errors", value: overview.connector_error_count, tone: "fail", kind: "connector_status" as GovernanceEventKind },
            { label: "Recent Audits", value: overview.recent_audit_count, tone: "ok", kind: "audit_event" as GovernanceEventKind },
          ].map((metric) => (
            <button
              key={metric.label}
              className="panel soft"
              type="button"
              onClick={() => {
                if (metric.kind) {
                  setKind(metric.kind);
                  setNotificationStatus("");
                  setPage(1);
                  return;
                }
                if ("status" in metric && metric.status) {
                  setNotificationKind("");
                  setNotificationStatus(metric.status);
                  setNotificationPage(1);
                }
              }}
              style={{ textAlign: "left", cursor: "pointer" }}
            >
              <div className={`badge ${metric.tone}`.trim()}>{metric.label}</div>
              <div className="metric" style={{ marginTop: 10 }}>
                {metric.value}
              </div>
              <div className="subtle">Last 24 hours · {overview.window_start} → {overview.window_end}</div>
            </button>
          ))}
        </div>
      ) : null}

      <div className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel soft">
          <div className="row space-between">
            <h4 style={{ margin: 0 }}>Notification Events</h4>
            <span className="badge ok">{notificationEvents.length} events</span>
          </div>
          <QueryToolbar onSubmit={applyNotificationFilters}>
            <div className="page-actions">
              <div className="field">
                <label>Kind</label>
                <select value={notificationKind} onChange={(event) => setNotificationKind(event.target.value as GovernanceEventKind | "")}>
                  {notificationKinds.map((option) => (
                    <option key={option.label} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Channel</label>
                <input value={notificationChannel} onChange={(event) => setNotificationChannel(event.target.value)} placeholder="dingtalk" />
              </div>
            <div className="field">
              <label>Provider</label>
              <input value={notificationProvider} onChange={(event) => setNotificationProvider(event.target.value)} placeholder="wecom" />
            </div>
              <div className="field">
                <label>Status</label>
                <select value={notificationStatus} onChange={(event) => setNotificationStatus(event.target.value)}>
                  {notificationStatusKinds.map((option) => (
                    <option key={option.label} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            <div className="field">
              <label>Search</label>
              <input value={notificationSearch} onChange={(event) => setNotificationSearch(event.target.value)} placeholder="token or project" />
              </div>
              <button className="primary-button" type="submit">
                Filter
              </button>
              <button className="badge" type="button" onClick={clearNotificationFilters}>
                Clear
              </button>
            </div>
          </QueryToolbar>
          {notificationEventsLoading ? <PageState kind="loading" message="Loading notification events..." /> : null}
          {notificationEventsError ? <PageState kind="error" message={notificationEventsError} /> : null}
          {!notificationEventsLoading && !notificationEventsError && notificationEvents.length === 0 ? (
            <PageState kind="empty" message="No notification events match current filters." />
          ) : null}
          {!notificationEventsLoading && !notificationEventsError && notificationEvents.length > 0 ? (
            <>
              <div className="list" style={{ marginTop: 12 }}>
                {notificationEvents.map((event) => (
                  <div
                    key={event.id}
                    className="list-item"
                    role="button"
                    tabIndex={0}
                    onClick={() => setSelectedEventId(event.id)}
                    onKeyDown={(keyboardEvent) => {
                      if (keyboardEvent.key === "Enter" || keyboardEvent.key === " ") {
                        setSelectedEventId(event.id);
                      }
                    }}
                    style={{
                      cursor: "pointer",
                      border: selectedEventId === event.id ? "1px solid rgba(255,255,255,0.35)" : undefined,
                    }}
                  >
                    <div>
                      <div className="row" style={{ gap: 8, alignItems: "center" }}>
                        <Highlight text={event.title} query={notificationSearch} />
                        <span className={`badge ${severityTone(event.severity)}`.trim()}>{event.kind}</span>
                      </div>
                      <div className="subtle" style={{ marginTop: 4 }}>
                        {event.channel ?? "-"} · {event.provider ?? "-"} · {event.status ?? "-"}
                      </div>
                      <div className="subtle" style={{ marginTop: 4 }}>
                        <Highlight text={eventSummary(event)} query={notificationSearch} />
                      </div>
                    </div>
                    <span className="badge ok">{event.timestamp}</span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 16 }}>
                <PaginationControls
                  page={notificationPage}
                  pageSize={notificationPageSize}
                  itemCount={notificationEvents.length}
                  onPrevious={() => setNotificationPage((current) => Math.max(current - 1, 1))}
                  onNext={() => setNotificationPage((current) => current + 1)}
                />
              </div>
            </>
          ) : null}
        </div>

        <div className="panel soft">
          <div className="row space-between">
            <h4 style={{ margin: 0 }}>AI Events</h4>
            <span className="badge ok">{aiEvents.length} events</span>
          </div>
          {aiEventsLoading ? <PageState kind="loading" message="Loading AI governance events..." /> : null}
          {aiEventsError ? <PageState kind="error" message={aiEventsError} /> : null}
          {!aiEventsLoading && !aiEventsError && aiEvents.length === 0 ? (
            <PageState kind="empty" message="No AI governance events yet." />
          ) : null}
          {!aiEventsLoading && !aiEventsError && aiEvents.length > 0 ? (
            <div className="list" style={{ marginTop: 12 }}>
              {aiEvents.map((event) => (
                <div
                  key={event.id}
                  className="list-item"
                  role="button"
                  tabIndex={0}
                  onClick={() => setSelectedEventId(event.id)}
                  onKeyDown={(keyboardEvent) => {
                    if (keyboardEvent.key === "Enter" || keyboardEvent.key === " ") {
                      setSelectedEventId(event.id);
                    }
                  }}
                  style={{
                    cursor: "pointer",
                    border: selectedEventId === event.id ? "1px solid rgba(255,255,255,0.35)" : undefined,
                  }}
                >
                  <div>
                    <div className="row" style={{ gap: 8, alignItems: "center" }}>
                      <Highlight text={event.title} query={search} />
                      <span className={`badge ${severityTone(event.severity)}`.trim()}>{event.severity}</span>
                    </div>
                    <div className="subtle" style={{ marginTop: 4 }}>
                      <Highlight text={event.description ?? event.source_id} query={search} />
                    </div>
                    <div className="subtle" style={{ marginTop: 4 }}>
                      {event.timestamp}
                    </div>
                  </div>
                  <span className="badge ok">{event.target_id ?? event.source_id}</span>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      <div style={{ marginTop: 16 }}>
        <QueryToolbar onSubmit={applyFilters}>
          <div className="page-actions">
            <div className="field">
              <label>Type</label>
              <select value={kind} onChange={(event) => setKind(event.target.value as GovernanceEventKind | "")}>
                {governanceKinds.map((option) => (
                  <option key={option.label} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label>Search</label>
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="title or id" />
            </div>
            <div className="field">
              <label>Project</label>
              <input value={projectId} onChange={(event) => setProjectId(event.target.value)} placeholder="proj_demo" />
            </div>
            <div className="field">
              <label>Environment</label>
              <input value={environment} onChange={(event) => setEnvironment(event.target.value)} placeholder="sit" />
            </div>
            <div className="field">
              <label>Status</label>
              <input value={status} onChange={(event) => setStatus(event.target.value)} placeholder="failed" />
            </div>
            <div className="field">
              <label>Target Type</label>
              <input value={targetType} onChange={(event) => setTargetType(event.target.value)} placeholder="execution" />
            </div>
            <div className="field">
              <label>Channel</label>
              <input value={channel} onChange={(event) => setChannel(event.target.value)} placeholder="dingtalk" />
            </div>
            <div className="field">
              <label>Provider</label>
              <input value={provider} onChange={(event) => setProvider(event.target.value)} placeholder="wecom" />
            </div>
            <button className="primary-button" type="submit">
              Filter
            </button>
            <button className="badge" type="button" onClick={clearFilters}>
              Clear
            </button>
          </div>
        </QueryToolbar>
      </div>

      <div className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel soft">
          <div className="row space-between">
            <h4 style={{ margin: 0 }}>Event Stream</h4>
            <span className="badge ok">{events.length} events</span>
          </div>
          {eventsLoading ? <PageState kind="loading" message="Loading governance events..." /> : null}
          {eventsError ? <PageState kind="error" message={eventsError} /> : null}
          {!eventsLoading && !eventsError && events.length === 0 ? (
            <PageState kind="empty" message="No governance events match the current filters." />
          ) : null}
          {!eventsLoading && !eventsError && events.length > 0 ? (
            <>
              <div className="list" style={{ marginTop: 12 }}>
                {events.map((event) => (
                  <div
                    key={event.id}
                    className="list-item"
                    role="button"
                    tabIndex={0}
                    onClick={() => setSelectedEventId(event.id)}
                    onKeyDown={(keyboardEvent) => {
                      if (keyboardEvent.key === "Enter" || keyboardEvent.key === " ") {
                        setSelectedEventId(event.id);
                      }
                    }}
                    style={{
                      cursor: "pointer",
                      border: selectedEventId === event.id ? "1px solid rgba(255,255,255,0.35)" : undefined,
                    }}
                  >
                    <div>
                      <div className="row" style={{ gap: 8, alignItems: "center" }}>
                        <Highlight text={event.title} query={search} />
                        <span className={`badge ${severityTone(event.severity)}`.trim()}>{event.kind}</span>
                      </div>
                      <div className="subtle" style={{ marginTop: 4 }}>
                        <Highlight text={eventSummary(event)} query={search} />
                      </div>
                      <div className="subtle" style={{ marginTop: 4 }}>
                        {event.timestamp}
                      </div>
                    </div>
                    <div className="row" style={{ gap: 8 }}>
                      {event.status ? <span className="badge">{event.status}</span> : null}
                      <span className={`badge ${severityTone(event.severity)}`.trim()}>{event.severity}</span>
                    </div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 16 }}>
                <PaginationControls
                  page={page}
                  pageSize={pageSize}
                  itemCount={events.length}
                  onPrevious={() => setPage((current) => Math.max(current - 1, 1))}
                  onNext={() => setPage((current) => current + 1)}
                />
              </div>
            </>
          ) : null}
        </div>

        <div className="panel soft">
          <div className="row space-between">
            <h4 style={{ margin: 0 }}>Detail Drawer</h4>
            {selectedEvent ? <span className="badge ok">{selectedEvent.kind}</span> : null}
          </div>
          {detailLoading ? <PageState kind="loading" message="Loading governance event detail..." /> : null}
          {detailError ? <PageState kind="error" message={detailError} /> : null}
          {!detailLoading && !detailError && selectedEvent ? (
            <>
              <div className="panel" style={{ marginTop: 12 }}>
                <div className="row space-between">
                  <div>
                    <div className="metric">{selectedEvent.title}</div>
                    <div className="subtle">{selectedEvent.description ?? "No description"}</div>
                  </div>
                  <span className={`badge ${severityTone(selectedEvent.severity)}`.trim()}>{selectedEvent.severity}</span>
                </div>
                <div className="subtle" style={{ marginTop: 8 }}>
                  {selectedEvent.timestamp}
                </div>
                <div className="subtle" style={{ marginTop: 8 }}>
                  Source: {selectedEvent.source_type} · {selectedEvent.source_id}
                </div>
                <div className="subtle">Target: {selectedEvent.target_type ?? "-"} · {selectedEvent.target_id ?? "-"}</div>
                <div className="subtle">
                  Project: {selectedEvent.project_id ?? "-"} · Environment: {selectedEvent.environment ?? "-"}
                </div>
                <div className="subtle">Status: {selectedEvent.status ?? "-"}</div>
                <div className="subtle">
                  Channel: {selectedEvent.channel ?? "-"} · Provider: {selectedEvent.provider ?? "-"}
                </div>
                <div className="subtle">
                  Policy: {selectedEvent.policy_scope_type ?? "-"} · {selectedEvent.policy_scope_id ?? "-"}
                </div>
                <div className="subtle">
                  Fallback: {selectedEvent.fallback_from ?? "-"} · {selectedEvent.fallback_reason ?? "-"}
                </div>
                <div className="row" style={{ marginTop: 12, gap: 8, flexWrap: "wrap" }}>
                  {extractJumpLinks(selectedEvent).map((jump) => (
                    <Link key={`${jump.label}:${jump.to}`} className="badge" to={jump.to}>
                      {jump.label}
                    </Link>
                  ))}
                </div>
              </div>
              <div className="panel" style={{ marginTop: 12 }}>
                <h4 style={{ margin: 0 }}>Routing Metadata</h4>
                <pre style={{ marginTop: 12, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                  {JSON.stringify(
                    {
                      event_type: selectedEvent.event_type,
                      channel: selectedEvent.channel,
                      provider: selectedEvent.provider,
                      target: selectedEvent.target,
                      policy_scope_type: selectedEvent.policy_scope_type,
                      policy_scope_id: selectedEvent.policy_scope_id,
                      fallback_from: selectedEvent.fallback_from,
                      fallback_reason: selectedEvent.fallback_reason,
                    },
                    null,
                    2
                  )}
                </pre>
              </div>
              <div className="panel" style={{ marginTop: 12 }}>
                <h4 style={{ margin: 0 }}>Raw Event</h4>
                <pre style={{ marginTop: 12, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                  {JSON.stringify(selectedEvent.raw, null, 2)}
                </pre>
              </div>
            </>
          ) : null}
          {!detailLoading && !detailError && !selectedEvent ? (
            <PageState kind="empty" message="Select a governance event to inspect its details." />
          ) : null}
        </div>
      </div>
    </Section>
  );
}
