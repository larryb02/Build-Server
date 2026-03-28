import logging

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlalchemy.exc import DBAPIError

# TODO: switching to relative imports
from .service import (
    generate_registration_token,
    get_all_runners,
    get_runner_by_id,
    register_runner,
    unregister_runner,
    update_runner_health,
    validate_registration_token,
)
from buildserver.api.runners.models import (
    RegisterRequest,
    GenerateTokenResponse,
    RegisterResponse,
    RunnerRead,
    RunnerHealth,
)
from buildserver.database.core import DbSession
from buildserver.api.auth.service import get_token_payload

router = APIRouter(prefix="/runners")
logger = logging.getLogger(__name__)


@router.post("/heartbeat", status_code=status.HTTP_204_NO_CONTENT)
def send_heartbeat(dbsession: DbSession, payload: dict = Depends(get_token_payload)):
    try:
        # TODO: create some types when this is fully fleshed out so linter stops yelling
        runner_id = int(payload.get("sub"))  # type: ignore
        # NOTE: call this inside update_runner_health so we're not making 3 queries
        runner = get_runner_by_id(runner_id, dbsession)
        if not runner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Could not find runner"
            )
        logger.debug("Got heartbeat from %s", runner)
        update_runner_health(runner.runner_id, RunnerHealth.HEALTHY, dbsession)
    except DBAPIError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR) from exc


@router.post("/token", response_model=GenerateTokenResponse)
def generate_token(dbsession: DbSession):
    """Generate a runner registration token."""
    token = generate_registration_token(dbsession)
    if not token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return GenerateTokenResponse(
        token=token.token, created_at=token.created_at, expires_at=token.expires_at
    )


@router.post("", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def create_runner(runner: RegisterRequest, dbsession: DbSession):
    """Register a runner with server"""
    try:
        if not validate_registration_token(runner.reg_token, dbsession):
            logger.error("invalid token")
            # TODO: need finer grained responses for better status code handling
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

        res = register_runner(runner.name, runner.reg_token, dbsession)
        return RegisterResponse(auth_token=res)
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
