"""Agent is an execution node"""

import logging
from concurrent.futures import ThreadPoolExecutor

import requests

from buildserver.agent.builder import builder
from buildserver.api.builds.models import JobRead
from buildserver.config import Config
from buildserver.models.jobs import JobStatus
from buildserver.rmq.rmq import RabbitMQConsumer

config = Config()

logging.basicConfig()
logger = logging.getLogger(f"{__name__}")
logger.setLevel(config.LOG_LEVEL)

TIMEOUT = config.TIMEOUT
MAX_WORKERS = 4  # TODO: move to config

BUILD_QUEUE = "build_jobs"
# NOTE: hack for now will store in config once agent becomes separate binary
API_ENDPOINT = "http://localhost:8000"


class Agent:
    """
    Build agent that consumes jobs from RabbitMQ and executes them.

    - maintain a connection to rabbitmq [x]
    - what should behavior be if connection to rabbitmq fails
      -> should not kill the process, continuously attempt to reconnect [x]
    - make sure queues are durable
    - verify body matches schema
    - how do build jobs get invoked?
      -> [consume from queue -> validate
      -> update active jobs -> builder executes -> report status back to API] [x]
    - run this asynchronously [x]
    - will want to limit number of jobs being performed at a time [x]
    - how will shutdown be handled? - command line, ctrl-c, kill
    """

    def __init__(self):
        self._rmq = RabbitMQConsumer()
        self._executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self.active_jobs: list[JobRead] = []

    def start(self):
        """Start consuming from the build queue. Blocks the calling thread."""
        logger.info("starting agent...")
        try:
            self._rmq.start(BUILD_QUEUE, self._on_message, prefetch_count=MAX_WORKERS)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the agent and close the RabbitMQ connection."""
        logger.info("stopping agent...")
        self._executor.shutdown(wait=True)
        self._rmq.stop()

    def _on_message(self, body: bytes):
        """Submit job to worker pool. Returns immediately to keep ioloop responsive."""
        self._executor.submit(self._handle_job, body)

    def _handle_job(self, body: bytes):
        """Execute a build job. Runs in a worker thread."""
        logger.info("received data %s", body)
        job = JobRead.model_validate_json(body)
        # since queue limits amount of messages consumed
        # should be fine to immediately start executing a job
        self.active_jobs.append(job)
        # from here agent needs to update status will just make calls to API for now
        # NOTE: for first iteration this is fine, ideally want to stream here
        requests.patch(
            f"{API_ENDPOINT}/jobs/{job.job_id}",
            json={"job_status": JobStatus.RUNNING},
            timeout=5,
        )
        try:
            # NOTE: currently not very 'integration testable'
            run_status = builder.run(job.git_repository_url)
            # update with final status here
            requests.patch(
                f"{API_ENDPOINT}/jobs/{job.job_id}",
                json={"job_status": run_status["build_status"]},
                timeout=5,
            )
        # TODO: Bad.
        except OSError as e:
            logger.error("OSError %s", e)
        finally:
            self.active_jobs.remove(job)


if __name__ == "__main__":
    Agent().start()
