from fastapi import APIRouter

from app.schemas.connector import ConnectorRead, ConnectorTestPayload
from app.services.connector_service import ConnectorService

router = APIRouter()
service = ConnectorService()


@router.get("", response_model=list[ConnectorRead])
def list_connectors() -> list[ConnectorRead]:
    return service.list_connectors()


@router.post("/{connector_type}/test", response_model=ConnectorRead)
def test_connector(connector_type: str, payload: ConnectorTestPayload) -> ConnectorRead:
    return service.test_connector(connector_type, payload.payload)
