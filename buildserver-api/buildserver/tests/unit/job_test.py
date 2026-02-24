from datetime import datetime
from unittest.mock import MagicMock

import pytest
from fastapi.exceptions import RequestValidationError

from buildserver.api.jobs.models import JobStatus
from buildserver.api.jobs.service import validate
from buildserver.api.jobs.service import update_job_status


class TestUpdateJobStatus:
    pass


class TestValidate:
    def test_valid_https_url_passes(self):
        validate("https://github.com/user/repo.git")

    def test_empty_url_raises(self):
        with pytest.raises(RequestValidationError):
            validate("")

    def test_http_url_raises(self):
        with pytest.raises(RequestValidationError):
            validate("http://github.com/user/repo.git")

    def test_ssh_url_raises(self):
        with pytest.raises(RequestValidationError):
            validate("git@github.com:user/repo.git")

    def test_bare_domain_raises(self):
        with pytest.raises(RequestValidationError):
            validate("github.com/user/repo.git")
