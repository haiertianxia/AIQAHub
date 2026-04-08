from fastapi import APIRouter

from app.schemas.settings import SettingsRead
from app.services.settings_service import SettingsService

router = APIRouter()
service = SettingsService()


@router.get("", response_model=SettingsRead)
def get_settings() -> SettingsRead:
    return service.get_settings()
