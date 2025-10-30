"""
Generic, safe OpenAPI exporter for any FastAPI app.

Usage examples (run from repo root):
  python -m common.tools.generate_openapi --app statistics_api.main:app --out statistics_api/openapi.json
  python -m common.tools.generate_openapi --app device_registration_api.main:app --out device_registration_api/openapi.json
"""

from __future__ import annotations

import argparse
import importlib
import json
import logging
from pathlib import Path
from typing import Any


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return logging.getLogger("OpenAPIExport")


def _split_app_spec(spec: str) -> tuple[str, str]:
    """
    Split 'module:attr' or 'module.attr' into (module, attr).
    """
    if ":" in spec:
        mod, attr = spec.split(":", 1)
        return mod.strip(), attr.strip()
    # fallback: last dot separates module and attr
    if "." in spec:
        parts = spec.split(".")
        return ".".join(parts[:-1]), parts[-1]
    raise ValueError("Invalid --app spec. Use 'module:attr' or 'module.attr'.")


def load_app(spec: str) -> Any:
    """
    Import the FastAPI app given by spec ('module:attr' or 'module.attr').
    """
    mod_name, attr_name = _split_app_spec(spec)
    module = importlib.import_module(mod_name)
    app = getattr(module, attr_name, None)
    if app is None:
        raise AttributeError(f"Attribute '{attr_name}' not found in module '{mod_name}'")
    if not hasattr(app, "openapi") or not callable(getattr(app, "openapi")):
        raise TypeError("Provided attribute does not look like a FastAPI app (missing openapi())")
    return app


def write_if_changed(out_path: Path, content: str, logger: logging.Logger) -> None:
    """
    Write content to out_path if different. Use a temporary file for durability.
    """
    if out_path.exists():
        try:
            existing = out_path.read_text(encoding="utf-8")
            if existing == content:
                logger.info("openapi.json is up-to-date; nothing to do.")
                return
            logger.warning("openapi.json exists and will be updated.")
        except Exception:
            logger.exception("Failed reading existing file; will attempt to overwrite.")

    tmp = out_path.with_suffix(out_path.suffix + ".tmp")
    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(content, encoding="utf-8")
        tmp.replace(out_path)
        logger.info("OpenAPI spec written to %s", out_path)
    finally:
        try:
            if tmp.exists():
                tmp.unlink(missing_ok=True)
        except Exception:
            # Best-effort cleanup
            logger.exception("Failed cleaning temporary file %s", tmp)


def main() -> int:
    logger = setup_logging()
    parser = argparse.ArgumentParser(description="Export OpenAPI from a FastAPI app.")
    parser.add_argument("--app", required=True, help="App spec as 'module:attr' (e.g., statistics_api.main:app)")
    parser.add_argument("--out", required=True, help="Output path to openapi.json")
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation (default: 2)")
    args = parser.parse_args()

    out_path = Path(args.out)

    try:
        app = load_app(args.app)
    except Exception as e:
        logger.exception("Failed loading app '%s'", args.app)
        return 1

    try:
        spec_dict = app.openapi()
        content = json.dumps(spec_dict, indent=args.indent, ensure_ascii=False)
    except Exception:
        logger.exception("Failed generating OpenAPI via app.openapi()")
        return 1

    try:
        write_if_changed(out_path, content, logger)
        return 0
    except Exception:
        logger.exception("Failed writing OpenAPI to %s", out_path)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
