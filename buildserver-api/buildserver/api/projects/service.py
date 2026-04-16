"""Project and pipeline trigger service layer"""

import logging

from sqlalchemy import delete, insert, select

from ...database.core import DbSession
from ...pipeline.spec import parse_spec
from ...utils import get_remote_hash
from ..pipelines.models import Pipeline, PipelineJob, PipelineStatus
from .models import Project, ProjectCreate

logger = logging.getLogger(__name__)


def create_project(project: ProjectCreate, dbsession: DbSession) -> Project:
    stmt = (
        insert(Project)
        .values(name=project.name, git_repository_url=project.git_repository_url)
        .returning(Project)
    )
    return dbsession.scalars(stmt).one()


def get_all_projects(dbsession: DbSession) -> list[Project]:
    return list(dbsession.scalars(select(Project)).all())


def get_project_by_id(project_id: int, dbsession: DbSession) -> Project | None:
    return dbsession.get(Project, project_id)


def delete_project(project_id: int, dbsession: DbSession) -> bool:
    result = dbsession.execute(
        delete(Project)
        .where(Project.project_id == project_id)
        .returning(Project.project_id)
    )
    return result.one_or_none() is not None


def trigger_pipeline(project: Project, branch: str, dbsession: DbSession) -> Pipeline:
    """
    Fetch the latest commit on branch, parse the pipeline spec, and create
    Pipeline + PipelineJob + Step rows in a single transaction.

    Raises:
        SpecError: If the spec cannot be fetched or parsed.
        DBAPIError: On database failure.
    """
    commit_hash = get_remote_hash(project.git_repository_url)
    spec = parse_spec(project.git_repository_url, commit_hash)

    pipeline = dbsession.scalars(
        insert(Pipeline)
        .values(
            project_id=project.project_id,
            branch=branch,
            commit_hash=commit_hash,
            status=PipelineStatus.QUEUED,
        )
        .returning(Pipeline)
    ).one()

    dbsession.execute(
        insert(PipelineJob),
        [
            {
                "pipeline_id": pipeline.pipeline_id,
                "name": job_spec.name,
                "commands": job_spec.commands,
                "status": PipelineStatus.QUEUED,
            }
            for job_spec in spec.jobs
        ],
    )

    logger.info(
        "Triggered pipeline %s for %s@%s (%d jobs)",
        pipeline.pipeline_id,
        project.git_repository_url,
        branch,
        len(spec.jobs),
    )
    return pipeline
