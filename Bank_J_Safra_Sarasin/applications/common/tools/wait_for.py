"""
Generic 'wait-for' utility for TCP or HTTP readiness.

Examples:
  # Wait for TCP port
  python -m common.tools.wait_for --tcp db:5432 --timeout 30

  # Wait for HTTP 2xx/3xx
  python -m common.tools.wait_for --http http://statistics_api:8000/healthz --timeout 30
"""

from __future__ import annotations

import argparse
import socket
import time
import urllib.request


def wait_tcp(host: str, port: int, timeout: int) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=3):
                return True
        except OSError:
            time.sleep(1)
    return False


def wait_http(url: str, timeout: int) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                if 200 <= resp.status < 400:
                    return True
        except Exception:
            time.sleep(1)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Wait for TCP or HTTP service readiness.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--tcp", help="host:port")
    group.add_argument("--http", help="http(s)://...")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout in seconds")
    args = parser.parse_args()

    if args.tcp:
        host, _, port_s = args.tcp.partition(":")
        try:
            port = int(port_s)
        except ValueError:
            print("Invalid port.")
            return 2
        ok = wait_tcp(host, port, args.timeout)
    else:
        ok = wait_http(args.http, args.timeout)

    print("READY" if ok else "TIMEOUT")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
