"""FastAPI application entrypoint"""

import logging
import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from . import __version__
from .api import api_router
from .api.runners.service import run_health_monitor
from .config import LOG_LEVEL
from .database.core import init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = threading.Event()
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


@app.exception_handler(404)
async def exception_404_handler(request, exc):
    return FileResponse("/dist/index.html")


app.mount("/", StaticFiles(directory="/dist", html=True), name="static")
