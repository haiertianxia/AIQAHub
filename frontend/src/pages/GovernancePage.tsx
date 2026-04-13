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
  { label: "Audit event", value: "audit_event" },
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
  return parts.filter(Boolean).join(" · ");
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
  const [page, setPage] = useState(1);
  const pageSize = 10;

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
        if (kind) {
          query.set("kind", kind);
        }
        if (search) {
          query.set("search", search);
        }
        if (projectId) {
          query.set("project_id", projectId);
        }
        if (environment) {
          query.set("environment", environment);
        }
        if (status) {
          query.set("status", status);
        }
        if (targetType) {
          query.set("target_type", targetType);
        }
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
  }, [kind, search, projectId, environment, status, targetType, page]);

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
    if (events.length === 0) {
      setSelectedEventId(null);
      setDetail(null);
      return;
    }
    if (!selectedEventId || !events.some((event) => event.id === selectedEventId)) {
      setSelectedEventId(events[0].id);
    }
  }, [events, selectedEventId]);

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

  const clearFilters = async () => {
    setKind("");
    setSearch("");
    setProjectId("");
    setEnvironment("");
    setStatus("");
    setTargetType("");
    setPage(1);
  };

  const selectedEvent = detail ?? null;

  return (
    <Section
      title="治理中心"
      description="统一查看资产、门禁、配置、连接器和审计信号"
      action={
        <div className="page-actions">
          <Link className="badge" to="/audit">
            Audit
          </Link>
          <button className="badge" type="button" onClick={() => void clearFilters()}>
            Reset
          </button>
        </div>
      }
    >
      {overviewLoading ? <PageState kind="loading" message="Loading governance overview..." /> : null}
      {overviewError ? <PageState kind="error" message={overviewError} /> : null}
      {overview ? (
        <>
          <div className="grid cols-3">
            {[
              { label: "AI Provider", value: `${overview.ai_provider} / ${overview.ai_model_name}`, tone: "ok" },
              { label: "AI Fallbacks", value: overview.ai_fallback_count, tone: overview.ai_fallback_count > 0 ? "warn" : "ok" },
              { label: "Asset Blocks", value: overview.asset_block_count, tone: "warn" },
              { label: "Gate Fails", value: overview.gate_fail_count, tone: "fail" },
              { label: "Settings Rollbacks", value: overview.settings_rollback_count, tone: "warn" },
              { label: "Connector Errors", value: overview.connector_error_count, tone: "fail" },
              { label: "Recent Audits", value: overview.recent_audit_count, tone: "ok" },
            ].map((metric) => (
              <button
                key={metric.label}
                className="panel soft"
                type="button"
                onClick={() => {
                  if (metric.label === "Asset Blocks") setKind("asset_block");
                  if (metric.label === "Gate Fails") setKind("gate_fail");
                  if (metric.label === "Settings Rollbacks") setKind("settings_rollback");
                  if (metric.label === "Connector Errors") setKind("connector_status");
                  if (metric.label === "Recent Audits") setKind("audit_event");
                  setPage(1);
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
        </>
      ) : null}

      {overview ? (
        <div className="grid cols-2" style={{ marginTop: 16 }}>
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
                {aiEvents.map((event) => {
                  const responseJson = event.metadata?.response_json as Record<string, unknown> | undefined;
                  const fallbackFrom = typeof responseJson?.fallback_from === "string" ? responseJson.fallback_from : "";
                  const fallbackReason = typeof responseJson?.fallback_reason === "string" ? responseJson.fallback_reason : "";
                  return (
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
                        {fallbackFrom ? (
                          <div className="subtle" style={{ marginTop: 4 }}>
                            Fallback from {fallbackFrom}
                            {fallbackReason ? ` · ${fallbackReason}` : ""}
                          </div>
                        ) : null}
                        <div className="subtle" style={{ marginTop: 4 }}>
                          {event.timestamp}
                        </div>
                      </div>
                      <span className="badge ok">{event.target_id ?? event.source_id}</span>
                    </div>
                  );
                })}
              </div>
            ) : null}
          </div>
          <div className="panel soft">
            <h4 style={{ margin: 0 }}>AI Governance Notes</h4>
            <div className="list" style={{ marginTop: 12 }}>
              <div className="list-item">
                <div>
                  <div>Configured Provider</div>
                  <div className="subtle">
                    {overview.ai_provider} / {overview.ai_model_name}
                  </div>
                </div>
                <span className="badge ok">{overview.ai_fallback_count} fallbacks</span>
              </div>
              <div className="list-item">
                <div>
                  <div>Fallback Policy</div>
                  <div className="subtle">OpenAI-compatible failures degrade to the deterministic mock provider.</div>
                </div>
                <span className="badge warn">enabled</span>
              </div>
              <div className="list-item">
                <div>
                  <div>Audit Trail</div>
                  <div className="subtle">Every AI analyze request writes an audit event and a history record.</div>
                </div>
                <span className="badge ok">recorded</span>
              </div>
            </div>
          </div>
        </div>
      ) : null}

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
            <button className="primary-button" type="submit">
              Filter
            </button>
            <button className="badge" type="button" onClick={() => void clearFilters()}>
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
                {relatedPage(selectedEvent) ? (
                  <div style={{ marginTop: 12 }}>
                    <Link className="badge" to={relatedPage(selectedEvent)!}>
                      Open related page
                    </Link>
                  </div>
                ) : null}
              </div>
              <div className="panel" style={{ marginTop: 12 }}>
                <h4 style={{ margin: 0 }}>Metadata</h4>
                <pre style={{ marginTop: 12, whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                  {JSON.stringify(selectedEvent.metadata, null, 2)}
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
