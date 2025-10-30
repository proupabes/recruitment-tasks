"""HTTP helpers (client IP extraction, etc.)."""

from __future__ import annotations
from fastapi import Request


def get_client_ip(request: Request) -> str | None:
    """Extract client IP considering common proxy headers; fall back to connection peer."""
    # X-Forwarded-For may contain a list; take the first non-empty token
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client and request.client.host:
        return request.client.host
    return None
