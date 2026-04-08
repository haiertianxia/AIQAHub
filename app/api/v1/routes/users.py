from fastapi import APIRouter

from app.schemas.auth import UserProfile
from app.services.user_service import UserService

router = APIRouter()
service = UserService()


@router.get("", response_model=list[UserProfile])
def list_users() -> list[UserProfile]:
    return service.list_users()

