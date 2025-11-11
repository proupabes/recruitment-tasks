"""
Database bootstrap (idempotent) for initial schema creation.

- Safe to call multiple times (uses PostgreSQL advisory lock).
- Creates the required tables based on SQLAlchemy models.
- Intended to run at app startup (FastAPI lifespan) in each service.

Env:
  DB_BOOTSTRAP           = "1" (default) to enable, "0" to skip
  DB_BOOTSTRAP_LOCK_KEY  = int, advisory lock key (same across services)

Note:
- We import the model(s) so metadata is populated.
- Uses Base.metadata.create_all via DeviceRegistration.__table__.metadata
"""

from __future__ import annotations
import os
import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

# Ensure models are imported so tables are registered in metadata:
from common.db import DeviceRegistration  # noqa: F401

logger = logging.getLogger("db_bootstrap")

# Pick up metadata from any mapped table (all share the same MetaData)
METADATA = DeviceRegistration.__table__.metadata


async def _acquire_advisory_lock(conn, lock_key: int) -> None:
    await conn.execute(text("SELECT pg_advisory_lock(:k)").bindparams(k=lock_key))


async def _release_advisory_lock(conn, lock_key: int) -> None:
    await conn.execute(text("SELECT pg_advisory_unlock(:k)").bindparams(k=lock_key))


async def bootstrap(engine: AsyncEngine, *, lock_key: Optional[int] = None) -> bool:
    """
    Create missing tables inside a global advisory lock to avoid races.
    Returns True on success, False on failure.
    """
    if os.getenv("DB_BOOTSTRAP", "1") not in {"1", "true", "TRUE", "yes", "on"}:
        logger.info("DB bootstrap disabled by DB_BOOTSTRAP env.")
        return True

    lk = lock_key
    if lk is None:
        # One fixed key for all services/processes. Customize via env if needed.
        lk = int(os.getenv("DB_BOOTSTRAP_LOCK_KEY", "726381"))

    try:
        async with engine.begin() as conn:
            # Optional: ensure 'public' schema exists
            await conn.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
            # Serialize CREATEs across all workers/services
            await _acquire_advisory_lock(conn, lk)
            try:
                # create_all checks existence; within the lock it’s race-free
                await conn.run_sync(METADATA.create_all)
            finally:
                await _release_advisory_lock(conn, lk)
        logger.info("DB bootstrap complete.")
        return True
    except Exception:
        logger.exception("DB bootstrap failed")
        return False
