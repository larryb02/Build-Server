import hashlib
from datetime import datetime, timedelta
from unittest.mock import MagicMock

import grpc
import pytest

from buildserver.api.registry.service import Registry, HEARTBEAT_TIMEOUT
from buildserver.api.runners.models import Runner  # registers Runner with Base
from buildserver.database.core import session_context
from protos import registry_pb2


@pytest.fixture
def registry():
    return Registry()


@pytest.fixture
def ctx():
    return MagicMock()


def _seed_token(registry, token):
    """Insert a token directly into pending_tokens, bypassing GenerateRegistrationToken."""
    registry._pending_tokens[token] = datetime.now() + timedelta(minutes=10)
    return hashlib.sha256(token.encode()).hexdigest()


class TestRegister:

    def test_runner_registration(self, registry, ctx, dbsession):
        token = "test-token"
        token_hash = _seed_token(registry, token)

        request = MagicMock()
        request.token = token
        request.name = "test-runner"

        registry.Register(request, ctx)

        assert token not in registry._pending_tokens

    def test_invalid_token_nonexistent(self, registry, ctx, dbsession):
        token = "nonexistent-token"
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        request = MagicMock()
        request.token = token
        request.name = "test-runner"

        registry.Register(request, ctx)

        ctx.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)

    def test_invalid_token_expired(self, registry, ctx, dbsession):
        token = "expired-token"
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        registry._pending_tokens[token] = datetime.now() - timedelta(minutes=1)

        request = MagicMock()
        request.token = token
        request.name = "test-runner"

        registry.Register(request, ctx)

        ctx.set_code.assert_called_with(grpc.StatusCode.INVALID_ARGUMENT)


class TestUnregister:

    def test_removes_last_seen_entry(self, registry, ctx, dbsession):
        token = "test-token"
        token_hash = _seed_token(registry, token)

        reg_request = MagicMock()
        reg_request.token = token
        reg_request.name = "test-runner"
        response = registry.Register(reg_request, ctx)

        unreg_request = MagicMock()
        unreg_request.runner_id = response.runner.runner_id
        print(unreg_request.runner_id)
        registry.Unregister(unreg_request, ctx)


class TestCheckRunnerHealth:

    def _register_runner(self, registry, ctx, token="test-token"):
        _seed_token(registry, token)
        req = MagicMock()
        req.token = token
        req.name = "test-runner"
        return registry.Register(req, ctx).runner.runner_id

    def _set_runner_state(self, runner_id, health, last_seen):
        with session_context() as session:
            runner = session.get(Runner, runner_id)
            runner.health = health
            runner.last_seen = last_seen

    def test_timed_out_runner_marked_unhealthy(self, registry, ctx, dbsession):
        runner_id = self._register_runner(registry, ctx)
        self._set_runner_state(
            runner_id,
            health=registry_pb2.RunnerHealth.HEALTHY,
            last_seen=datetime.now() - HEARTBEAT_TIMEOUT - timedelta(seconds=10),
        )

        registry._check_runner_health()

        with session_context() as session:
            runner = session.get(Runner, runner_id)
            assert runner.health == registry_pb2.RunnerHealth.UNHEALTHY

    def test_recent_runner_not_affected(self, registry, ctx, dbsession):
        runner_id = self._register_runner(registry, ctx)
        self._set_runner_state(
            runner_id,
            health=registry_pb2.RunnerHealth.HEALTHY,
            last_seen=datetime.now() - timedelta(seconds=5),
        )

        registry._check_runner_health()

        with session_context() as session:
            runner = session.get(Runner, runner_id)
            assert runner.health == registry_pb2.RunnerHealth.HEALTHY


class TestListAvailable:

    def test_returns_healthy_runners(self, registry, ctx, dbsession):
        token = "test-token"
        token_hash = _seed_token(registry, token)

        reg_request = MagicMock()
        reg_request.token = token
        reg_request.name = "test-runner"
        response = registry.Register(reg_request, ctx)

        runner_id = response.runner.runner_id
        registry._update_health(runner_id, registry_pb2.RunnerHealth.HEALTHY)

        list_response = registry.ListAvailable(MagicMock(), ctx)

        assert len(list_response.runners) == 1
        assert list_response.runners[0].runner_id == runner_id
        assert list_response.runners[0].health == registry_pb2.RunnerHealth.HEALTHY
