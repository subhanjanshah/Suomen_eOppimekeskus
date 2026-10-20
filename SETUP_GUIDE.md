# eOppimisKeskus — Windows Setup Guide

This guide is for running the newsletter application on a **Windows computer** using the included double-click launchers. Docker Desktop is the only separate application required for the recommended setup; **you do not need to install Python, VS Code, Ollama, or Git**.

## 1. Install Docker Desktop (one time)

1. Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/).
2. Open Docker Desktop once to complete installation, accept any terms, and allow the Docker engine to initialize. Follow any Windows/WSL setup prompts from Docker Desktop.
3. Make sure Docker Desktop can run on your computer and that sufficient disk space and memory are available for the local AI model.

The launcher can start Docker Desktop automatically **after** it has been installed and configured.

## 2. Download and extract the project

1. Open the [project repository](https://github.com/subhanjanshah/Suomen_eOppimekeskus).
2. Select **Code → Download ZIP**.
3. Extract the ZIP into a normal folder (for example, under Documents).
4. Open the extracted project folder. Check that it contains `compose.yaml`, `Start-eOppimisKeskus.bat`, and `Stop-eOppimisKeskus.bat`.

Do not run the `.bat` files while they are still inside the ZIP. Keep the launchers in the same folder as `compose.yaml`.

## 3. Start the application

1. Double-click **`Start-eOppimisKeskus.bat`**.
2. A Command Prompt window appears. The launcher checks Docker, opens Docker Desktop if it is not already running, and waits for Docker to become ready.
3. The launcher runs `docker compose up -d --build`, waits for the website to respond, and opens **http://localhost:8501** in your default browser.
4. The launcher window closes automatically after a successful start. If there is an error, it stays open so you can read the message.

**First launch:** Docker may need to download the base image, build the app, and download **Qwen3:4b** (roughly 2.5 GB for the model). This requires an internet connection and may take several minutes. The website being open does **not** necessarily mean the model download has finished; the first AI generation may take longer.

## 4. Create your account and use the app

1. On first use, create the **administrator account** using the setup form shown in the browser. Choose a password of at least 12 characters.
2. Sign in. The administrator can add colleagues through **Manage Accounts** in the application.
3. Collect articles by topic, URLs, or supported feeds; review and edit AI summaries; select approved items; design the newsletter; and export the HTML draft.
4. **Check every AI-generated summary, date, link, and image permission before publishing.** The app does not send newsletters automatically.

## 5. Stop the application

1. Double-click **`Stop-eOppimisKeskus.bat`**.
2. It runs `docker compose down` to stop and remove the project's containers.
3. The Command Prompt window closes automatically on success. If stopping fails, the window stays open to show the error.

Closing the browser tab alone **does not stop** the containers. The Stop launcher does **not** close Docker Desktop itself; that is normal.

**Keep your data:** The normal Stop launcher preserves Docker named volumes containing the model and saved accounts. **Never run `docker compose down -v`** unless you intentionally want to delete those volumes.

## Troubleshooting

| Problem | What to do |
|---|---|
| Docker is not found | Install Docker Desktop and complete its first-run setup. Then retry the Start launcher. |
| Docker takes too long to start | Open Docker Desktop and wait until the engine is ready; then run Start again. |
| Browser does not open or cannot connect | Visit http://localhost:8501 manually. Wait for the first build to finish. Check the Command Prompt error or Docker Desktop. |
| Website opens but AI is unavailable | The model may still be downloading on first launch. Allow more time; inspect the logs if it persists. |
| AI responses are slow | Qwen3:4b runs locally. CPU-only generation can take several minutes per article; the configured request timeout is 600 seconds. |
| Port 8501 is already in use | Stop another local application or container using port 8501. |
| Stop launcher reports an error | Check that Docker Desktop is running, then retry. |

For technical diagnostics, open PowerShell **in the extracted project folder** and run:

```powershell
docker compose ps
docker compose logs --tail 80 newsletter
```

## Optional developer commands

```powershell
docker compose up -d --build
docker compose logs --tail 80 newsletter
docker compose down
```

The Docker configuration in `compose.yaml` uses the local AI model `qwen3:4b` and `OLLAMA_TIMEOUT: "600"`. The application is bound to `127.0.0.1:8501`, so it is intended for use on the same computer, not as a public website.

For manual development without Docker, Python 3.12+, Ollama, and the Python dependencies are needed. **These are not required for the client launcher workflow.**

## Notes for sharing the project

- Share the repository ZIP or the complete project folder, not only the two `.bat` files.
- The recipient must install Docker Desktop on their own Windows computer.
- The recipient creates their own first administrator account; do not share your personal credentials or private account data.
- The `.bat` launchers described here are **Windows-only**. This guide does not include a macOS launcher.
