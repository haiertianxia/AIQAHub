from fastapi import APIRouter

from app.schemas.auth import LoginRequest, LoginResponse, UserProfile
from app.services.auth_service import AuthService

router = APIRouter()
service = AuthService()


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest) -> LoginResponse:
    return service.login(payload)


@router.post("/logout")
def logout() -> dict[str, str]:
    return {"message": "logged out"}


@router.get("/me", response_model=UserProfile)
def me() -> UserProfile:
    return service.profile()

