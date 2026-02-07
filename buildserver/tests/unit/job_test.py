from datetime import datetime
from unittest.mock import MagicMock

from buildserver.api.builds.models import JobStatus
from buildserver.services.builds import update_job_status


class TestUpdateJobStatus:

    def test_returns_updated_job_when_found(self):
        # TODO: Mock with pytest man <facepalm>
        mock_record = MagicMock()
        mock_record._mapping = {
            "job_id": 1,
            "git_repository_url": "git@github.com:user/repo.git",
            "commit_hash": "abc123",
            "job_status": JobStatus.RUNNING,
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        }

        mock_result = MagicMock()
        mock_result.one_or_none.return_value = mock_record

        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result

        result = update_job_status(mock_session, job_id=1, new_status=JobStatus.RUNNING)

        assert result is not None
        assert result.job_id == 1
        assert result.job_status == JobStatus.RUNNING
        assert result.git_repository_url == "git@github.com:user/repo.git"
        mock_session.execute.assert_called_once()

    def test_returns_none_when_job_not_found(self):
        mock_result = MagicMock()
        mock_result.one_or_none.return_value = None

        mock_session = MagicMock()
        mock_session.execute.return_value = mock_result

        result = update_job_status(
            mock_session, job_id=999, new_status=JobStatus.FAILED
        )

        assert result is None
        mock_session.execute.assert_called_once()
