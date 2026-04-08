from app.schemas.auth import UserProfile
from app.services.base import BaseService


class UserService(BaseService):
    def list_users(self) -> list[UserProfile]:
        return [UserProfile(id="user_demo", email="demo@example.com", name="Demo User")]

