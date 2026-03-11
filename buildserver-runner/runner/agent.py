"""Agent is an execution node"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, CancelledError
import requests
import threading

import grpc
from protos import registry_pb2, registry_pb2_grpc
from tenacity import retry, retry_if_exception_type, wait_exponential, before_sleep_log

from runner.builder.builder import run as run_build, BuildError, CloneError
from runner.types import Job, JobStatus
from runner.config import LOG_LEVEL, APISERVER_HOST, RUNNER_TOKEN, GRPC_SERVICE_CONFIG
from runner.rmq.rmq import RabbitMQConsumer

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(LOG_LEVEL)

MAX_WORKERS = 4  # TODO: move to config
BUILD_QUEUE = "build_jobs"
HEARTBEAT_TIMER = 1


class Agent:
    """
    Build agent that consumes jobs from RabbitMQ and executes them.
    """

    def __init__(self):
        self._rmq = RabbitMQConsumer()
        self._executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self._heartbeat_executor = ThreadPoolExecutor(max_workers=1)
        self.active_jobs: list[Job] = []
        self._stop_event = threading.Event()
        self._grpc_channel = grpc.insecure_channel(
            APISERVER_HOST,
            options=[
                ("grpc.enable_retries", 1),
                ("grpc.service_config", json.dumps(GRPC_SERVICE_CONFIG)),
            ],
        )

    def start(self):
        """Start consuming from the build queue. Blocks the calling thread."""
        if not APISERVER_HOST:
            raise RuntimeError(
                "runner is not registered - run 'buildserver-runner register' first"
            )
        logger.info("starting agent...")
        try:
            self._heartbeat_executor.submit(self._heartbeat)
            self._rmq.start(BUILD_QUEUE, self._on_message, prefetch_count=MAX_WORKERS)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the agent and close the RabbitMQ connection."""
        logger.info("stopping agent...")
        self._stop_event.set()
        if self._grpc_channel:
            self._grpc_channel.close()
        self._heartbeat_executor.shutdown(wait=True)
        self._rmq.stop()

    def _heartbeat(self):
        @retry(
            retry=retry_if_exception_type(grpc.RpcError),
            wait=wait_exponential(multiplier=1, min=1, max=60),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
        # NOTE: delayed cancellation on keyboard interrupt while waiting for next retry attempt
        def connect():
            registry = registry_pb2_grpc.RegistryStub(self._grpc_channel)

            def send_ping():
                while not self._stop_event.is_set():
                    self._stop_event.wait(timeout=HEARTBEAT_TIMER)
                    logger.debug("sending ping")
                    yield registry_pb2.HeartbeatMessage(
                        runner_token=RUNNER_TOKEN, message="PING"
                    )

            logger.debug("attempting to connect to server")
            for response in registry.Heartbeat(send_ping()):
                logger.debug("heartbeat pong: runner_token=%s", response.runner_token)

        connect()

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
