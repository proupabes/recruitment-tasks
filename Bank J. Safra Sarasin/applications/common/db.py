"""Shared async SQLAlchemy 2.x database utilities."""

from __future__ import annotations

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, func, Integer


def create_engine(db_url: str, echo: bool = False) -> AsyncEngine:
    """Create an async SQLAlchemy engine."""
    return create_async_engine(db_url, echo=echo, pool_pre_ping=True)


def make_sessionmaker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create an async sessionmaker bound to the engine."""
    return async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(session_factory: async_sessionmaker[AsyncSession]):
    """Async context manager to provide a unit-of-work style session."""
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


class Base(DeclarativeBase):
    """Shared declarative base, if services want to share model definitions."""
    pass


# Shared table model used by both services (DRY)
class DeviceRegistration(Base):
    """Event log of device registrations (append-only)."""
    __tablename__ = "device_registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_key: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    user_agent: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    client_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv4/IPv6 string
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )
