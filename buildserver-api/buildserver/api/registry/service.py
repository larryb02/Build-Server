import logging
import secrets
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import threading
import hashlib

import grpc
from protos import registry_pb2, registry_pb2_grpc
from sqlalchemy.exc import DBAPIError

from buildserver.api.runners.models import Runner
from buildserver.database.core import session_context

logger = logging.getLogger(__name__)
EXPIRES_IN = timedelta(minutes=60)
HEARTBEAT_TIMEOUT = timedelta(seconds=30)


class Registry(registry_pb2_grpc.RegistryServicer):
    """Runner registry"""

    def __init__(self):
        self._pending_tokens: dict = defaultdict()
        self._token_lock = threading.Lock()

    def start(self):
        threading.Thread(target=self._health_watcher, daemon=True).start()

    def Register(self, request, context):
        if not self._validate_registration_token(request.token):
            logger.error("invalid token")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return registry_pb2.RegisterResponse()
        token_hash = hashlib.sha256(request.token.encode()).hexdigest()
        runner = Runner(
            name=request.name,
            runner_token_hash=token_hash,
        )
        with session_context() as session:
            try:
                session.add(runner)
                session.flush()
                runner_cp = runner
            except DBAPIError as exc:
                logger.error(exc)
                session.rollback()
                context.abort(grpc.StatusCode.INTERNAL, "failed to register runner")
        with self._token_lock:
            self._pending_tokens.pop(request.token, None)
        logger.debug("registered runner: %s", runner_cp)
        return registry_pb2.RegisterResponse(
            runner=registry_pb2.RunnerInfo(
                runner_id=runner_cp.runner_id,
                name=runner_cp.name,
                token=runner_cp.runner_token_hash,
                health=runner_cp.health,
            )
        )

    def Heartbeat(self, request_iterator, context):
        try:
            while context.is_active():
                for msg in request_iterator:
                    # token_hash = hashlib.sha256(msg.runner_token.encode()).hexdigest()
                    logger.debug("Got message from: %s", msg.runner_token)
                    runner = self._get_runner_by_token(msg.runner_token)
                    if not runner:
                        logger.warning("runner not found")
                        context.abort(
                            grpc.StatusCode.NOT_FOUND, "runner not registered"
                        )
                        return  # maybe continue is better here...
                    # NOTE: Update last_seen here as well
                    self._update_health(
                        runner.runner_id, registry_pb2.RunnerHealth.HEALTHY
                    )
                    logger.debug("sending pong")
                    yield registry_pb2.HeartbeatMessage(
                        runner_token=msg.runner_token, message="PONG"
                    )
        except GeneratorExit:
            logger.debug("Client disconnected")
        finally:
            logger.debug("Stream closed setting runner to offline: %s", runner)
            self._update_health(runner.runner_id, registry_pb2.RunnerHealth.OFFLINE)

    def _get_runner_by_token(self, token_hash: str) -> Runner | None:
        with session_context() as session:
            try:
                return (
                    session.query(Runner)
                    .filter(Runner.runner_token_hash == token_hash)
                    .first()
                )
            except DBAPIError as exc:
                logger.error("failed to get runner by token: %s", exc)
                return None

    def _update_health(self, runner_id: int, health):
        with session_context() as session:
            try:
                runner = session.get(Runner, runner_id)
                if runner:
                    runner.health = health
                if health == registry_pb2.RunnerHealth.HEALTHY:
                    runner.last_seen = datetime.now()
            except DBAPIError as exc:
                logger.error(
                    "failed to update health for runner %s: %s", runner_id, exc
                )

    def _health_watcher(self):
        while True:
            time.sleep(HEARTBEAT_TIMEOUT.seconds)
            self._check_runner_health()

    def _check_runner_health(self):
        logger.debug("checking runner health status")
        now = datetime.now()
        with session_context() as session:
            try:
                runners = session.query(Runner).all()
                logger.debug("Got runners: %s", runners)
            except DBAPIError as exc:
                logger.error("failed to get runners: %s", exc)
                return
        stale_runners = [
            runner
            for runner in runners
            if runner.health == registry_pb2.RunnerHealth.HEALTHY
            and now - runner.last_seen > HEARTBEAT_TIMEOUT
        ]
        # TODO: support bulk operations
        for runner in stale_runners:
            logger.warning(
                "runner timed out, marking unhealthy\n id: %s\n last_seen: %s\n, now: %s",
                runner.runner_id,
                runner.last_seen,
                now,
            )
            self._update_health(runner.runner_id, registry_pb2.RunnerHealth.UNHEALTHY)

    def Unregister(self, request, context):
        with session_context() as session:
            try:
                runner = session.get(Runner, request.runner_id)
                if runner is None:
                    context.abort(grpc.StatusCode.NOT_FOUND)
                session.delete(runner)
            except DBAPIError as exc:
                logger.error(exc)
                context.abort(grpc.StatusCode.INTERNAL, "failed to unregister runner")
        logger.debug("unregistered runner: %s", request.runner_id)
        return registry_pb2.UnregisterResponse()

    def ListAvailable(self, request, context):
        # TODO: move db logic to a 'service' function?
        with session_context() as session:
            try:
                runners = (
                    session.query(Runner)
                    .filter(Runner.health == registry_pb2.RunnerHealth.HEALTHY)
                    .all()
                )
                result = [
                    registry_pb2.RunnerInfo(
                        runner_id=r.runner_id,
                        name=r.name,
                        token=r.runner_token_hash,
                        health=r.health,
                    )
                    for r in runners
                ]
            except DBAPIError as exc:
                logger.error(exc)
                context.abort(grpc.StatusCode.INTERNAL, "failed to list runners")
        return registry_pb2.ListAvailableResponse(runners=result)

    def GenerateRegistrationToken(self, request, context):
        token = secrets.token_hex()
        created_at = datetime.now()
        expires_at = created_at + EXPIRES_IN
        with self._token_lock:
            self._pending_tokens[token] = expires_at
        return registry_pb2.GenerateRegistrationTokenResponse(
            token=token, created_at=created_at, expires_at=expires_at
        )

    def _validate_registration_token(self, token):
        logger.debug("Got token %s", token)
        with self._token_lock:
            expires_at = self._pending_tokens.get(token)
            logger.debug("expires at %s", expires_at)
        if not expires_at:
            logger.error("token not found")
            return False
        if expires_at > datetime.now():
            return True
        return False
