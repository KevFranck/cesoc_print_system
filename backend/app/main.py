from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app import models as _models  # noqa: F401  # force l'enregistrement de toutes les tables SQLAlchemy


@asynccontextmanager
async def lifespan(_: FastAPI):
    db = SessionLocal()
    try:
        init_db(db)
    finally:
        db.close()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}
