import secrets

from sqlalchemy import insert

from buildserver.database.core import DbSession
from buildserver.api.auth.models import PendingRegistrationToken


def generate_registration_token(dbsession: DbSession) -> str:
    """
    Generate 32 bit registration token add to pending registration tokens table
    """
    token = secrets.token_hex()
    stmt = insert(PendingRegistrationToken).values()
    return token


def valid_registration_token() -> bool:
    return False
