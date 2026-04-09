from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.asset import AssetCreate, AssetRead
from app.db.session import get_db
from app.services.asset_service import AssetService

router = APIRouter()
service = AssetService()


@router.get("", response_model=list[AssetRead])
def list_assets(db: Session = Depends(get_db)) -> list[AssetRead]:
    return service.list_assets(db)


@router.post("", response_model=AssetRead)
def create_asset(payload: AssetCreate, db: Session = Depends(get_db)) -> AssetRead:
    return service.create_asset(db, payload)
