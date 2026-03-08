import logging

import grpc
from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from protos import registry_pb2, registry_pb2_grpc

from buildserver.api.runners.models import RegistrationTokenResponse
from buildserver.config import GRPC_PORT

router = APIRouter(prefix="/runners")
logger = logging.getLogger(__name__)

_channel = grpc.insecure_channel(f"localhost:{GRPC_PORT}")
_registry = registry_pb2_grpc.RegistryStub(_channel)


@router.post("/register", response_model=RegistrationTokenResponse)
def register_runner():
    """Generate a runner registration token."""
    try:
        response = _registry.GenerateRegistrationToken(
            registry_pb2.GenerateRegistrationTokenRequest()
        )
        return RegistrationTokenResponse(
            token=response.token,
            created_at=response.created_at.ToDatetime(),
            expires_at=response.expires_at.ToDatetime(),
        )
    except grpc.RpcError as e:
        logger.error("gRPC error generating token: %s", e)
        raise HTTPException(status_code=500)
