"""FastAPI application entrypoint"""

from concurrent.futures import ProcessPoolExecutor
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from buildserver.agent.agent import Agent
from buildserver.api.builds.views import router as build_router

from buildserver.config import Config
from buildserver.database.core import init_db

config = Config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ctx = {}
    logging.basicConfig()
    logging.getLogger("uvicorn").handlers.clear()
    logger = logging.getLogger(f"{__name__}")
    logger.setLevel(config.LOG_LEVEL)
    ctx["logger"] = logger
    yield ctx


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # temporarily allowing all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(build_router)


def _start_agent():
    """Entry point for agent subprocess."""
    Agent().start()


def main():  # noqa: C0116
    init_db()
    executor = ProcessPoolExecutor()
    executor.submit(_start_agent)
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
