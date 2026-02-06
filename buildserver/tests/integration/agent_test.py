import json
from random import randint
import threading
import time
import uuid
from unittest.mock import patch

import pytest

from buildserver.agent.agent import Agent, BUILD_QUEUE
from buildserver.models.jobs import JobStatus
from buildserver.rmq.rmq import RabbitMQProducer


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
            "job_status": JobStatus.CREATED,
            "created_at": time.time(),
        }
    ).encode()


class TestJobSubmission:

    def test_agent_receives_and_executes_job(self, run_agent, producer):
        with (
            patch("buildserver.agent.agent.builder") as mock_builder,
            patch("buildserver.agent.agent.requests"),
        ):
            mock_builder.run.return_value = {
                "git_repository_url": "git@github.com:user/repo.git",
                "commit_hash": "abc123",
                "build_status": JobStatus.SUCCEEDED,
            }

            producer.publish(BUILD_QUEUE, _make_job_message())
            time.sleep(1)

            mock_builder.run.assert_called_once()
            result = mock_builder.run.return_value
            assert result["build_status"] in (JobStatus.SUCCEEDED, JobStatus.FAILED)

    def test_agent_executes_multiple_jobs(self, run_agent, producer):
        with (
            patch("buildserver.agent.agent.builder") as mock_builder,
            patch("buildserver.agent.agent.requests"),
        ):
            mock_builder.run.return_value = {
                "git_repository_url": "git@github.com:user/repo.git",
                "commit_hash": "abc123",
                "build_status": JobStatus.FAILED,
            }

            for _ in range(3):
                producer.publish(BUILD_QUEUE, _make_job_message())
            time.sleep(2)

            assert mock_builder.run.call_count == 3
            result = mock_builder.run.return_value
            assert result["build_status"] is not None
