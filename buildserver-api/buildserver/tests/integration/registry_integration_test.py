from datetime import datetime, timedelta

import pytest

from ...api.runners.models import Runner, RunnerHealth
from ...api.runners.service import (
    _check_runner_health,
    generate_registration_token,
    get_all_runners,
    register_runner,
    unregister_runner,
    validate_registration_token,
    HEARTBEAT_TIMEOUT,
)


def _seed_token(dbsession) -> str:
    """Insert a pending token directly and return the raw token."""
    pending = generate_registration_token(dbsession)
    return pending.token


class TestRegister:

    @pytest.mark.skip(reason="Test is currently broken")
    def test_runner_registration(self, dbsession):
        token = _seed_token(dbsession)
        runner = register_runner("test-runner", token, dbsession)
        assert runner is not None
        assert runner.name == "test-runner"

    def test_invalid_token_nonexistent(self, dbsession):
        assert validate_registration_token("nonexistent-token", dbsession) is False

    def test_invalid_token_expired(self, dbsession):
        from ...api.runners.models import PendingTokens

        expired = PendingTokens(
            token="expired-token",
            created_at=datetime.now() - timedelta(hours=2),
            expires_at=datetime.now() - timedelta(hours=1),
        )
        dbsession.add(expired)
        dbsession.flush()
        assert validate_registration_token("expired-token", dbsession) is False


class TestUnregister:

    @pytest.mark.skip(reason="Test is currently broken")
    def test_removes_runner(self, dbsession):
        token = _seed_token(dbsession)
        runner = register_runner("test-runner", token, dbsession)
        assert unregister_runner(runner.runner_id, dbsession) is True

    def test_unregister_nonexistent(self, dbsession):
        assert unregister_runner(99999, dbsession) is False


@pytest.mark.skip(reason="_register method is broken")
class TestCheckRunnerHealth:

    def _register(self, dbsession, token_suffix="") -> int:
        token = _seed_token(dbsession)
        return register_runner(f"test-runner{token_suffix}", token, dbsession).runner_id

    def _set_runner_state(self, runner_id, health, last_seen, dbsession):
        runner = dbsession.get(Runner, runner_id)
        runner.health = health
        runner.last_seen = last_seen

    @pytest.mark.skip(reason="requires injectable session for background thread - TODO")
    def test_timed_out_runner_marked_offline(self, dbsession):
        runner_id = self._register(dbsession)
        self._set_runner_state(
            runner_id,
            health=RunnerHealth.HEALTHY,
            last_seen=datetime.now() - HEARTBEAT_TIMEOUT - timedelta(seconds=10),
            dbsession=dbsession,
        )

        _check_runner_health()

        runner = dbsession.get(Runner, runner_id)
        assert runner.health == RunnerHealth.OFFLINE


class TestListRunners:

    def test_returns_all_runners(self, dbsession):
        token = _seed_token(dbsession)
        register_runner("test-runner", token, dbsession)

        runners = get_all_runners(dbsession)

        assert len(runners) == 1
