from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.suite import TestSuiteCreate, TestSuiteRead
from app.services.suite_service import SuiteService

router = APIRouter()
service = SuiteService()


@router.get("", response_model=list[TestSuiteRead])
def list_suites(db: Session = Depends(get_db), project_id: str | None = Query(default=None)) -> list[TestSuiteRead]:
    return service.list_suites(db, project_id=project_id)


@router.get("/{suite_id}", response_model=TestSuiteRead)
def get_suite(suite_id: str, db: Session = Depends(get_db)) -> TestSuiteRead:
    return service.get_suite(db, suite_id)


@router.post("", response_model=TestSuiteRead)
def create_suite(payload: TestSuiteCreate, db: Session = Depends(get_db)) -> TestSuiteRead:
    return service.create_suite(db, payload)


@router.put("/{suite_id}", response_model=TestSuiteRead)
def update_suite(suite_id: str, payload: TestSuiteCreate, db: Session = Depends(get_db)) -> TestSuiteRead:
    return service.update_suite(db, suite_id, payload)


@router.delete("/{suite_id}", response_model=TestSuiteRead)
def delete_suite(suite_id: str, db: Session = Depends(get_db)) -> TestSuiteRead:
    return service.delete_suite(db, suite_id)
