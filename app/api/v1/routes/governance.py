from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.session import get_db
from app.schemas.governance import (
    GovernanceEventDetailRead,
    GovernanceEventKind,
    GovernanceEventRead,
    GovernanceOverviewRead,
)
from app.services.audit_service import AuditService

router = APIRouter()
service = AuditService()


@router.get("/overview", response_model=GovernanceOverviewRead)
def get_governance_overview(db: Session = Depends(get_db)) -> GovernanceOverviewRead:
    return service.get_governance_overview(db)


@router.get("/events", response_model=list[GovernanceEventRead])
def list_governance_events(
    db: Session = Depends(get_db),
    kind: GovernanceEventKind | None = Query(default=None),
    kind_prefix: str | None = Query(default=None),
    search: str | None = Query(default=None),
    project_id: str | None = Query(default=None),
    environment: str | None = Query(default=None),
    status: str | None = Query(default=None),
    channel: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    limit: int | None = Query(default=None, ge=1, le=200),
) -> list[GovernanceEventRead]:
    return service.list_governance_events(
        db,
        kind=kind,
        kind_prefix=kind_prefix,
        search=search,
        project_id=project_id,
        environment=environment,
        status=status,
        channel=channel,
        provider=provider,
        target_type=target_type,
        page=page,
        page_size=page_size,
        limit=limit,
    )


@router.get("/events/{event_id}", response_model=GovernanceEventDetailRead)
def get_governance_event_detail(event_id: str, db: Session = Depends(get_db)) -> GovernanceEventDetailRead:
    event = service.get_governance_event_detail(db, event_id)
    if event is None:
        raise NotFoundError(f"governance event {event_id} not found")
    return event
