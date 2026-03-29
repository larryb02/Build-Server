"""Agent is an execution node"""

import logging
import threading
import time

import httpx
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, wait_exponential, before_sleep_log

from runner.builder.builder import run as run_build, BuildError, CloneError
from runner.config import APISERVER_HOST, RUNNER_TOKEN
from runner.types import Job


logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 10


class Agent:
    """
    Build agent that consumes jobs from RabbitMQ and executes them.
    """

    def __init__(self):
        self._stop_event = threading.Event()

    def start(self):
        """Start consuming from the build queue. Blocks the calling thread."""
        if not APISERVER_HOST:
            raise RuntimeError(
                "runner is not registered - run 'buildserver-runner register' first"
            )
        logger.info("starting agent...")
        try:
            threads = [
                threading.Thread(target=self._heartbeat, daemon=True),
                threading.Thread(target=self._request_work, daemon=True),
            ]
            for t in threads:
                t.start()
            for t in threads:
                t.join()
        except KeyboardInterrupt:
            self.stop()

    def _request_work(self):
        sleep_for = 3
        while not self._stop_event.is_set():
            time.sleep(sleep_for)
            logger.debug("requesting work...")
            try:
                with httpx.Client() as client:
                    r = client.post(
                        f"{APISERVER_HOST}/api/v1/jobs/request",
                        headers={"Authorization": f"Bearer {RUNNER_TOKEN}"},
                    )
                    r.raise_for_status()
                    job = r.json().get("job")
                    logger.debug("got %s", job)
                    if not job:
                        logger.debug("no jobs")
                        continue
                    # NOTE: Shutdown ungracefully fine for now.
                    # No worker pools for now -- also fine.
                    threading.Thread(
                        target=self._handle_job, args=(job,), daemon=True
                    ).start()
            except httpx.HTTPError as exc:
                logger.error("failed to request work: %s", exc)

    def stop(self):
        logger.info("stopping agent...")
        self._stop_event.set()

    @retry(
        retry=retry_if_exception_type(httpx.HTTPError),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _heartbeat(self):
        while not self._stop_event.is_set():
            if self._stop_event.is_set():
                break
            self._stop_event.wait(timeout=HEARTBEAT_INTERVAL)
            logger.debug("sending heartbeat")
            with httpx.Client() as client:
                try:
                    r = client.post(
                        f"{APISERVER_HOST}/api/v1/runners/heartbeat",
                        headers={"Authorization": f"Bearer {RUNNER_TOKEN}"},
                    )
                    r.raise_for_status()
                except httpx.HTTPError as exc:
                    logger.error("failed to send heartbeat: %s", exc)

    def _update_job_status(self, job_id: int, status: str):
        with httpx.Client() as client:
            r = client.patch(
                f"{APISERVER_HOST}/api/v1/jobs/{job_id}",
                json={"job_status": status},
                headers={"Authorization": f"Bearer {RUNNER_TOKEN}"},
            )
            r.raise_for_status()

    def _handle_job(self, job):
        """Execute a job. Runs in a worker thread."""
        logger.info("handling job: %s", job)
        try:
            validated_job = Job.model_validate(job)
        except ValidationError as exc:
            logger.error(exc)
            return
        try:
            self._update_job_status(
                validated_job.job_id, "RUNNING"
            )  # TODO: make enum type
            run_build(validated_job)
            self._update_job_status(validated_job.job_id, "SUCCEEDED")
            logger.info("Job %s succeeded", validated_job.job_id)
        except (BuildError, CloneError) as exc:
            logger.error("Job failed: %s", exc)
            self._update_job_status(validated_job.job_id, "FAILED")
        except httpx.HTTPError as exc:
            logger.error("Failed to update job status: %s", exc)


if __name__ == "__main__":
    Agent().start()
