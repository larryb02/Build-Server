"""Agent is an execution node"""

import logging
from concurrent.futures import ThreadPoolExecutor
import requests

from runner.builder.builder import run as run_build, BuildError, CloneError
from runner.types import Job, JobStatus
from runner.config import LOG_LEVEL, APISERVER_HOST
from runner.rmq.rmq import RabbitMQConsumer

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

MAX_WORKERS = 4  # TODO: move to config
BUILD_QUEUE = "build_jobs"


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
        self.active_jobs: list[Job] = []

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
        job = Job.model_validate_json(body)
        # since queue limits amount of messages consumed
        # should be fine to immediately start executing a job
        self.active_jobs.append(job)
        # from here agent needs to update status will just make calls to API for now
        # NOTE: for first iteration this is fine, ideally want to stream here
        logger.debug("We made it here...")
        try:
            requests.patch(
                f"{APISERVER_HOST}/jobs/{job.job_id}",
                json={"job_status": JobStatus.RUNNING},
                timeout=5,
            )
        # can't return anything if you can't reach the server
        # this is fine for now because implementation will be changing soon
        # but hanging jobs will exist in database -- are they drained from rabbitmq?
        except requests.exceptions.RequestException as e:
            logger.error("Failed to make request: %s", e)
            return
        try:
            run_build(job)
            status = JobStatus.SUCCEEDED
            logger.info("Job %s succeeded", job.job_id)
        except (BuildError, CloneError) as e:
            status = JobStatus.FAILED
            logger.error("Job %s failed: %s", job.job_id, e)
        try:
            requests.patch(
                f"{APISERVER_HOST}/jobs/{job.job_id}",
                json={"job_status": status},
                timeout=5,
            )
        except requests.exceptions.RequestException as e:
            logger.error("Failed to make request: %s", e)
            return
        self.active_jobs.remove(job)


if __name__ == "__main__":
    Agent().start()
