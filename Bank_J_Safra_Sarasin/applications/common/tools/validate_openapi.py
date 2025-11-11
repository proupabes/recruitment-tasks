"""
Lightweight OpenAPI schema validation.

- Works with stdlib by checking key structural elements (openapi, info, paths).
- If 'openapi-spec-validator' is installed, uses it for full validation.
- Non-destructive: returns non-zero exit code on validation errors.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

logger = logging.getLogger("validate_openapi")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def basic_checks(spec: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(spec, dict):
        errors.append("Spec is not a JSON object.")
        return errors
    if "openapi" not in spec:
        errors.append("Missing 'openapi' field.")
    if "info" not in spec or not isinstance(spec["info"], dict):
        errors.append("Missing or invalid 'info' object.")
    if "paths" not in spec or not isinstance(spec["paths"], dict):
        errors.append("Missing or invalid 'paths' object.")
    return errors


def full_validate_if_available(spec: dict) -> list[str]:
    try:
        # Optional dependency
        from openapi_spec_validator import validate_spec
        from openapi_spec_validator.schemas import read_yaml_file
    except Exception:
        logger.info("openapi-spec-validator not installed; skipping strict validation.")
        return []

    try:
        validate_spec(spec)  # raises on error
        return []
    except Exception as e:
        return [f"openapi-spec-validator error: {e}"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an OpenAPI JSON file.")
    parser.add_argument("--file", required=True, help="Path to openapi.json")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        logger.error("File not found: %s", path)
        return 2

    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error("Failed to read/parse JSON: %s", e)
        return 2

    errors = basic_checks(spec)
    errors += full_validate_if_available(spec)

    if errors:
        for err in errors:
            logger.error("Validation error: %s", err)
        return 1

    logger.info("OpenAPI validation passed for %s", path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
