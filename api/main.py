from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.repository.views import router as repository_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # temporarily allowing all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(repository_router)
