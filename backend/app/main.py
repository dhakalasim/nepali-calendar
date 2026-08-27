"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import init_db
from .notifications.scheduler import shutdown_scheduler, start_scheduler
from .routers import calendar, dates, events, notifications

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    try:
        yield
    finally:
        shutdown_scheduler()


app = FastAPI(title="Nepali Calendar API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (calendar, dates, events, notifications):
    app.include_router(module.router)


@app.get("/api/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
