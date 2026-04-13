from fastapi import APIRouter

from app.api.v1.routes import ai, assets, audit, auth, connectors, environments, executions, gates, governance, notifications, projects, reports, settings, suites, users

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(suites.router, prefix="/suites", tags=["suites"])
api_router.include_router(environments.router, prefix="/environments", tags=["environments"])
api_router.include_router(executions.router, prefix="/executions", tags=["executions"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(gates.router, prefix="/gates", tags=["gates"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(governance.router, prefix="/governance", tags=["governance"])
api_router.include_router(connectors.router, prefix="/connectors", tags=["connectors"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
