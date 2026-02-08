import json
from random import randint
import threading
import time
from unittest.mock import patch

import pytest

from runner.agent import Agent, BUILD_QUEUE
from runner.types import JobStatus
from runner.rmq.rmq import RabbitMQProducer


@pytest.fixture()
def run_agent():
    """Start the agent in a background thread with a fresh instance."""
    agent = Agent()
    t = threading.Thread(target=agent.start, daemon=True)
    t.start()
    time.sleep(1)
    yield agent
    agent.stop()
    t.join(timeout=5)


@pytest.fixture()
def producer():
    return RabbitMQProducer()


def _make_job_message(repo_url: str = "git@github.com:user/repo.git") -> bytes:
    return json.dumps(
        {
            "job_id": randint(0, 1000),
            "git_repository_url": repo_url,
            "commit_hash": "abc123",
            "job_status": JobStatus.QUEUED,
            "created_at": time.time(),
        }
    ).encode()


class TestJobSubmission:

    def test_agent_receives_and_executes_job(self, run_agent, producer):
        with (
            patch("runner.agent.run_build") as mock_run_build,
            patch("runner.agent.requests"),
        ):
            mock_run_build.return_value = None

            producer.publish(BUILD_QUEUE, _make_job_message())
            time.sleep(1)

            mock_run_build.assert_called_once()

    def test_agent_executes_multiple_jobs(self, run_agent, producer):
        with (
            patch("runner.agent.run_build") as mock_run_build,
            patch("runner.agent.requests"),
        ):
            mock_run_build.return_value = None

            for _ in range(3):
                producer.publish(BUILD_QUEUE, _make_job_message())
            time.sleep(2)

            assert mock_run_build.call_count == 3
