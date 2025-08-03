import asyncio
from collections import defaultdict
from dataclasses import dataclass
import enum
import logging
from uuid import uuid4, UUID


from buildserver.api.builds.models import ArtifactCreate
from buildserver.artifacts import artifactstore
import buildserver.builder.builder as builder
import buildserver.config as config
from buildserver.database.core import create_session
from buildserver.services.builds import create_artifact, update_build

logging.basicConfig()
logger = logging.getLogger(f"{__name__}")
logger.setLevel(config.LOG_LEVEL)

TIMEOUT = config.TIMEOUT


class JobType(enum.Enum):
    BUILD_PROGRAM = "BUILD_PROGRAM"
    SEND_ARTIFACTS = "SEND_ARTIFACTS"


@dataclass
class JobState:
    type: JobType = None
    result: asyncio.Future = None


class Agent:
    """
    Long running task that manages jobs and workers
    """

    def __init__(self):
        self.build_job_queue = asyncio.Queue()
        self.artifact_job_queue = asyncio.Queue()
        self.jobs = defaultdict(
            JobState
        )  # maps job type/status/results to a job_id; make this clearer

        # NOTE: predefined job handlers due to time constraints and simple needs
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
        try:
            job_id, (repo_url, build_id) = await self.build_job_queue.get()
            logger.info(f"[Worker-{job_id}] Building: {repo_url}")
            status = builder.run(repo_url)
            async def add_to_db(status):
                logger.debug(f"Updating build-{build_id} in database")
                db_session = create_session()
                try:
                    await asyncio.gather(asyncio.to_thread(update_build, db_session, build_id, **status))
                    db_session.commit()
                except Exception as e:
                    logger.error(f"Failed to update database from async: {e}")
                    db_session.rollback()
                db_session.close()
            await add_to_db(status)
            await self.add_job(JobType.SEND_ARTIFACTS, repo_url)
        except Exception as e:
            logger.error(f"[Worker-{job_id}] Build fail: {e}")
            raise e

    async def __send_artifacts(self):
        job_id, repo_url = await self.artifact_job_queue.get()
        logger.info(
            f"[{self.__send_artifacts.__name__} Worker-{job_id}] Gathering artifacts for build: {repo_url}"
        )
        try:
            artifacts = artifactstore.gather_artifacts(repo_url)
            for artifact in artifacts:
                db_session = create_session()
                try:
                    await asyncio.gather(asyncio.to_thread(create_artifact, ArtifactCreate(**artifact), db_session))
                    db_session.commit()
                    logger.debug(f"Successfully added artifact to database")
                except Exception as e:
                    logger.error(f"Failed to write artifact to database: {e}")
                    db_session.rollback()
                db_session.close()
        except Exception as e:
            logger.error(
                f"[{self.__send_artifacts.__name__} Worker-{job_id}] Job failed: {e}"
            )
            raise e

    async def add_job(self, job_type: JobType, job: any) -> UUID:
        job_id = uuid4()
        logger.info(
            f"Added new job: [{job_id} {job_type}]: {job} id: {id(self.jobhandlers[job_type]["queue"])}"
        )
        try:
            await self.jobhandlers[job_type]["queue"].put((job_id, job))
        except Exception as e:
            logger.error(f"Failed to add job to queue: {e}")
            raise e
        self.jobs[job_id].result = asyncio.get_running_loop().create_future()
        logger.debug(
            f"[{job_type}] Queue Size: {self.jobhandlers[job_type]["queue"].qsize()}"
        )
        return job_id

    def close(self):
        for w in self.workers:
            w.cancel()
        logger.info("Shut down build agent")

    async def do_job(self, job_type: JobType):
        while True:
            try:
                await self.jobhandlers[job_type]["fn"]()
            except Exception as e:
                logger.error(f"Caught exception {e}")
            logger.debug("task done")
            self.jobhandlers[job_type]["queue"].task_done()

    async def run(self):
        logger.info(f"Started build agent: [{id(asyncio.get_running_loop())}]")
        self.workers = [
            asyncio.create_task(self.do_job(job_type)) for job_type in JobType
        ]
        try:
            for worker in self.workers:
                await worker
        except Exception as e:
            logger.error(f"Exception raised: {e}")
            raise
