from datetime import datetime, timedelta
from unittest.mock import MagicMock

from buildserver.api.runners.service import validate_registration_token
from buildserver.api.runners.models import PendingTokens


class TestValidateRegistrationToken:

    def _make_session(self, token, expires_at):
        pending = PendingTokens(
            token=token, created_at=datetime.now(), expires_at=expires_at
        )
        session = MagicMock()
        session.scalars.return_value.first.return_value = pending
        return session

    def test_happy_path(self):
        token = "valid-token"
        session = self._make_session(token, datetime.now() + timedelta(minutes=10))
        assert validate_registration_token(token, session) is True

    def test_expired_token(self):
        token = "expired-token"
        session = self._make_session(token, datetime.now() - timedelta(minutes=1))
        assert validate_registration_token(token, session) is False

    def test_nonexistent_token(self):
        session = MagicMock()
        session.scalars.return_value.first.return_value = None
        assert validate_registration_token("nonexistent", session) is False
