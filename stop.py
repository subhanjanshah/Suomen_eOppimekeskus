#!/usr/bin/env python3
"""Cross-platform Docker Compose stopper for eOppimisRadar."""

from pathlib import Path
import shutil
import subprocess
import sys

PROJECT_DIR = Path(__file__).resolve().parent


def main():
    print("\n=== Stopping eOppimisRadar ===\n", flush=True)
    if not (PROJECT_DIR / "compose.yaml").is_file() and not (PROJECT_DIR / "docker-compose.yml").is_file():
        print("ERROR: No compose.yaml or docker-compose.yml found next to stop.py.")
        return 1

    if not shutil.which("docker"):
        print("ERROR: Docker CLI was not found. Install Docker Desktop first.")
        return 1

    if subprocess.run(
        ["docker", "compose", "version"],
        cwd=PROJECT_DIR,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode != 0:
        print("ERROR: Docker Compose is unavailable.")
        return 1

    try:
        result = subprocess.run(
            ["docker", "compose", "down"],
            cwd=PROJECT_DIR,
            check=False,
        )
    except KeyboardInterrupt:
        print("\nStop interrupted.")
        return 130

    if result.returncode == 0:
        print("\neOppimisRadar containers stopped. Persistent Docker volumes were preserved.")
    else:
        print("\nERROR: Could not stop containers. Check that Docker Desktop is running.")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
