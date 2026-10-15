from pathlib import Path
import subprocess
import webbrowser

project = Path(__file__).resolve().parent

print("Starting eOppimisRadar...")

result = subprocess.run(
    ["docker", "compose", "up", "-d", "--build"],
    cwd=project
)

if result.returncode == 0:
    print("Open http://localhost:8501")
    webbrowser.open("http://localhost:8501")
else:
    print("Startup failed. Check Docker Desktop.")
