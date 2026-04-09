import json
from pathlib import Path

from app.core.config import get_settings
from app.schemas.settings import SettingsRead, SettingsUpdate
from app.services.base import BaseService


class SettingsService(BaseService):
    overrides_path = Path("var/settings_overrides.json")

    @staticmethod
    def _mask(value: str) -> str:
        if "://" not in value:
            return value
        scheme, rest = value.split("://", 1)
        if "@" in rest:
            return f"{scheme}://***@{rest.split('@', 1)[1]}"
        return value

    def _load_overrides(self) -> dict:
        if not self.overrides_path.exists():
            return {}
        try:
            return json.loads(self.overrides_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _save_overrides(self, overrides: dict) -> None:
        self.overrides_path.parent.mkdir(parents=True, exist_ok=True)
        self.overrides_path.write_text(json.dumps(overrides, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")

    def get_settings(self) -> SettingsRead:
        settings = get_settings()
        overrides = self._load_overrides()
        return SettingsRead(
            app_name=overrides.get("app_name", settings.app_name),
            app_version=overrides.get("app_version", settings.app_version),
            log_level=overrides.get("log_level", settings.log_level),
            database_url=self._mask(settings.database_url),
            redis_url=self._mask(settings.redis_url),
            jenkins_url=overrides.get("jenkins_url", settings.jenkins_url),
            jenkins_user=overrides.get("jenkins_user", settings.jenkins_user),
        )

    def update_settings(self, payload: SettingsUpdate) -> SettingsRead:
        settings = get_settings()
        overrides = self._load_overrides()
        for key, value in payload.model_dump(exclude_none=True).items():
            overrides[key] = value
        self._save_overrides(overrides)
        return self.get_settings()
