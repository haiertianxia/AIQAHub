from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.connector import ConnectorRead, ConnectorTestPayload, JenkinsCallbackPayload
from app.services.connector_service import ConnectorService
from app.schemas.execution import ExecutionRead

router = APIRouter()
service = ConnectorService()


@router.get("", response_model=list[ConnectorRead])
def list_connectors() -> list[ConnectorRead]:
    return service.list_connectors()


@router.post("/{connector_type}/test", response_model=ConnectorRead)
def test_connector(connector_type: str, payload: ConnectorTestPayload) -> ConnectorRead:
    return service.test_connector(connector_type, payload.payload)


@router.post("/jenkins/callback", response_model=ExecutionRead)
async def jenkins_callback(request: Request, db: Session = Depends(get_db)) -> ExecutionRead:
    body = await request.body()
    payload = JenkinsCallbackPayload.model_validate_json(body)
    return service.handle_jenkins_callback(db, payload, headers=request.headers, raw_body=body)
