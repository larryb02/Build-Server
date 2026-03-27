import hashlib
import logging
import secrets
import threading
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import DBAPIError

from buildserver.api.runners.models import PendingTokens, Runner, RunnerHealth
from buildserver.database.core import DbSession, session_context

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
    now = datetime.now()
    with session_context() as session:
        try:
            runners = list(session.scalars(select(Runner)).all())
            logger.debug("Got runners: %s", runners)
        except DBAPIError as exc:
            logger.error("failed to get runners: %s", exc)
            return
        stale_runners = [
            runner
            for runner in runners
            if runner.health == RunnerHealth.HEALTHY
            and now - runner.last_seen > HEARTBEAT_TIMEOUT
        ]
        for runner in stale_runners:
            logger.warning(
                "runner timed out, marking offline\n id: %s\n last_seen: %s\n now: %s",
                runner.runner_id,
                runner.last_seen,
                now,
            )
            runner.health = RunnerHealth.OFFLINE


def register_runner(token: str, name: str, dbsession: DbSession) -> Runner:
    # token_hash = hashlib.sha256(token.encode()).hexdigest()
    runner = Runner(name=name, runner_token_hash=token)
    try:
        dbsession.add(runner)
        dbsession.flush()
        pending = dbsession.scalars(
            select(PendingTokens).where(PendingTokens.token == token)
        ).one_or_none()
        dbsession.delete(pending)
        return runner
    except DBAPIError as exc:
        logger.error(exc)
        raise exc


def unregister_runner(runner_id: int, dbsession: DbSession) -> bool:
    try:
        runner = dbsession.get(Runner, runner_id)
        if runner is None:
            logger.debug("could not find runner with id: %s", runner_id)
            return False
        dbsession.delete(runner)
        logger.debug("successfully unregistered runner")
        return True
    except DBAPIError as exc:
        logger.error(exc)
        raise exc


def get_all_runners(dbsession: DbSession) -> list[Runner]:
    try:
        return list(dbsession.scalars(select(Runner)).all())
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


def get_runner_by_token(token_hash: str, dbsession: DbSession) -> Runner:
    try:
        res = dbsession.scalars(
            select(Runner).where(Runner.runner_token_hash == token_hash)
        ).one_or_none()
        if res:
            # so linter stops complaining
            return res
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
        ).first()
    except DBAPIError as exc:
        logger.error("failed to validate token: %s", exc)
        raise exc
    if not pending:
        logger.error("token not found")
        return False
    return pending.expires_at > datetime.now()
