"""End-to-end test for the build execution pipeline"""

import pytest

from buildserver.models.jobs import JobStatus

TEST_REPO = "git@github.com:larryb02/test.git"


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
    assert data["job_status"] == str(JobStatus.QUEUED)
    job_id = data["job_id"]

    # Wait for job completion (blocking)
    resp = await client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200
    job = resp.json()

    assert job["job_status"] == str(JobStatus.SUCCEEDED)
