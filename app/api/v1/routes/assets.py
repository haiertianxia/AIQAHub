from fastapi import APIRouter

from app.schemas.asset import AssetCreate, AssetRead
from app.services.asset_service import AssetService

router = APIRouter()
service = AssetService()


@router.get("", response_model=list[AssetRead])
def list_assets() -> list[AssetRead]:
    return service.list_assets()


@router.post("", response_model=AssetRead)
def create_asset(payload: AssetCreate) -> AssetRead:
    return service.create_asset(payload)

