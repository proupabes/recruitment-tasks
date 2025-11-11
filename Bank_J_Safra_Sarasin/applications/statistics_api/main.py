from __future__ import annotations

from fastapi import FastAPI, Depends, Request, Query
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator
from typing import Annotated
from contextlib import asynccontextmanager
import httpx
import os

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from collections.abc import AsyncGenerator

from common.config import database_url, device_api_url
from common.db import create_engine, make_sessionmaker, DeviceRegistration
from common.device_types import DeviceType, normalize_device_type
from common.errors import make_validation_handler_for_statistics
from common.http_utils import get_client_ip
from common.logging_utils import setup_logging
from common.tools.db_bootstrap import bootstrap as db_bootstrap

logger = setup_logging("StatisticsAPI")

# --- Database (async SQLAlchemy 2.x) ---
DB_URL = database_url(default="postgresql+asyncpg://postgres:postgres@db:5432/devicesdb")
engine = create_engine(DB_URL, echo=False)
SessionLocal = make_sessionmaker(engine)

async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Proper FastAPI dependency that opens and closes AsyncSession."""
    async with SessionLocal() as session:
        yield session

# --- Lifespan: mark startup completion once basic init passes ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.startup_complete = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        ok = await db_bootstrap(engine)
        app.state.startup_complete = bool(ok)
    except Exception as e:
        logger.warning("Startup DB probe failed: %s", e)
        app.state.startup_complete = False
    yield

app = FastAPI(title="StatisticsAPI",
              version=os.getenv("API_VERSION", "1.0.0"),
              lifespan=lifespan)

# --- Models (Pydantic) ---

class LoginEvent(BaseModel):
    userKey: str = Field(..., min_length=1, max_length=255)
    deviceType: str = Field(..., min_length=1, max_length=50)

    @field_validator("userKey")
    @classmethod
    def _trim_userkey(cls, v: str) -> str:
        v2 = v.strip()
        if not v2:
            raise ValueError("userKey must not be empty")
        return v2


class StatisticsResponse(BaseModel):
    deviceType: str
    count: int


# --- Exception handlers (DRY via common) ---
@app.exception_handler(RequestValidationError)
async def _validation_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error in statistics-api: %s", exc.errors())
    return make_validation_handler_for_statistics()(request, exc)


# --- Endpoints ---

@app.post("/Log/auth")
async def log_auth(event: LoginEvent, request: Request):
    """
    Receive a login event, enrich it (normalize device, UA/IP), forward to DeviceRegistrationAPI,
    and respond with required schema.
    """
    normalized: DeviceType = normalize_device_type(event.deviceType)
    payload = {
        "userKey": event.userKey,
        "deviceType": normalized.value,
        # extra (optional) metadata for DeviceRegistrationAPI:
        "userAgent": request.headers.get("user-agent"),
        "clientIp": get_client_ip(request),
    }

    url = f"{device_api_url()}/Device/register"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json=payload)
    except Exception:
        logger.exception("Error calling DeviceRegistrationAPI")
        # Required contract: 400 with bad_request on failure
        return JSONResponse(status_code=400, content={"statusCode": 400, "message": "bad_request"})

    if resp.status_code == 200:
        return {"statusCode": 200, "message": "success"}
    else:
        # Do not leak internals; unify as bad_request
        logger.warning("DeviceRegistrationAPI responded with non-200: %s", resp.status_code)
        return JSONResponse(status_code=400, content={"statusCode": 400, "message": "bad_request"})


@app.get("/Log/auth/statistics", response_model=StatisticsResponse)
async def get_statistics(
    session: Annotated[AsyncSession, Depends(get_session)],
    deviceType: str = Query(..., min_length=1, max_length=50),
):
    """
    Return the count of registrations for a given deviceType (normalized).
    Uses direct SQL COUNT for robustness. Never 400 for unknown device types:
    they normalize to 'Unknown' and return 0 if not present.
    """
    normalized: DeviceType = normalize_device_type(deviceType)
    try:
        # Dla pełnej czytelności logów
        logger.info("Statistics query: raw=%r -> normalized=%s", deviceType, normalized.value)

        stmt = text("SELECT COUNT(*) FROM public.device_registrations WHERE device_type = :dt")
        res = await session.execute(stmt, {"dt": normalized.value})

        # Bezpiecznie: COUNT(*) zawsze 1 wiersz; scalar() jest wystarczające, ale i tak rzutujemy
        count = res.scalar()
        count_int = int(count if count is not None else 0)

        return {"deviceType": normalized.value, "count": count_int}
    except Exception:
        # 400 tylko przy realnym błędzie zapytania/DB
        logger.exception("Statistics query failed (deviceType=%r, normalized=%s)", deviceType, normalized.value)
        return JSONResponse(status_code=400, content={"deviceType": normalized.value, "count": -1})

# ---------- Probes ----------
@app.get("/livez")
async def livez():
    """Liveness: process is responsive."""
    return {"status": "ok"}


@app.get("/startupz")
async def startupz():
    """Startup: set when lifespan finished initial checks."""
    ok = bool(getattr(app.state, "startup_complete", False))
    return JSONResponse(status_code=200 if ok else 503,
                        content={"status": "ok" if ok else "starting"})


@app.get("/readyz")
async def readyz(session: Annotated[AsyncSession, Depends(get_session)]):
    """
    Readiness: DB connectivity + schema + DeviceRegistrationAPI readiness.
    """
    db_ok = False
    schema_ok = False
    dep_ok = False

    # 1) DB connectivity and schema presence
    try:
        await session.execute(text("SELECT 1"))
        db_ok = True

        res = await session.execute(text("SELECT to_regclass('public.device_registrations')"))
        schema_ok = bool(res.scalar())
    except Exception:
        logger.warning("Readiness DB/schema check failed", exc_info=True)

    # 2) Dependency readiness (DeviceRegistrationAPI)
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{device_api_url()}/readyz")
            dep_ok = 200 <= r.status_code < 400
    except Exception:
        logger.warning("Readiness dependency check failed", exc_info=True)

    ok = db_ok and schema_ok and dep_ok
    return JSONResponse(
        status_code=200 if ok else 503,
        content={
            "status": "ok" if ok else "fail",
            "db": db_ok,
            "schema": schema_ok,
            "deviceRegistration": dep_ok,
        },
    )


@app.get("/healthz")
async def healthz(session: Annotated[AsyncSession, Depends(get_session)]):
    """Back-compat alias -> readiness."""
    return await readyz(session)
