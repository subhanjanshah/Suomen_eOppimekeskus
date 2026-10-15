from pathlib import Path
import subprocess

project = Path(__file__).resolve().parent

print("Stopping eOppimisRadar...")

subprocess.run(
    ["docker", "compose", "down"],
    cwd=project
)
