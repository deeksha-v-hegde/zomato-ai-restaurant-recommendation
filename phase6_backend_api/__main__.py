"""CLI entrypoint for Phase 6 backend API."""

from __future__ import annotations

import argparse
import logging
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 6: Zomato Recommendation Backend API")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("-v", "--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        import uvicorn
    except ImportError:
        logging.error("uvicorn not installed. Run: pip install -r phase6_backend_api/requirements.txt")
        return 1

    try:
        uvicorn.run(
            "phase6_backend_api.app.main:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
    except OSError as exc:
        if getattr(exc, "winerror", None) == 10048 or "address already in use" in str(exc).lower():
            logging.error(
                "Port %s is already in use. Stop the other backend process or use --port.",
                args.port,
            )
            logging.error("Example: python -m phase6_backend_api --port 8001")
            return 1
        raise
    return 0


if __name__ == "__main__":
    sys.exit(main())
