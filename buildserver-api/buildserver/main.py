"""FastAPI application entrypoint"""

from concurrent.futures import ProcessPoolExecutor

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from buildserver.api.jobs.views import router as build_router
from buildserver.rebuilder import run as run_rebuilder

from buildserver.database.core import init_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # temporarily allowing all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(build_router)


def main():  # noqa: C0116
    init_db()
    executor = ProcessPoolExecutor()
    executor.submit(run_rebuilder)
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
