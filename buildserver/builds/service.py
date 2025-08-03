from fastapi import Request
from fastapi.exceptions import RequestValidationError
from uuid import UUID
from sqlalchemy import insert, select
from logging import Logger

from buildserver.database.core import Session, DbSession, create_session
from buildserver.builder.agent import JobType, Agent, Status
from buildserver.builder.builder import BuildStatus
from buildserver.builds.models import (
    Artifact,
    ArtifactCreate,
    Build,
    BuildCreate,
    BuildRead,
)


def validate(repo_url: str):
    if repo_url == "":
        raise RequestValidationError("Url may not be blank")


async def register(repo: str, agent: Agent) -> UUID:
    job_id = await agent.add_job(JobType.BUILD_PROGRAM, repo)
    return job_id


def create_build(build: BuildCreate, dbsession: DbSession):
    stmt = (
        insert(Build)
        .values(
            git_repository_url=build.git_repository_url, build_status=BuildStatus.QUEUED
        )
        .returning(
            Build.git_repository_url,
            Build.build_id,
            Build.build_status,
            Build.commit_hash,
            Build.created_at,
        )
    )
    try:
        record = dbsession.execute(stmt).one_or_none()
    except Exception as e:
        raise e
    return record


def create_artifact(artifact: ArtifactCreate, dbsession: DbSession):
    stmt = (
        insert(Artifact)
        .values(
            artifact_file_name=artifact.artifact_file_name,
            git_repository_url=artifact.git_repository_url,
            commit_hash=artifact.commit_hash,
            artifact_path=artifact.artifact_path,
        )
        .returning(
            Artifact.artifact_id,
            Artifact.artifact_file_name,
            Artifact.commit_hash,
            Artifact.git_repository_url,
        )
    )
    try:
        record = dbsession.execute(stmt).one_or_none()
    except Exception as e:
        raise e
    return record


async def post_process(request: Request, build_job_id: UUID):
    db_session = (
        create_session()
    )  # NOTE: have to manually create session due to being in another thread.
    # could benefit from using an async engine https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
    agent = request.state.agent
    logger = request.state.logger
    try:
        build_status = await agent.jobs[build_job_id].result
    except Exception as e:
        logger.error(f"Result Error: {e}")
        return
    logger.info(f"[Background Task]: Got build result {build_status}")
    # can update status here
    # -----------------------
    # now we gather artifacts
    if build_status["status"] == BuildStatus.SUCCEEDED:
        logger.info("Build succeeded. Uploading artifacts to repository")
        try:
            await gather_artifacts(
                agent, logger, build_status["git_repository_url"], db_session
            )
        except Exception as e:
            raise e


async def gather_artifacts(
    agent: Agent, logger: Logger, repo_url: str, db_session: DbSession
):
    job_id = await agent.add_job(JobType.SEND_ARTIFACTS, repo_url)
    default_repository_id = 1  # Can assume that only one artifact repository will exist
    try:
        artifacts = await agent.jobs[job_id].result
    except Exception as e:
        logger.error(f"Result Error: {e}")
        raise e
    try:
        for artifact in artifacts:
            logger.debug(f"Processing artifact: {artifact.keys()}")
            artifact = ArtifactCreate(
                **artifact, artifact_repository_id=default_repository_id
            )
            artifact = create_artifact(artifact, db_session)
            logger.info(f"Successfully added artifact: {artifact}")
        db_session.commit()  # commit after all operations are successful
    except Exception as e:
        logger.error(f"Failed to create artifact: {e}")
        db_session.rollback()
    db_session.close()


def get_all_unique_builds() -> list:
    """
    Create a list of all unique builds

    A build is considered unique if b1.git_repository_url != b2.git_repository_url
    """
    db_session = create_session()
    stmt = (
        select(*Build.__table__.columns)
        .distinct(Build.git_repository_url)
        .order_by(Build.git_repository_url, Build.created_at)
        .where(
            Build.build_status == BuildStatus.SUCCEEDED
            or Build.build_status == BuildStatus.FAILED
        )
    )
    builds = db_session.execute(stmt).fetchall()
    builds = [BuildRead(**build._mapping) for build in builds]
    db_session.close()
    return builds
