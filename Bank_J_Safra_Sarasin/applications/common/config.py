"""Shared configuration helpers."""

from __future__ import annotations
import os


def get_env(name: str, default: str | None = None) -> str:
    """Return an environment variable or default; raise if missing and no default provided."""
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Required environment variable '{name}' is not set.")
    return value


def database_url(env_var: str = "DATABASE_URL", default: str | None = None) -> str:
    """Return DB URL; supports async driver for SQLAlchemy 2.x."""
    return get_env(env_var, default)


def device_api_url(env_var: str = "DEVICE_API_URL", default: str | None = None) -> str:
    """Internal URL for DeviceRegistrationAPI (used by StatisticsAPI)."""
    return get_env(env_var, default or "http://device_reg_api:8001")
