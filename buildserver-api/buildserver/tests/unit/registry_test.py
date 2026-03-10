from datetime import datetime, timedelta

from buildserver.api.registry.service import Registry


class TestValidateRegistrationToken:

    def setup_method(self):
        self.registry = Registry()

    def test_happy_path(self):
        token = "valid-token"
        self.registry._pending_tokens[token] = datetime.now() + timedelta(minutes=10)
        assert self.registry._validate_registration_token(token) is True

    def test_expired_token(self):
        token = "expired-token"
        self.registry._pending_tokens[token] = datetime.now() - timedelta(minutes=1)
        assert self.registry._validate_registration_token(token) is False

    def test_nonexistent_token(self):
        assert self.registry._validate_registration_token("nonexistent") is False
