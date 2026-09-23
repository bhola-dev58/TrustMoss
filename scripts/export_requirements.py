#!/usr/bin/env python3
"""
Synchronizes requirements.txt and apps/api/requirements.txt from pyproject.toml / poetry.lock.
Guarantees backward compatibility for Docker container builds and legacy workflows.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    pyproject_file = repo_root / "pyproject.toml"
    lock_file = repo_root / "poetry.lock"

    if not pyproject_file.exists() or not lock_file.exists():
        print(f"Error: {pyproject_file} or {lock_file} not found.", file=sys.stderr)
        return 1

    print("Exporting production dependencies from poetry.lock...")
    cmd = [
        sys.executable,
        "-m",
        "poetry",
        "export",
        "-f",
        "requirements.txt",
        "--without-hashes",
        "-o",
        str(repo_root / "requirements.txt"),
    ]

    try:
        subprocess.run(cmd, cwd=repo_root, check=True)
        print("Successfully updated requirements.txt")
        return 0
    except subprocess.CalledProcessError as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
