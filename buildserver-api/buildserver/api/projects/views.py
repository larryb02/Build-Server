"""Project API endpoints"""

import logging

from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import DBAPIError

from ...database.core import DbSession
from ...pipeline.spec import SpecError
from ..pipelines.models import PipelineRead
from .models import ProjectCreate, ProjectRead, TriggerRequest
from .service import (
    create_project,
    get_all_projects,
    get_project_by_id,
    trigger_pipeline,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects")


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def register_project(project: ProjectCreate, dbsession: DbSession) -> ProjectRead:
    try:
        row = create_project(project, dbsession)
        return ProjectRead.model_validate(row, from_attributes=True)
    except DBAPIError as exc:
        logger.error(exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc


@router.get("", response_model=list[ProjectRead])
def list_projects(dbsession: DbSession) -> list[ProjectRead]:
    try:
        return [
            ProjectRead.model_validate(p, from_attributes=True)
            for p in get_all_projects(dbsession)
        ]
    except DBAPIError as exc:
        logger.error(exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc


@router.post(
    "/{project_id}/trigger",
    response_model=PipelineRead,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger(
    project_id: int, body: TriggerRequest, dbsession: DbSession
) -> PipelineRead:
    project = get_project_by_id(project_id, dbsession)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    try:
        pipeline = trigger_pipeline(project, body.branch, dbsession)
        return PipelineRead.model_validate(pipeline, from_attributes=True)
    except SpecError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except DBAPIError as exc:
        logger.error(exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc
