from fastapi import Request
from uuid import UUID
from sqlalchemy import insert, or_, select, update
from logging import Logger

from buildserver.database.core import DbSession, create_session
from buildserver.agent.agent import JobType, Agent
from buildserver.builder.builder import BuildStatus
from buildserver.api.builds.models import (
    Artifact,
    ArtifactCreate,
    Build,
    BuildCreate,
    BuildRead,
)


async def register(repo: BuildCreate, agent: Agent, logger: Logger) -> UUID:
    """
    Add a new BUILD job to task queue, create a db record with info about this build
    """
    dbsession = create_session()
    try:
        build = BuildRead(**dict(create_build(repo, dbsession)._mapping))
        job_id = await agent.add_job(JobType.BUILD_PROGRAM, (repo.git_repository_url, build.build_id))
        dbsession.commit()
    except Exception as e:
        logger.error(f"Failed to write build to db: {e}")
        dbsession.rollback()
    dbsession.close()
    return job_id, build

def get_all_builds(dbsession: DbSession):
    stmt = (
        select(*Build.__table__.columns)
    )
    try:
        records = dbsession.execute(stmt).fetchall()
    except Exception as e:
        raise e
    return records
    

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


def update_build(dbsession: DbSession, build_id, **fields):
    # kwargs = dict(fields)
    # print(f"Using these fields to update status: {}")
    stmt = (
        update(Build)
        .where(Build.build_id == build_id)
        .values(**fields)
        .returning(*Build.__table__._columns)  # return all columns
    )
    try:
        dbsession.execute(stmt)
    except Exception as e:
        raise e


async def post_process(request: Request, build_job_id: UUID):
    db_session = (
        create_session()
    )  # NOTE: have to manually create session due to being in another thread.
    # could benefit from using an async engine https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
    agent = request.state.agent
    logger = request.state.logger
    try:
        build_status, build_id = await agent.jobs[build_job_id].result
    except Exception as e:
        logger.error(f"Result Error: {e}")
        raise e
    logger.info(f"[Background Task]: Got build result {build_status}")
    try:
        update_build(
            db_session, build_id, **build_status
        )
        db_session.commit()
    except Exception as e:
        logger.error(f"Failed to update build_status in database: {e}")
    if build_status["build_status"] == BuildStatus.SUCCEEDED:
        logger.info("Build succeeded. Uploading artifacts to repository")
        try:
            await gather_artifacts(
                agent, logger, build_status["git_repository_url"], db_session
            )
        except Exception as e:
            raise e
    db_session.close()


async def gather_artifacts(
    agent: Agent, logger: Logger, repo_url: str, db_session: DbSession
):
    job_id = await agent.add_job(JobType.SEND_ARTIFACTS, repo_url)
    try:
        artifacts = await agent.jobs[job_id].result
    except Exception as e:
        logger.error(f"Result Error: {e}")
        raise e
    try:
        for artifact in artifacts:
            logger.debug(f"Processing artifact: {artifact.keys()}")
            artifact = ArtifactCreate(**artifact)
            artifact = create_artifact(artifact, db_session)
            logger.debug(f"Successfully added artifact: {artifact}")
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
        .order_by(Build.git_repository_url, Build.created_at.desc()).where(
            or_(
                Build.build_status == BuildStatus.SUCCEEDED,
                Build.build_status == BuildStatus.FAILED,
            )
        )
    )
    builds = db_session.execute(stmt).fetchall()
    builds = [BuildRead(**build._mapping) for build in builds]
    db_session.close()
    return builds
