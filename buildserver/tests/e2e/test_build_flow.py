"""End-to-end test for the build execution pipeline"""

import asyncio

import pytest

from buildserver.api.jobs.models import JobStatus

TEST_REPO = "git@github.com:larryb02/test.git"
POLL_INTERVAL = 1  # seconds
POLL_TIMEOUT = 60  # seconds

pytestmark = pytest.mark.skip("work in progress")


async def poll_for_status(
    client, job_id: int, expected: JobStatus, timeout: int = POLL_TIMEOUT
):
    """Poll job endpoint until status matches or timeout."""
    elapsed = 0
    last_status = None
    while elapsed < timeout:
        resp = await client.get(f"/jobs/{job_id}")
        assert resp.status_code == 200
        job = resp.json()
        last_status = job["job_status"]
        if last_status == str(expected):
            return job
        if last_status == str(JobStatus.FAILED):
            raise AssertionError(f"Job {job_id} failed")
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
    raise TimeoutError(f"Job {job_id} stuck at {last_status}, expected {expected}")


@pytest.mark.asyncio
async def test_register_and_build_succeeds(client):
    """
    Register a job via the API and verify it completes successfully.

    Flow:
    1. POST /jobs/register -> creates job with QUEUED status
    2. Agent consumes from RabbitMQ -> updates to RUNNING
    3. Builder executes -> updates to SUCCEEDED/FAILED
    4. GET /jobs/{job_id} -> verify final status
    """
    # Register the job
    response = await client.post(
        "/jobs/register",
        json={"git_repository_url": TEST_REPO},
    )
    assert response.status_code == 200
    data = response.json()
    # assert data["job_status"] == str(JobStatus.QUEUED)
    job_id = data["job_id"]

    # Poll until job completes
    job = await poll_for_status(client, job_id, JobStatus.SUCCEEDED)
    assert job["job_status"] == str(JobStatus.SUCCEEDED)
