import logging
import secrets
from collections import defaultdict
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


class Registry(registry_pb2_grpc.RegistryServicer):
    """Runner registry"""

    def __init__(self):
        self._pending_tokens: dict = defaultdict()
        self._token_lock = threading.Lock()

    def Register(self, request, context):
        if not self._validate_registration_token(request.token):
            logger.error("invalid token")
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            return registry_pb2.RegisterResponse()
        token_hash = hashlib.sha256(request.token.encode()).hexdigest()
        runner = Runner(
            name=request.name,
            runner_token_hash=token_hash,
            health=registry_pb2.RunnerHealth.UNKNOWN,
        )
        with session_context() as session:
            try:
                runner_id = runner.runner_id
                session.add(runner)
                session.flush()
            except DBAPIError as exc:
                logger.error(exc)
                session.rollback()
                context.abort(grpc.StatusCode.INTERNAL, "failed to register runner")
        with self._token_lock:
            self._pending_tokens.pop(request.token, None)
        # logger.debug("registered runner: %s", runner)
        return registry_pb2.RegisterResponse(
            runner=registry_pb2.RunnerInfo(
                runner_id=runner_id,
                name=request.name,
                token=request.token,
                health=registry_pb2.RunnerHealth.UNKNOWN,
            )
        )

    def Heartbeat(self, request, context):
        # a runner will hit this endpoint to start a bidirectional stream
        # then periodical ping-pong responses will be sent
        raise NotImplementedError("Heartbeat not implemented")

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
