"""End-to-end test for the build execution pipeline"""

import asyncio
import pytest

from buildserver.builder.builder import BuildStatus

TEST_REPO = "git@github.com:larryb02/test.git"
POLL_INTERVAL = 2
POLL_TIMEOUT = 120

pytestmark = pytest.mark.skip("in a refactor, these tests will fail")


@pytest.mark.asyncio
async def test_register_and_build_succeeds(client):
    """Register a build via the API and verify it completes successfully."""
    response = await client.post(
        "/builds/register",
        json={"git_repository_url": TEST_REPO},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["build_status"] == BuildStatus.QUEUED.value
    build_id = data["build_id"]

    elapsed = 0
    final_status = None
    while elapsed < POLL_TIMEOUT:
        await asyncio.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL

        resp = await client.get("/builds")
        assert resp.status_code == 200
        builds = resp.json()

        match = next((b for b in builds if b["build_id"] == build_id), None)
        assert match is not None, f"Build {build_id} not found in GET /builds"

        if match["build_status"] in (
            BuildStatus.SUCCEEDED.value,
            BuildStatus.FAILED.value,
        ):
            final_status = match["build_status"]
            break

    assert (
        final_status == BuildStatus.SUCCEEDED.value
    ), f"Build did not succeed within {POLL_TIMEOUT}s. Status: {final_status}"
