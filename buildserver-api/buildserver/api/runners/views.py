import logging

from fastapi import APIRouter, status
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import DBAPIError, NoResultFound

# TODO: switching to relative imports
from .service import (
    generate_registration_token,
    get_all_runners,
    get_runner_by_token,
    register_runner,
    unregister_runner,
    update_runner_health,
    validate_registration_token,
)
from buildserver.api.runners.models import (
    HeartbeatRequest,
    RegisterRequest,
    GenerateTokenResponse,
    RunnerRead,
    RunnerHealth,
)
from buildserver.database.core import DbSession

router = APIRouter(prefix="/runners")
logger = logging.getLogger(__name__)


@router.post("/heartbeat", status_code=status.HTTP_204_NO_CONTENT)
def send_heartbeat(token: HeartbeatRequest, dbsession: DbSession):
    try:
        runner = get_runner_by_token(token.token, dbsession)
        logger.debug("Got heartbeat from %s", runner)
        update_runner_health(runner.runner_id, RunnerHealth.HEALTHY, dbsession)
    except NoResultFound as exc:
        logger.error("Could not find token: %s", token)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND) from exc
    except DBAPIError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc


@router.post("/register", response_model=GenerateTokenResponse)
def generate_token(dbsession: DbSession):
    """Generate a runner registration token."""
    token = generate_registration_token(dbsession)
    if not token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return GenerateTokenResponse(
        token=token.token, created_at=token.created_at, expires_at=token.expires_at
    )


@router.post("", response_model=RunnerRead, status_code=status.HTTP_201_CREATED)
def create_runner(runner: RegisterRequest, dbsession: DbSession):
    """Register a runner with server"""
    try:
        if not validate_registration_token(runner.token, dbsession):
            logger.error("invalid token")
            # TODO: need finer grained responses for better status code handling
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        res = register_runner(runner.token, runner.name, dbsession)
        return RunnerRead(
            runner_id=res.runner_id,
            name=res.name,
            health=RunnerHealth(res.health),
            last_seen=res.last_seen,
        )
    except DBAPIError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc


@router.get("", response_model=list[RunnerRead])
def get_runners(dbsession: DbSession):
    """List all runners."""
    try:
        runners = get_all_runners(dbsession)
        return [
            RunnerRead(
                runner_id=runner.runner_id,
                name=runner.name,
                health=RunnerHealth(runner.health),
                last_seen=runner.last_seen,
            )
            for runner in runners
        ]
    except DBAPIError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc


@router.delete("/{runner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_runner(runner_id: int, dbsession: DbSession):
    """Unregister a runner."""
    try:
        found = unregister_runner(runner_id, dbsession)
        if not found:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    except DBAPIError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc
