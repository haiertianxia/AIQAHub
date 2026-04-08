from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Permission:
    code: str
    description: str


ADMIN = Permission(code="admin", description="Platform administrator")
PROJECT_OWNER = Permission(code="project_owner", description="Project owner")
MEMBER = Permission(code="member", description="Project member")

