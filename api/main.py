import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.repository.views import router as repository_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    ctx = {}
    # initialize logger
    logging.basicConfig()
    logging.getLogger("uvicorn").handlers.clear()
    logger = logging.getLogger(f"{__name__}")
    logger.setLevel(logging.INFO)
    ctx['logger'] = logger
    yield ctx


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # temporarily allowing all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(repository_router)
