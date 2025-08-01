from fastapi.exceptions import RequestValidationError
from uuid import UUID
from sqlalchemy import insert

from buildserver.database.core import Session
from buildserver.builder.agent import JobType
from buildserver.builder.builder import BuildStatus
from buildserver.builds.models import Artifact, ArtifactCreate


def validate(repo_url):
    if repo_url == "":
        raise RequestValidationError("Url may not be blank")


async def register(repo: str, agent) -> UUID:
    job_id = await agent.add_job(JobType.BUILD_PROGRAM, repo)
    return job_id


def create_artifact(artifact: ArtifactCreate, dbsession):
    stmt = (
        insert(Artifact)
        .values(
            artifact_name=artifact.artifact_file_name,
            artifact_file=artifact.artifact_file_contents,
            artifact_repository_id=artifact.artifact_repository_id,
            git_repository_url=artifact.git_repository_url,
            commit_hash=artifact.commit_hash,
        )
        .returning(
            Artifact.artifact_id,
            Artifact.artifact_name,
            Artifact.artifact_repository_id,
            Artifact.commit_hash,
            Artifact.git_repository_url,
            Artifact.artifact_file,
        )
    )
    try:
        record = dbsession.execute(stmt).one_or_none()
    except Exception as e:
        raise e
    return record


async def post_process(request, build_job_id):
    db_session = (
        Session()
    )  # have to manually create session due to being in another thread.
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


async def gather_artifacts(agent, logger, repo_url, db_session):
    job_id = await agent.add_job(JobType.SEND_ARTIFACTS, repo_url)
    default_repository_id = 7  # Can assume that only one artifact repository will exist
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
