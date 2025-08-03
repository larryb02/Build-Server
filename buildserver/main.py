import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from buildserver.builds.views import router as build_router
from buildserver.builder.agent import Agent
from buildserver.builder.rebuilder import Rebuilder
from buildserver.config import LOG_LEVEL


@asynccontextmanager
async def lifespan(app: FastAPI):
    ctx = {}
    # initialize logger
    logging.basicConfig()
    logging.getLogger("uvicorn").handlers.clear()
    logger = logging.getLogger(f"{__name__}")
    logger.setLevel(LOG_LEVEL)
    ctx["logger"] = logger

    # initialize agent
    agent = Agent()
    loop = asyncio.get_event_loop()
    agent_thread = asyncio.run_coroutine_threadsafe(agent.run(), loop)
    ctx["agent"] = agent

    # initialize rebuilder
    rebuilder = Rebuilder(agent=agent)
    asyncio.run_coroutine_threadsafe(rebuilder.run(), loop)
    yield ctx

    # shutdown
    agent.close()
    agent_thread.cancel()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # temporarily allowing all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(build_router)
