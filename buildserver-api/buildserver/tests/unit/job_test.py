from datetime import datetime
from unittest.mock import MagicMock

import pytest

from buildserver.api.jobs.models import JobStatus
from buildserver.api.jobs.service import validate
from buildserver.api.jobs.service import update_job_status


class TestUpdateJobStatus:
    pass


class TestValidate:
    def test_valid_https_url_passes(self):
        validate("https://github.com/user/repo.git")

    def test_empty_url_raises(self):
        with pytest.raises(ValueError):
            validate("")

    def test_http_url_raises(self):
        with pytest.raises(ValueError):
            validate("http://github.com/user/repo.git")

    def test_ssh_url_raises(self):
        with pytest.raises(ValueError):
            validate("git@github.com:user/repo.git")

    def test_bare_domain_raises(self):
        with pytest.raises(ValueError):
            validate("github.com/user/repo.git")
