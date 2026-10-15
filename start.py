#!/usr/bin/env python3
"""Cross-platform Docker Compose launcher for eOppimisRadar."""

from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

PROJECT_DIR = Path(__file__).resolve().parent
APP_URL = "http://localhost:8501"
WAIT_SECONDS = 120


def run(command, *, capture=False):
    return subprocess.run(
        command,
        cwd=PROJECT_DIR,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.STDOUT if capture else None,
        check=False,
    )


def main():
    print("\n=== Starting eOppimisRadar ===\n", flush=True)
    if not (PROJECT_DIR / "compose.yaml").is_file() and not (PROJECT_DIR / "docker-compose.yml").is_file():
        print("ERROR: No compose.yaml or docker-compose.yml found next to start.py.")
        return 1

    if not shutil.which("docker"):
        print("ERROR: Docker CLI was not found. Install and start Docker Desktop first.")
        return 1

    if run(["docker", "info"], capture=True).returncode != 0:
        print("ERROR: Docker is not running or cannot be accessed. Start Docker Desktop and retry.")
        return 1

    if run(["docker", "compose", "version"], capture=True).returncode != 0:
        print("ERROR: Docker Compose is unavailable. Update or reinstall Docker Desktop.")
        return 1

    print("Building and starting containers (the first run can take a while)...\n", flush=True)
    try:
        result = run(["docker", "compose", "up", "-d", "--build"])
    except KeyboardInterrupt:
        print("\nStartup interrupted.")
        return 130

    if result.returncode != 0:
        print("\nERROR: Docker Compose could not start the application.")
        print("For detailed errors, run: docker compose logs --tail=100")
        return result.returncode

    print(f"\nWaiting up to {WAIT_SECONDS} seconds for {APP_URL} ...", flush=True)
    deadline = time.monotonic() + WAIT_SECONDS
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(APP_URL, timeout=3) as response:
                if response.status < 500:
                    print(f"\nApp is available at {APP_URL}")
                    webbrowser.open(APP_URL)
                    return 0
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(3)

    print("\nThe containers started, but the app did not respond in time.")
    print(f"Try opening {APP_URL} manually.")
    print("For troubleshooting, run: docker compose ps")
    print("Then: docker compose logs --tail=100")
    print("Note: Ollama and the qwen3:4b model may also need setup.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
