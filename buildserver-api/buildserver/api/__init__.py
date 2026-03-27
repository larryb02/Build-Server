from fastapi import APIRouter

from buildserver.api.jobs.views import router as jobs_router
from buildserver.api.runners.views import router as runners_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(jobs_router, tags=["jobs"])
api_router.include_router(runners_router, tags=["runners"])
