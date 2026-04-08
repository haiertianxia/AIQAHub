from app.core.security import hash_password
from app.schemas.auth import LoginRequest, LoginResponse, UserProfile
from app.services.base import BaseService


class AuthService(BaseService):
    def login(self, payload: LoginRequest) -> LoginResponse:
        _ = hash_password(payload.password)
        return LoginResponse(access_token="demo-token")

    def profile(self) -> UserProfile:
        return UserProfile(id="user_demo", email="demo@example.com", name="Demo User")

