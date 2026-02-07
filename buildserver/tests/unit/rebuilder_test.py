from unittest.mock import patch, MagicMock
import subprocess

from buildserver import rebuilder


class TestCheckForRebuild:

    @patch("buildserver.rebuilder.requests")
    @patch("buildserver.rebuilder.get_remote_hash")
    def test_registers_rebuild_when_hashes_differ(
        self, mock_get_remote_hash, mock_requests
    ):
        mock_get_remote_hash.return_value = "b" * 40
        job = {
            "git_repository_url": "git@github.com:user/repo.git",
            "commit_hash": "a" * 40,
        }

        rebuilder.check_for_rebuild(job, "http://localhost:8000")

        mock_requests.post.assert_called_once_with(
            "http://localhost:8000/jobs/register",
            json={"git_repository_url": "git@github.com:user/repo.git"},
            timeout=5,
        )

    @patch("buildserver.rebuilder.requests")
    @patch("buildserver.rebuilder.get_remote_hash")
    def test_skips_rebuild_when_hashes_match(self, mock_get_remote_hash, mock_requests):
        hash = "a" * 40
        mock_get_remote_hash.return_value = hash
        job = {
            "git_repository_url": "git@github.com:user/repo.git",
            "commit_hash": hash,
        }

        rebuilder.check_for_rebuild(job, "http://localhost:8000")

        mock_requests.post.assert_not_called()

    @patch("buildserver.rebuilder.requests")
    @patch("buildserver.rebuilder.get_remote_hash")
    def test_skips_when_commit_hash_is_none(self, mock_get_remote_hash, mock_requests):
        job = {
            "git_repository_url": "git@github.com:user/repo.git",
            "commit_hash": None,
        }

        rebuilder.check_for_rebuild(job, "http://localhost:8000")

        mock_get_remote_hash.assert_not_called()
        mock_requests.post.assert_not_called()

    @patch("buildserver.rebuilder.requests")
    @patch("buildserver.rebuilder.get_remote_hash")
    def test_continues_when_get_remote_hash_fails(
        self, mock_get_remote_hash, mock_requests
    ):
        mock_get_remote_hash.side_effect = subprocess.CalledProcessError(1, "git")
        job = {
            "git_repository_url": "git@github.com:user/repo.git",
            "commit_hash": "a" * 40,
        }

        rebuilder.check_for_rebuild(job, "http://localhost:8000")

        mock_requests.post.assert_not_called()

    @patch("buildserver.rebuilder.requests")
    @patch("buildserver.rebuilder.get_remote_hash")
    def test_handles_register_request_failure(
        self, mock_get_remote_hash, mock_requests
    ):
        mock_get_remote_hash.return_value = "b" * 40
        mock_requests.post.side_effect = Exception("connection refused")
        mock_requests.RequestException = Exception
        job = {
            "git_repository_url": "git@github.com:user/repo.git",
            "commit_hash": "a" * 40,
        }

        # should not raise
        rebuilder.check_for_rebuild(job, "http://localhost:8000")
