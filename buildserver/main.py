"""FastAPI application entrypoint"""

from concurrent.futures import ProcessPoolExecutor
import uvicorn
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from buildserver.agent import agent
from buildserver.api.builds.views import router as build_router

# from buildserver.agent.agent import Agent
# from buildserver.builder.rebuilder import Rebuilder
from buildserver.config import Config
from buildserver.database.core import init_db

config = Config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ctx = {}
    # initialize logger
    logging.basicConfig()
    logging.getLogger("uvicorn").handlers.clear()
    logger = logging.getLogger(f"{__name__}")
    logger.setLevel(config.LOG_LEVEL)
    ctx["logger"] = logger

    # initialize agent
    # agent = Agent()
    # loop = asyncio.get_event_loop()
    # asyncio.run_coroutine_threadsafe(agent.run(), loop)
    # ctx["agent"] = agent

    # # initialize rebuilder
    # rebuilder = Rebuilder(agent=agent)
    # asyncio.run_coroutine_threadsafe(rebuilder.run(), loop)
    yield ctx

    # shutdown
    # agent.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # temporarily allowing all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(build_router)


def main():
    init_db()
    executor = ProcessPoolExecutor()
    executor.submit(agent.start)
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
