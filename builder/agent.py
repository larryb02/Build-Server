import asyncio
from collections import defaultdict
from dataclasses import dataclass
import enum
import logging
from uuid import uuid4, UUID

from builder.builder import Builder


JOB_TYPE = enum.Enum("JOB_TYPE", ["BUILD_PROGRAM", "SEND_ARTIFACTS"])
STATUS = enum.Enum("STATUS", ["QUEUED", "RUNNING", "COMPLETED"])


@dataclass
class JobState:
    type: JOB_TYPE = None
    status: STATUS | None = None
    result: asyncio.Future = None


class Agent:
    """
    Long running process that assigns jobs from task queue to workers
    """

    async def __build_program(self):
        job_id, repo_url = await self.build_job_queue.get()
        self.jobs[job_id].status = STATUS.RUNNING
        self.logger.info(f"[Worker-{job_id}] Building: {repo_url}")
        b = Builder()
        status = b.run(repo_url)
        try:
            self.jobs[job_id].result.set_result(status)
        except asyncio.InvalidStateError as e:
            self.logger.error(f"Failed to set result of future {e}")
            raise e
        self.build_job_queue.task_done()
        self.jobs[job_id].status = STATUS.COMPLETED

    async def __send_artifacts(self):
        job_id, artifacts = await self.artifact_job_queue.get()
        self.logger.info(f"Cool shiny artifact: {job_id} {artifacts}")

    def __init__(self):
        logging.basicConfig()
        self.logger = logging.getLogger(f"{__name__}")
        self.logger.setLevel(logging.INFO)
        self.build_job_queue = asyncio.Queue()
        self.artifact_job_queue = asyncio.Queue()
        self.jobs = defaultdict(
            JobState
        )  # maps job type/status/results to a job_id; make this clearer

        # predefined job handlers due to time constraints and simple needs
        # the next logical step is to create a class that takes a job_type, handler, and queue as parameters
        # to allow for dynamic job types and handlers if the need ever arises for more
        self.jobhandlers = {
            JOB_TYPE.BUILD_PROGRAM: {
                "fn": self.__build_program,
                "queue": self.build_job_queue,
            },
            JOB_TYPE.SEND_ARTIFACTS: {
                "fn": self.__send_artifacts,
                "queue": self.artifact_job_queue,
            },
        }

    async def add_job(self, job_type, job) -> UUID:
        job_id = uuid4()
        self.logger.info(f"Added new job: [{job_id} {job_type}]: {job}")
        await self.jobhandlers[job_type]["queue"].put((job_id, job))
        self.jobs[job_id].status = STATUS.QUEUED
        self.jobs[job_id].result = asyncio.get_running_loop().create_future()
        return job_id

    def close(self):
        for w in self.workers:
            w.cancel()
        self.logger.info("Shut down build agent")

    async def do_job(self, job_type):
        while True:
            await self.jobhandlers[job_type]["fn"]()

    async def run(self):
        self.logger.info("Started build agent")
        self.workers = [
            asyncio.create_task(self.do_job(job_type)) for job_type in JOB_TYPE
        ]
