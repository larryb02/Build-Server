import asyncio
from collections import defaultdict
from dataclasses import dataclass
import enum
import logging
from uuid import uuid4, UUID

from buildserver.builder.builder import Builder
from buildserver.config import LOG_LEVEL


class JobType(enum.Enum):
    BUILD_PROGRAM = "BUILD_PROGRAM"
    SEND_ARTIFACTS = "SEND_ARTIFACTS"


class Status(enum.Enum):
    QUEUED = "QUEUED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass
class JobState:
    type: JobType = None
    status: Status | None = None
    result: asyncio.Future = None


class Agent:
    """
    Long running process that assigns jobs from task queue to workers
    """

    def __init__(self):
        logging.basicConfig()
        self.logger = logging.getLogger(f"{__name__}")
        self.logger.setLevel(LOG_LEVEL) # get this from env variable
        self.build_job_queue = asyncio.Queue()
        self.artifact_job_queue = asyncio.Queue()
        self.jobs = defaultdict(
            JobState
        )  # maps job type/status/results to a job_id; make this clearer

        # predefined job handlers due to time constraints and simple needs
        # the next logical step is to create a message queue system
        # to allow for dynamic job types and handlers if the need ever arises for more
        self.jobhandlers = {
            JobType.BUILD_PROGRAM: {
                "fn": self.__build_program,
                "queue": self.build_job_queue,
            },
            JobType.SEND_ARTIFACTS: {
                "fn": self.__send_artifacts,
                "queue": self.artifact_job_queue,
            },
        }

    async def __build_program(self):
        job_id, repo_url = await self.build_job_queue.get()
        self.logger.info(f"[Worker-{job_id}] Building: {repo_url}")
        b = Builder()
        try:
            status = b.run(repo_url)
            try:
                self.jobs[job_id].result.set_result(status)
            except asyncio.InvalidStateError as e:
                self.logger.error(f"Failed to set result of future {e}")
                raise e
        except Exception as e:
            self.logger.error(f"[Worker-{job_id}] Build fail: {e}")
            self.jobs[job_id].result.set_exception(e)
        # self.jobs[job_id].status = Status.COMPLETED

    async def __send_artifacts(self):
        job_id, repo_url = await self.artifact_job_queue.get()
        self.logger.info(f"[Worker-{job_id}] Gathering artifacts for build: {repo_url}")
        b = Builder()
        try:
            artifacts = b.gather_artifacts(repo_url)
        except Exception as e:
            self.logger.error(f"[Worker-{job_id}] Job failed: {e}")
            self.jobs[job_id].result.set_exception(e)
        self.jobs[job_id].result.set_result(artifacts)
        # self.jobs[job_id].status = Status.COMPLETED

    async def add_job(self, job_type, job) -> UUID:
        job_id = uuid4()
        self.logger.info(
            f"Added new job: [{job_id} {job_type}]: {job} id: {id(self.jobhandlers[job_type]["queue"])}"
        )
        try:
            await self.jobhandlers[job_type]["queue"].put((job_id, job))
        except Exception as e:
            self.logger.error("Failed to add job to queue")
            raise e
        # self.jobs[job_id].status = Status.QUEUED
        self.jobs[job_id].result = asyncio.get_running_loop().create_future()
        self.logger.debug(
            f"[{job_type}] Queue Size: {self.jobhandlers[job_type]["queue"].qsize()}"
        )
        return job_id

    def close(self):
        for w in self.workers:
            w.cancel()
        self.logger.info("Shut down build agent")

    async def do_job(self, job_type):
        while True:
            await self.jobhandlers[job_type]["fn"]()
            self.jobhandlers[job_type]["queue"].task_done()

    async def run(self):
        self.logger.info("Started build agent")
        self.workers = [
            asyncio.create_task(self.do_job(job_type)) for job_type in JobType
        ]
