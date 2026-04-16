"""Job API endpoints"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DBAPIError

from ..auth.service import get_token_payload
from .models import (
    PipelineJobResponse,
    PipelineJobStatusUpdate,
)
from .service import (
    assign_job,
    build_job_read,
    update_job_status,
)
from ..runners.service import get_runner_by_id
from ...database.core import DbSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs")


@router.post(
    "/request", response_model=PipelineJobResponse, status_code=status.HTTP_202_ACCEPTED
)
def request_job(dbsession: DbSession, payload: dict = Depends(get_token_payload)):
    try:
        runner_id = int(payload.get("sub"))
        runner = get_runner_by_id(runner_id, dbsession)
        if not runner:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        job = assign_job(runner_id, dbsession)
        if not job:
            return PipelineJobResponse(job=None)
        return PipelineJobResponse(job=build_job_read(job.pipeline_job_id, dbsession))
    except DBAPIError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc


@router.patch("/{pipeline_job_id}", status_code=status.HTTP_204_NO_CONTENT)
def update_job(
    pipeline_job_id: int,
    body: PipelineJobStatusUpdate,
    dbsession: DbSession,
    payload: dict = Depends(get_token_payload),
):
    try:
        job = update_job_status(dbsession, pipeline_job_id, body.status)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {pipeline_job_id} not found",
            )
    except DBAPIError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc
