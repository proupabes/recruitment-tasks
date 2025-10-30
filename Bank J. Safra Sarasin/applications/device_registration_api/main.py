from __future__ import annotations

from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator
from typing import Annotated, Optional
import os

from contextlib import asynccontextmanager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from collections.abc import AsyncGenerator

from common.config import database_url
from common.db import create_engine, make_sessionmaker, session_scope, DeviceRegistration
from common.device_types import DeviceType, normalize_device_type
from common.errors import make_validation_handler_for_device
from common.http_utils import get_client_ip
from common.logging_utils import setup_logging
from common.tools.db_bootstrap import bootstrap as db_bootstrap

logger = setup_logging("DeviceRegistrationAPI")

# --- Database (async SQLAlchemy 2.x) ---
DB_URL = database_url(default="postgresql+asyncpg://postgres:postgres@db:5432/devicesdb")
engine = create_engine(DB_URL, echo=False)
SessionLocal = make_sessionmaker(engine)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an AsyncSession and closes it."""
    async with SessionLocal() as session:
        yield session

# --- Lifespan: mark startup completion once basic init passes ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.startup_complete = False
    try:
        # 1) Ensure DB is reachable quickly
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

        # 2) Bootstrap schema (idempotent, advisory lock)
        ok = await db_bootstrap(engine)
        if not ok:
            # keep startupz=503; readiness will also fail
            app.state.startup_complete = False
        else:
            app.state.startup_complete = True
    except Exception as e:
        logger.warning("Startup DB probe failed: %s", e)
        app.state.startup_complete = False
    yield

# Then create app with lifespan:
app = FastAPI(title="DeviceRegistrationAPI",
              version=os.getenv("API_VERSION", "0.0.1"),
              lifespan=lifespan)

# --- Models (Pydantic) ---
class DeviceRegisterRequest(BaseModel):
    userKey: str = Field(..., min_length=1, max_length=255)
    deviceType: str = Field(..., min_length=1, max_length=50)
    # optional metadata (allowed but not required)
    userAgent: Optional[str] = Field(default=None, max_length=1024)
    clientIp: Optional[str] = Field(default=None, max_length=45)

    @field_validator("userKey")
    @classmethod
    def _trim_userkey(cls, v: str) -> str:
        v2 = v.strip()
        if not v2:
            raise ValueError("userKey must not be empty")
        return v2

# --- Exception handlers ---
@app.exception_handler(RequestValidationError)
async def _validation_handler(request: Request, exc: RequestValidationError):
    # Return {"statusCode": 400}
    return make_validation_handler_for_device()(request, exc)

# ---------- Probes ----------
@app.get("/livez")
async def livez():
    """Liveness: do NOT check external deps. If can respond, alive."""
    return {"status": "ok"}

@app.get("/startupz")
async def startupz():
    """Startup: only OK when startup initialization has completed."""
    ok = bool(getattr(app.state, "startup_complete", False))
    return JSONResponse(status_code=200 if ok else 503,
                        content={"status": "ok" if ok else "starting"})

@app.get("/readyz")
async def readyz(session: Annotated[AsyncSession, Depends(get_session)]):
    """
    Readiness: database must be reachable and required schema must exist.
    """
    try:
        # 1) DB connectivity
        await session.execute(text("SELECT 1"))

        # 2) Schema/table presence (bootstrap creates it; here we verify)
        res = await session.execute(text("SELECT to_regclass('public.device_registrations')"))
        table_ok = bool(res.scalar())

        if not table_ok:
            return JSONResponse(
                status_code=503,
                content={"status": "fail", "reason": "schema_missing"}
            )

        return {"status": "ok"}
    except Exception:
        logger.warning("Readiness database/schema check failed", exc_info=True)
        return JSONResponse(status_code=503, content={"status": "fail"})

@app.get("/healthz")
async def healthz(session: Annotated[AsyncSession, Depends(get_session)]):
    """Back-compat alias -> readiness."""
    return await readyz(session)  # reuse the same logic

# --- Endpoints ---
@app.post("/Device/register")
async def register_device(payload: DeviceRegisterRequest, request: Request):
    """
    Insert an event into the database. Accepts optional metadata (userAgent, clientIp).
    Unknown device types are normalized to 'Unknown'.
    """
    normalized: DeviceType = normalize_device_type(payload.deviceType)

    # Prefer explicit clientIp passed by caller, otherwise derive from request
    client_ip = payload.clientIp or get_client_ip(request)

    # Persist
    async with session_scope(SessionLocal) as session:
        try:
            session.add(
                DeviceRegistration(
                    user_key=payload.userKey,
                    device_type=normalized.value,
                    user_agent=payload.userAgent,
                    client_ip=client_ip,
                )
            )
            # commit is handled by session_scope
        except Exception:
            logger.exception("Database insert failed")
            return JSONResponse(status_code=400, content={"statusCode": 400})

    return {"statusCode": 200}
