"""Logging setup helpers."""

from __future__ import annotations
import logging
import os


def setup_logging(service_name: str) -> logging.Logger:
    """Configure root logging once and return a service-scoped logger."""
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logger = logging.getLogger(service_name)
    logger.setLevel(level)
    return logger
