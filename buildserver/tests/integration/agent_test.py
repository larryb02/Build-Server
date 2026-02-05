import threading
import time

import pika
import pytest

from buildserver.agent import agent
from buildserver.rmq.rmq import RabbitMQConnection


@pytest.fixture()
def run_agent():
    """Start the agent in a background thread with a fresh connection."""
    agent._rmq = RabbitMQConnection()
    agent.results.clear()
    t = threading.Thread(target=agent.start, daemon=True)
    t.start()
    time.sleep(1)
    yield
    agent.stop()
    t.join(timeout=5)


def _publish(body: bytes):
    params = RabbitMQConnection._get_connection_parameters()
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.basic_publish(
        exchange="",
        routing_key=agent.BUILD_QUEUE,
        body=body,
        properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent),
    )
    connection.close()


class TestJobSubmission:

    def test_agent_receives_message(self, run_agent):
        _publish(b"hello")
        time.sleep(1)

        assert len(agent.results) == 1
        assert agent.results[0] == "doing work!"

    def test_agent_handles_multiple_messages(self, run_agent):
        for msg in [b"job-1", b"job-2", b"job-3"]:
            _publish(msg)
        time.sleep(2)

        assert len(agent.results) == 3
        assert all(r == "doing work!" for r in agent.results)
