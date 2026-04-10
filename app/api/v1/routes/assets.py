from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.asset import AssetCreate, AssetLinkCreate, AssetLinkRead, AssetRead, AssetRevisionRead
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


@router.put("/{asset_id}", response_model=AssetRead)
def update_asset(asset_id: str, payload: AssetCreate, db: Session = Depends(get_db)) -> AssetRead:
    return service.update_asset(db, asset_id, payload)


@router.get("/{asset_id}/revisions", response_model=list[AssetRevisionRead])
def list_asset_revisions(asset_id: str, db: Session = Depends(get_db)) -> list[AssetRevisionRead]:
    return service.list_asset_revisions(db, asset_id)


@router.get("/{asset_id}/links", response_model=list[AssetLinkRead])
def list_asset_links(asset_id: str, db: Session = Depends(get_db)) -> list[AssetLinkRead]:
    return service.list_asset_links(db, asset_id)


@router.post("/{asset_id}/links", response_model=AssetLinkRead)
def create_asset_link(asset_id: str, payload: AssetLinkCreate, db: Session = Depends(get_db)) -> AssetLinkRead:
    return service.create_asset_link(db, asset_id, payload)


@router.delete("/{asset_id}/links/{link_id}", status_code=204)
def delete_asset_link(asset_id: str, link_id: str, db: Session = Depends(get_db)) -> None:
    service.delete_asset_link(db, asset_id, link_id)


@router.delete("/{asset_id}", response_model=AssetRead)
def delete_asset(asset_id: str, db: Session = Depends(get_db)) -> AssetRead:
    return service.delete_asset(db, asset_id)
