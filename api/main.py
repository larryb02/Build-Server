import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from api.repository.views import router as repository_router
from api.builds.views import router as build_router
from builder.agent import Agent
import api.config


@asynccontextmanager
async def lifespan(app: FastAPI):
    ctx = {}
    # initialize logger
    logging.basicConfig()
    logging.getLogger("uvicorn").handlers.clear()
    logger = logging.getLogger(f"{__name__}")
    logger.setLevel(api.config.LOG_LEVEL)
    ctx['logger'] = logger

    # initialize agent
    agent = Agent()
    loop = asyncio.get_event_loop()
    agent_thread = asyncio.run_coroutine_threadsafe(agent.run(), loop)
    ctx['agent'] = agent
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
app.include_router(repository_router)
app.include_router(build_router)
