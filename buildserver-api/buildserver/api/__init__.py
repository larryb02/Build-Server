from fastapi import APIRouter

from .pipelines.views import router as pipelines_router
from .projects.views import router as projects_router
from .runners.views import router as runners_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(pipelines_router, tags=["pipelines"])
api_router.include_router(projects_router, tags=["projects"])
api_router.include_router(runners_router, tags=["runners"])
