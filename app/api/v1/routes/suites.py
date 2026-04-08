from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.suite import TestSuiteCreate, TestSuiteRead
from app.services.suite_service import SuiteService

router = APIRouter()
service = SuiteService()


@router.get("", response_model=list[TestSuiteRead])
def list_suites(db: Session = Depends(get_db)) -> list[TestSuiteRead]:
    return service.list_suites(db)


@router.post("", response_model=TestSuiteRead)
def create_suite(payload: TestSuiteCreate, db: Session = Depends(get_db)) -> TestSuiteRead:
    return service.create_suite(db, payload)
