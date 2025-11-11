"""
Minimal end-to-end smoke test:
- Calls DeviceRegistrationAPI to register a random event
- Calls StatisticsAPI to fetch the count for the normalized device type
- Exits non-zero if any step fails

Uses urllib (stdlib) to avoid extra deps.
"""

from __future__ import annotations

import json
import random
import string
import sys
import time
import urllib.request


def _post_json(url: str, payload: dict, timeout: int = 5) -> tuple[int, dict | None]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, (json.loads(body) if body else None)
    except Exception:
        return 0, None


def _get_json(url: str, timeout: int = 5) -> tuple[int, dict | None]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, (json.loads(body) if body else None)
    except Exception:
        return 0, None


def main() -> int:
    stats_base = "http://localhost:8000"
    device_base = "http://localhost:8001"

    # Generate random userKey to avoid collisions
    user_key = "smoke-" + "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    device_type = "Android"

    # 1) Register
    code, body = _post_json(
        f"{device_base}/Device/register",
        {"userKey": user_key, "deviceType": device_type, "userAgent": "smoke/1.0"},
    )
    if code != 200 or not body or body.get("statusCode") != 200:
        print("Smoke: register failed", code, body)
        return 1

    # Small delay for DB commit visibility (usually not needed)
    time.sleep(0.5)

    # 2) Stats
    code, body = _get_json(f"{stats_base}/Log/auth/statistics?deviceType={device_type}")
    if code != 200 or not body or "count" not in body:
        print("Smoke: statistics failed", code, body)
        return 1

    print("Smoke OK:", body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
