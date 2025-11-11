"""Shared FastAPI exception handlers (configurable per service)."""

from __future__ import annotations
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from typing import Callable, Any


def make_validation_handler_for_statistics() -> Callable[[Any, RequestValidationError], JSONResponse]:
    """Return a handler that maps validation errors to the required StatsAPI schema."""
    def handler(_request, _exc: RequestValidationError):
        return JSONResponse(status_code=400, content={"statusCode": 400, "message": "bad_request"})
    return handler


def make_validation_handler_for_device() -> Callable[[Any, RequestValidationError], JSONResponse]:
    """Return a handler for DeviceRegistrationAPI (statusCode only)."""
    def handler(_request, _exc: RequestValidationError):
        return JSONResponse(status_code=400, content={"statusCode": 400})
    return handler
