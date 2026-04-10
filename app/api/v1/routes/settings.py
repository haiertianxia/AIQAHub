from fastapi import APIRouter, Query

from app.schemas.settings import SettingsHistoryEntry, SettingsRead, SettingsRollback, SettingsUpdate
from app.services.settings_service import SettingsService

router = APIRouter()
service = SettingsService()


@router.get("", response_model=SettingsRead)
def get_settings(environment: str | None = Query(default=None)) -> SettingsRead:
    return service.get_settings(environment)


@router.put("", response_model=SettingsRead)
def update_settings(payload: SettingsUpdate, environment: str | None = Query(default=None)) -> SettingsRead:
    return service.update_settings(payload, environment)


@router.get("/history", response_model=list[SettingsHistoryEntry])
def get_settings_history(environment: str | None = Query(default=None)) -> list[SettingsHistoryEntry]:
    return service.list_history(environment)


@router.post("/rollback", response_model=SettingsRead)
def rollback_settings(payload: SettingsRollback) -> SettingsRead:
    return service.rollback_settings(payload)
