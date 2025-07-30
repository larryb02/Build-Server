import asyncio
from collections import defaultdict
import enum
import logging
from uuid import uuid4, UUID

from builder.builder import Builder

logging.basicConfig()


class Agent:
    """
    Long running process that assigns jobs from task queue to workers
    """

    STATUS = enum.Enum("STATUS", ["QUEUED", "RUNNING", "FAILED", "SUCCEEDED"])

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}")
        self.logger.setLevel(logging.INFO)
        self.job_queue = asyncio.Queue()
        self.jobs = defaultdict()

    async def add_job(self, job) -> UUID:
        job_id = uuid4()
        self.logger.info("Added new job: [%s] %s", job_id, job)
        await self.job_queue.put((job_id, job))
        self.jobs[job_id] = Agent.STATUS.QUEUED
        return job_id

    def close(self):
        for w in self.workers:
            w.cancel()
        self.logger.info("Shut down build agent")

    async def do_job(self):
        while True:
            job_id, repo_url = await self.job_queue.get()
            self.jobs[job_id] = Agent.STATUS.RUNNING
            self.logger.info(f"[Worker-[{job_id}]] Building: {repo_url}")
            b = Builder()
            try:
                b.run(repo_url)
            except Exception as e:
                # report failure
                self.jobs[job_id] = Agent.STATUS.FAILED
                print("Job Failed")
                raise e
            # if succeeded
            print("Job Succeeded")
            self.jobs[job_id] = Agent.STATUS.SUCCEEDED
            self.job_queue.task_done()

    async def run(self):
        self.logger.info("Started build agent")
        self.workers = [asyncio.create_task(self.do_job()) for _ in range(3)]
