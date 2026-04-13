import json
from datetime import UTC, datetime
from pathlib import Path

from app.core.config import get_settings
from app.schemas.settings import (
    SettingsHistoryEntry,
    SettingsRead,
    SettingsRollback,
    SettingsUpdate,
)
from app.schemas.governance import GovernanceEventDetailRead, normalize_utc_timestamp, stable_governance_event_id
from app.services.base import BaseService


class SettingsService(BaseService):
    overrides_path = Path("var/settings_overrides.json")
    history_path = Path("var/settings_history.json")
    editable_keys = (
        "app_name",
        "app_version",
        "log_level",
        "jenkins_url",
        "jenkins_user",
        "ai_provider",
        "ai_model_name",
    )

    @staticmethod
    def _mask(value: str) -> str:
        if "://" not in value:
            return value
        scheme, rest = value.split("://", 1)
        if "@" in rest:
            return f"{scheme}://***@{rest.split('@', 1)[1]}"
        return value

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _normalize_environment(environment: str | None) -> str:
        settings = get_settings()
        return (environment or settings.app_env or "local").strip() or "local"

    def _load_json(self, path: Path, default: object) -> object:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return default

    def _save_json(self, path: Path, payload: object) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False),
            encoding="utf-8",
        )

    def _load_override_state(self) -> dict[str, dict[str, str]]:
        raw = self._load_json(self.overrides_path, {})
        if not isinstance(raw, dict):
            return {}
        if "environments" in raw and isinstance(raw["environments"], dict):
            environments = raw["environments"]
            return {key: value for key, value in environments.items() if isinstance(value, dict)}
        return {"__legacy__": raw}

    def _save_override_state(self, environments: dict[str, dict[str, str]]) -> None:
        payload = {"environments": environments}
        self._save_json(self.overrides_path, payload)

    def _load_history(self) -> list[dict[str, object]]:
        raw = self._load_json(self.history_path, [])
        if isinstance(raw, list):
            return [entry for entry in raw if isinstance(entry, dict)]
        return []

    def _save_history(self, history: list[dict[str, object]]) -> None:
        self._save_json(self.history_path, history)

    def _environment_overrides(self, environment: str | None) -> dict[str, str]:
        env = self._normalize_environment(environment)
        overrides = self._load_override_state()
        if env in overrides:
            return dict(overrides.get(env, {}))
        return dict(overrides.get("__legacy__", {}))

    def _revision_history(self, environment: str | None) -> list[dict[str, object]]:
        env = self._normalize_environment(environment)
        history = self._load_history()
        return [entry for entry in history if entry.get("environment") == env]

    def _next_revision_number(self, environment: str | None) -> int:
        revisions = self._revision_history(environment)
        if not revisions:
            return 1
        return max(int(entry.get("revision_number", 0)) for entry in revisions) + 1

    def _effective_settings(self, environment: str | None) -> tuple[str, int, SettingsRead]:
        env = self._normalize_environment(environment)
        settings = get_settings()
        overrides = self._environment_overrides(env)
        revision_number = self._revision_history(env)[-1]["revision_number"] if self._revision_history(env) else 0
        return (
            env,
            int(revision_number),
            SettingsRead(
                environment=env,
                revision_number=int(revision_number),
                app_name=overrides.get("app_name", settings.app_name),
                app_version=overrides.get("app_version", settings.app_version),
                log_level=overrides.get("log_level", settings.log_level),
                database_url=self._mask(settings.database_url),
                redis_url=self._mask(settings.redis_url),
                jenkins_url=overrides.get("jenkins_url", settings.jenkins_url),
                jenkins_user=overrides.get("jenkins_user", settings.jenkins_user),
                ai_provider=overrides.get("ai_provider", settings.ai_provider),
                ai_model_name=overrides.get("ai_model_name", settings.ai_model_name),
            ),
        )

    def _snapshot_from_payload(self, environment: str, revision_number: int, action: str, payload: dict[str, str]) -> dict[str, object]:
        settings = get_settings()
        return {
            "environment": environment,
            "revision_number": revision_number,
            "action": action,
            "app_name": payload.get("app_name", settings.app_name),
            "app_version": payload.get("app_version", settings.app_version),
            "log_level": payload.get("log_level", settings.log_level),
            "jenkins_url": payload.get("jenkins_url", settings.jenkins_url),
            "jenkins_user": payload.get("jenkins_user", settings.jenkins_user),
            "ai_provider": payload.get("ai_provider", settings.ai_provider),
            "ai_model_name": payload.get("ai_model_name", settings.ai_model_name),
            "updated_at": self._now(),
        }

    def _persist_revision(self, environment: str, action: str, overrides: dict[str, str]) -> SettingsRead:
        state = self._load_override_state()
        state[environment] = overrides
        self._save_override_state(state)

        revision_number = self._next_revision_number(environment)
        history = self._load_history()
        history.append(self._snapshot_from_payload(environment, revision_number, action, overrides))
        self._save_history(history)
        return self.get_settings(environment)

    def get_settings(self, environment: str | None = None) -> SettingsRead:
        _, _, current = self._effective_settings(environment)
        return current

    def list_history(self, environment: str | None = None) -> list[SettingsHistoryEntry]:
        env = self._normalize_environment(environment)
        revisions = self._revision_history(env)
        return [SettingsHistoryEntry.model_validate(entry) for entry in reversed(revisions)]

    def list_all_history(self) -> list[SettingsHistoryEntry]:
        history = [SettingsHistoryEntry.model_validate(entry) for entry in self._load_history()]
        return sorted(history, key=lambda entry: (entry.updated_at, entry.environment, entry.revision_number), reverse=True)

    def update_settings(self, payload: SettingsUpdate, environment: str | None = None) -> SettingsRead:
        env = self._normalize_environment(environment)
        overrides = self._environment_overrides(env)
        for key, value in payload.model_dump(exclude_none=True).items():
            overrides[key] = value
        return self._persist_revision(env, "update", overrides)

    def rollback_settings(self, payload: SettingsRollback) -> SettingsRead:
        env = self._normalize_environment(payload.environment)
        revisions = self._revision_history(env)
        target = next((entry for entry in revisions if int(entry.get("revision_number", 0)) == payload.revision_number), None)
        if target is None:
            raise ValueError(f"Revision {payload.revision_number} not found for environment {env}")

        overrides = {
            key: str(target[key])
            for key in self.editable_keys
            if key in target and target[key] is not None
        }
        return self._persist_revision(env, "rollback", overrides)

    def list_governance_events(self) -> list[GovernanceEventDetailRead]:
        events: list[GovernanceEventDetailRead] = []
        for entry in self.list_all_history():
            kind = "settings_rollback" if entry.action == "rollback" else "settings_update"
            severity = "warn" if kind == "settings_rollback" else "info"
            source_id = entry.governance_source_id()
            events.append(
                GovernanceEventDetailRead(
                    id=stable_governance_event_id(kind, "settings_history", source_id),
                    kind=kind,
                    source_type="settings_history",
                    source_id=source_id,
                    timestamp=normalize_utc_timestamp(entry.updated_at),
                    severity=severity,
                    target_type="settings",
                    target_id=entry.environment,
                    environment=entry.environment,
                    title=f"Settings {entry.action}",
                    description=f"env={entry.environment} revision={entry.revision_number}",
                    metadata={"revision_number": entry.revision_number},
                    raw=entry.model_dump(),
                )
            )
        return events
