from app.core.config import get_settings
from app.schemas.settings import SettingsRead
from app.services.base import BaseService


class SettingsService(BaseService):
    @staticmethod
    def _mask(value: str) -> str:
        if "://" not in value:
            return value
        scheme, rest = value.split("://", 1)
        if "@" in rest:
            return f"{scheme}://***@{rest.split('@', 1)[1]}"
        return value

    def get_settings(self) -> SettingsRead:
        settings = get_settings()
        return SettingsRead(
            app_name=settings.app_name,
            app_version=settings.app_version,
            log_level=settings.log_level,
            database_url=self._mask(settings.database_url),
            redis_url=self._mask(settings.redis_url),
            jenkins_url=settings.jenkins_url,
            jenkins_user=settings.jenkins_user,
        )
