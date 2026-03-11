"""FastAPI application entrypoint"""

import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

import grpc
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from grpc_reflection.v1alpha import reflection
from protos import registry_pb2, registry_pb2_grpc

from buildserver.api.jobs.views import router as build_router
from buildserver.api.runners.views import router as runners_router
from buildserver.config import GRPC_PORT, LOG_LEVEL
from buildserver.database.core import init_db
from buildserver.rebuilder import run as run_rebuilder
from buildserver.api.registry.service import Registry

logging.basicConfig(level=LOG_LEVEL, force=True)
logger = logging.getLogger(__name__)


def _create_grpc_server() -> grpc.Server:
    server = grpc.server(ThreadPoolExecutor(max_workers=10))
    registry = Registry()
    registry.start()
    registry_pb2_grpc.add_RegistryServicer_to_server(registry, server)
    reflection.enable_server_reflection(
        (
            registry_pb2.DESCRIPTOR.services_by_name["Registry"].full_name,
            reflection.SERVICE_NAME,
        ),
        server,
    )
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    return server


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = threading.Event()
    rebuilder_thread = threading.Thread(
        target=run_rebuilder, args=(stop_event,), daemon=True
    )
    rebuilder_thread.start()
    grpc_server = _create_grpc_server()
    grpc_server.start()
    logger.info("gRPC server started on port %s", GRPC_PORT)
    yield
    stop_event.set()
    grpc_server.stop(grace=None)
    logger.info("gRPC server stopped")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # temporarily allowing all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(build_router)
app.include_router(runners_router)


def main():  # noqa: C0116
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
