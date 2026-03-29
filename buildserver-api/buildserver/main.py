"""FastAPI application entrypoint"""

import logging
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .api import api_router
from .api.runners.service import run_health_monitor
from .config import LOG_LEVEL
from .database.core import init_db
from .rebuilder import run as run_rebuilder

logging.basicConfig(level=LOG_LEVEL, force=True)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = threading.Event()
    rebuilder_thread = threading.Thread(
        target=run_rebuilder, args=(stop_event,), daemon=True
    )
    rebuilder_thread.start()
    health_monitor_thread = threading.Thread(
        target=run_health_monitor, args=(stop_event,), daemon=True
    )
    health_monitor_thread.start()
    yield
    stop_event.set()


app = FastAPI(title="Build Server", lifespan=lifespan, version=__version__)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # temporarily allowing all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router)


def main():  # noqa: C0116
    init_db()
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
