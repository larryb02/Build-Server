import hashlib
import logging
import secrets
import threading
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.exc import DBAPIError

from .models import PendingTokens, Runner, RunnerHealth
from ...database.core import DbSession, session_context
from ..auth.service import create_jwt, get_token_payload

logger = logging.getLogger(__name__)
EXPIRES_IN = timedelta(minutes=60)
HEARTBEAT_TIMEOUT = timedelta(seconds=30)


def run_health_monitor(stop_event: threading.Event) -> None:
    """Background task to maintain runner health state"""
    while not stop_event.is_set():
        stop_event.wait(timeout=HEARTBEAT_TIMEOUT.seconds)
        _check_runner_health()


def _check_runner_health() -> None:
    logger.debug("checking runner health status")
    stale_threshold = datetime.now() - HEARTBEAT_TIMEOUT
    with session_context() as session:
        try:
            stale_runners = session.scalars(
                update(Runner)
                .where(Runner.health == RunnerHealth.HEALTHY)
                .where(Runner.last_seen < stale_threshold)
                .values(health=RunnerHealth.OFFLINE)
                .returning(Runner)
            ).all()
        except DBAPIError as exc:
            logger.error("failed to update stale runners: %s", exc)
            return
        for runner in stale_runners:
            logger.warning(
                "runner timed out, marking offline\n id: %s\n last_seen: %s",
                runner.runner_id,
                runner.last_seen,
            )


def register_runner(name: str, reg_token: str, dbsession: DbSession) -> str:
    runner = Runner(name=name)
    try:
        dbsession.add(runner)
        dbsession.flush()
        pending = dbsession.scalars(
            select(PendingTokens).where(PendingTokens.token == reg_token)
        ).one_or_none()
        dbsession.delete(pending)
        token = create_jwt(data={"sub": str(runner.runner_id)})
        return token
    except DBAPIError as exc:
        logger.error(exc)
        raise exc


def unregister_runner(runner_id: int, dbsession: DbSession) -> bool:
    try:
        result = dbsession.execute(
            update(Runner)
            .where(Runner.runner_id == runner_id)
            .where(Runner.deleted == False)  # noqa: E712
            .values(deleted=True)
            .returning(Runner.runner_id)
        )
        found = result.one_or_none() is not None
        if found:
            logger.debug("successfully unregistered runner %s", runner_id)
        else:
            logger.debug("could not find runner with id: %s", runner_id)
        return found
    except DBAPIError as exc:
        logger.error(exc)
        raise exc


def get_all_runners(dbsession: DbSession) -> list[Runner]:
    try:
        return list(
            dbsession.scalars(select(Runner).where(Runner.deleted == False)).all()
        )  # noqa: E712
    except DBAPIError as exc:
        logger.error("failed to list runners: %s", exc)
        raise exc


def generate_registration_token(dbsession: DbSession) -> PendingTokens:
    token = secrets.token_hex()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    created_at = datetime.now()
    expires_at = created_at + EXPIRES_IN
    pending = PendingTokens(
        token=token_hash, created_at=created_at, expires_at=expires_at
    )
    try:
        dbsession.add(pending)
        dbsession.flush()
        return pending
    except DBAPIError as exc:
        logger.error("failed to generate token: %s", exc)
        raise exc


def get_runner_by_id(runner_id: int, dbsession: DbSession) -> Runner | None:
    try:
        runner = dbsession.get(Runner, runner_id)
        return runner
    except DBAPIError as exc:
        logger.error("failed to get runner by token: %s", exc)
        raise exc


def update_runner_health(
    runner_id: int, health: RunnerHealth, dbsession: DbSession
) -> None:
    try:
        runner = dbsession.get(Runner, runner_id)
        if runner:
            runner.health = health
            if health == RunnerHealth.HEALTHY:
                runner.last_seen = datetime.now()
    except DBAPIError as exc:
        logger.error("failed to update health for runner %s: %s", runner_id, exc)


def validate_registration_token(token: str, dbsession: DbSession) -> bool:
    logger.debug("validating token %s", token)
    try:
        pending = dbsession.scalars(
            select(PendingTokens).where(PendingTokens.token == token)
        ).one_or_none()
        if not pending:
            logger.error("token not found")
            return False
        return pending.expires_at > datetime.now()
    except DBAPIError as exc:
        logger.error("failed to validate token: %s", exc)
        raise exc


def get_active_runner(
    dbsession: DbSession,
    payload: dict = Depends(get_token_payload),
) -> dict:
    runner_id = int(payload.get("sub"))
    runner = dbsession.get(Runner, runner_id)
    if runner is None or runner.deleted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized client",
        )
    return payload
