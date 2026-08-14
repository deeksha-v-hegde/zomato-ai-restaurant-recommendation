"""Launch the Phase 8 Streamlit app."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_PATH = Path(__file__).resolve().parent / "app.py"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Phase 8: Run Streamlit deployment app")
    parser.add_argument("--server.port", dest="port", type=int, default=8501)
    parser.add_argument("--server.address", dest="address", default="127.0.0.1")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(PROJECT_ROOT) + (os.pathsep + existing if existing else "")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_PATH),
        f"--server.port={args.port}",
        f"--server.address={args.address}",
    ]
    return subprocess.call(cmd, cwd=str(PROJECT_ROOT), env=env)


if __name__ == "__main__":
    raise SystemExit(main())
