import json
from random import randint
import threading
import time
from unittest.mock import patch

import pytest

from runner.agent import Agent
from runner.types import JobStatus


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
