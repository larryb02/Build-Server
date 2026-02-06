"""Build agent that manages job queues and workers"""

import logging

import requests

from buildserver.agent.builder import builder
from buildserver.config import Config
from buildserver.models.jobs import Job, JobStatus
from buildserver.rmq.rmq import RabbitMQConsumer

config = Config()

logging.basicConfig()
logger = logging.getLogger(f"{__name__}")
logger.setLevel(config.LOG_LEVEL)

TIMEOUT = config.TIMEOUT


# class JobType(enum.Enum):
#     BUILD_PROGRAM = "BUILD_PROGRAM"
#     SEND_ARTIFACTS = "SEND_ARTIFACTS"


# class Agent:
#     """
#     Long running task that manages jobs and workers
#     """

#     def __init__(self):
#         self.build_job_queue = asyncio.Queue()
#         self.artifact_job_queue = asyncio.Queue()

#         # NOTE: predefined job handlers due to time constraints and simple needs
#         # the next logical step is to create a message queue system
#         # to allow for dynamic job types and handlers if the need ever arises for more
#         self.jobhandlers = {
#             JobType.BUILD_PROGRAM: {
#                 "fn": self.__build_program,
#                 "queue": self.build_job_queue,
#             },
#             JobType.SEND_ARTIFACTS: {
#                 "fn": self.__send_artifacts,
#                 "queue": self.artifact_job_queue,
#             },
#         }

#     async def __build_program(self):
#         """
#         Run the builder while updating the build status throughout the process.
#         If build is successful add a task to task queue to gather artifacts
#         """

#         async def update_db(**fields):
#             logger.debug("Updating build-%s in database", build_id)
#             db_session = create_session()
#             try:
#                 await asyncio.to_thread(update_build, db_session, build_id, **fields)
#                 db_session.commit()
#             except Exception as e:
#                 logger.error("Failed to update database from async: %s", e)
#                 db_session.rollback()
#             db_session.close()

#         try:
#             job_id, (repo_url, build_id) = await self.build_job_queue.get()
#             logger.info("[Worker-%s] Building: %s", job_id, repo_url)
#             await update_db(build_status=builder.BuildStatus.RUNNING)
#             build_metadata = builder.run(repo_url)
#             logger.debug("Build complete updating status in db")
#             await update_db(**build_metadata)
#             if build_metadata["build_status"] == builder.BuildStatus.SUCCEEDED:
#                 await self.add_job(JobType.SEND_ARTIFACTS, repo_url)
#         except Exception as e:
#             logger.error("[Worker-%s] Build fail: %s", job_id, e)
#             raise e

#     async def __send_artifacts(self):
#         """
#         Collect artifacts and store in artifact repository with a reference in the database
#         """
#         job_id, repo_url = await self.artifact_job_queue.get()
#         logger.info(
#             "[%s Worker-%s] Gathering artifacts for build: %s",
#             self.__send_artifacts.__name__,
#             job_id,
#             repo_url,
#         )
#         try:
#             artifacts = artifactstore.gather_artifacts(repo_url)
#             for artifact in artifacts:
#                 db_session = create_session()
#                 try:
#                     await asyncio.to_thread(
#                         create_artifact, ArtifactCreate(**artifact), db_session
#                     )
#                     db_session.commit()
#                     logger.debug("Successfully added artifact to database")
#                 except Exception as e:
#                     logger.error("Failed to write artifact to database: %s", e)
#                     db_session.rollback()
#                 db_session.close()
#         except Exception as e:
#             logger.error(
#                 "[%s Worker-%s] Job failed: %s",
#                 self.__send_artifacts.__name__,
#                 job_id,
#                 e,
#             )
#             raise e

#     async def add_job(self, job_type: JobType, job: any) -> UUID:
#         job_id = uuid4()  # using job id's to trace workers while debugging
#         logger.info("Added new job: [%s-%s]: %s", job_id, job_type, job)
#         try:
#             await self.jobhandlers[job_type]["queue"].put((job_id, job))
#         except Exception as e:
#             logger.error("Failed to add job to queue: %s", e)
#             raise e
#         logger.debug(
#             "[%s] Queue Size: %d", job_type, self.jobhandlers[job_type]["queue"].qsize()
#         )
#         return job_id

#     def close(self):
#         for w in self.workers:
#             w.cancel()
#         logger.info("Shut down build agent")

#     async def do_job(self, job_type: JobType):
#         while True:
#             try:
#                 await self.jobhandlers[job_type]["fn"]()
#             except Exception as e:
#                 logger.error("Caught exception %s", e)
#             logger.debug("task done")
#             self.jobhandlers[job_type]["queue"].task_done()

#     async def run(self):
#         logger.info("Started build agent: [%d]", id(asyncio.get_running_loop()))
#         self.workers = [
#             asyncio.create_task(self.do_job(job_type)) for job_type in JobType
#         ]
#         try:
#             for worker in self.workers:
#                 await worker
#         except Exception as e:
#             logger.error("Exception raised: %s", e)
#             raise

# def _run():
#     agent = Agent()
#     asyncio.run(agent.run())

BUILD_QUEUE = "build_jobs"
# NOTE: hack for now will store in config once agent becomes separate binary
API_ENDPOINT = "localhost:8000"
# create a class called 'Agent' (for now)
# maintain a connection to rabbitmq [x]
# what should behavior be if connection to rabbitmq fails
# -> should not kill the process, continuously attempt to reconnect [x]
# make sure queues are durable
# when does agent get initialized? -> module scope for now,
# don't need multiple instances just a singleton [x]
# verify body matches schema
# how do build jobs get invoked?
# -> [consume from queue -> validate
# -> update active jobs -> builder executes -> report status back to API]
# run this asynchronously
# will want to limit number of jobs being performed at a time
# how will shutdown be handled? - command line, ctrl-c, kill


_rmq = RabbitMQConsumer()
results = []
active_jobs: list[Job] = []


def _on_message(body: bytes):
    logger.info("received data %s", body)
    job = Job.model_validate_json(body)
    # since queue limits amount of messages consumed
    # should be fine to immediately start executing a job
    active_jobs.append(job)
    # from here agent needs to update status will just make calls to API for now
    # NOTE: for first iteration this is fine, ideally want to stream here
    requests.patch(
        f"{API_ENDPOINT}/jobs/{job.job_id}",
        json={"status_update": JobStatus.RUNNING},
        timeout=5,
    )
    try:
        # NOTE: currently not very 'integration testable'
        run_status = builder.run(job.git_repository_url)
        # update with final status here
        requests.patch(
            f"{API_ENDPOINT}/jobs/{job.job_id}",
            json={"status_update": run_status["status"]},
            timeout=5,
        )
    # TODO: Bad.
    except OSError as e:
        logger.error("OSError %s", e)


def start():
    """
    Initialize the build agent.
    """
    logger.info("starting agent...")
    try:
        # NOTE: blocking connection is fine until agent has more things to do
        _rmq.start(BUILD_QUEUE, _on_message)
    except KeyboardInterrupt:
        stop()


def stop():
    """Stop the agent and close the RabbitMQ connection."""
    logger.info("stopping agent...")
    _rmq.stop()


if __name__ == "__main__":
    start()
