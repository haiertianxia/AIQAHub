from fastapi import APIRouter
from app.schemas.settings import SettingsRead, SettingsUpdate
from app.services.settings_service import SettingsService

router = APIRouter()
service = SettingsService()


@router.get("", response_model=SettingsRead)
def get_settings() -> SettingsRead:
    return service.get_settings()


@router.put("", response_model=SettingsRead)
def update_settings(payload: SettingsUpdate) -> SettingsRead:
    return service.update_settings(payload)
