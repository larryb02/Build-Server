import logging
import threading

import grpc
from protos import scheduler_pb2, scheduler_pb2_grpc
from sqlalchemy.exc import DBAPIError
from sqlalchemy import select, update

from buildserver.config import GRPC_PORT
from buildserver.database.core import session_context
from buildserver.api.jobs.models import Job, JobStatus
from buildserver.api.runners.models import Runner

logger = logging.getLogger(__name__)


class Scheduler(scheduler_pb2_grpc.SchedulerServicer):
    def __init__(self):
        self._channel = grpc.insecure_channel(f"localhost:{GRPC_PORT}")
        self._lock = threading.Lock()

    def RequestJob(self, request, context):
        """Schedule a runner to execute job"""
        # NOTE: locking entire function for now -- maybe later
        # i can make the scope finer grained
        with self._lock:
            try:
                # make sure runner fits some set of criteria then assign job if there is one
                logger.debug("JobRequest from %s", request.runner_token)
                with session_context() as session:
                    # NOTE: need to check runner capacity as well
                    # -- just revisit data model to support this
                    # get runner metadata
                    # TODO: convert this to a service function
                    runner = (
                        session.query(Runner)
                        .filter(Runner.runner_token_hash == request.runner_token)
                        .first()
                    )
                    stmt = (
                        select(Job)
                        .where(Job.job_status == JobStatus.QUEUED)
                        .where(Job.runner_id == None)
                    )
                    res = session.scalars(stmt).first()
                    if not res:
                        logger.debug("no jobs")
                        return scheduler_pb2.JobResponse()
                    logger.debug("assigning job: %s", res)
                    stmt = (
                        update(Job)
                        .where(Job.job_id == res.job_id)
                        .values(runner_id=runner.runner_id)
                    )
                    session.execute(stmt)
                return scheduler_pb2.JobResponse(
                    job=scheduler_pb2.JobInfo(
                        job_id=res.job_id, git_repository_url=res.git_repository_url
                    )
                )
            except (grpc.RpcError, DBAPIError) as exc:
                logger.error(exc)
                context.abort(grpc.StatusCode.INTERNAL, "failed to process request")
