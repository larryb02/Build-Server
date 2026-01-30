"""Build service layer for database operations"""

import logging
from uuid import UUID

from sqlalchemy import insert, or_, select, update

from buildserver import config
from buildserver.database.core import DbSession, create_session
from buildserver.builder.builder import BuildStatus
from buildserver.api.builds.models import (
    Artifact,
    ArtifactCreate,
    Build,
    BuildCreate,
    BuildRead,
)

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(config.LOG_LEVEL)


async def register(repo: BuildCreate) -> UUID:
    """
    Add a new BUILD job to task queue, create a db record with info about this build
    """
    dbsession = create_session()
    try:
        build = BuildRead(**dict(create_build(repo, dbsession)._mapping))
        # await agent.add_job(JobType.BUILD_PROGRAM, (repo.git_repository_url, build.build_id))
        dbsession.commit()
    except Exception as e:
        logger.error("Failed to write build to db: %s", e)
        dbsession.rollback()
    dbsession.close()
    return build


def get_all_builds(dbsession: DbSession):
    stmt = select(*Build.__table__.columns)
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


def get_all_unique_builds() -> list:
    """
    Create a list of all unique builds

    A build is considered unique if b1.git_repository_url != b2.git_repository_url
    """
    db_session = create_session()
    stmt = (
        select(*Build.__table__.columns)
        .distinct(Build.git_repository_url)
        .order_by(Build.git_repository_url, Build.created_at.desc())
        .where(
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
