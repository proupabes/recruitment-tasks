"""
Async DB healthcheck using asyncpg.

- Reads DATABASE_URL from env or --url
- Executes 'SELECT 1' to confirm connectivity
- Non-zero exit code on failure (useful for CI/healthchecks)
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

import asyncpg


async def check(url: str) -> bool:
    conn = None
    try:
        conn = await asyncpg.connect(dsn=url, timeout=5)
        await conn.execute("SELECT 1;")
        return True
    except Exception:
        return False
    finally:
        if conn:
            try:
                await conn.close()
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="PostgreSQL healthcheck (asyncpg).")
    parser.add_argument("--url", help="DATABASE_URL (postgresql://... or postgresql+asyncpg://...)")
    args = parser.parse_args()

    url = args.url or os.getenv("DATABASE_URL")
    if not url:
        print("DATABASE_URL not provided.", file=sys.stderr)
        return 2

    # Allow both sync and async dialects; asyncpg.connect expects postgresql://...
    url = url.replace("postgresql+asyncpg://", "postgresql://")

    ok = asyncio.run(check(url))
    print("DB_OK" if ok else "DB_FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
