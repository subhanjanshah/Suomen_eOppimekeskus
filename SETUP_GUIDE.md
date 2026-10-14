# eOppimisRadar setup guide

## Recommended: Windows client with Docker

1. Install **Docker Desktop** and start it. Allow Docker enough memory to run the local AI model.
2. Download the project ZIP and extract it to a normal folder.
3. Double-click **Start-eOppimisRadar.bat**. It starts the Docker container and opens your browser at `http://localhost:8501`.
4. On first launch, Docker builds the image and automatically downloads **Qwen3:4b**. The first launch may take several minutes; if the browser opens early, wait and refresh.
5. Create the first administrator account. Additional users can be created by the administrator.
6. Review AI summaries before publication. Generation on CPU may take several minutes per article.
7. Double-click **Stop-eOppimisRadar.bat** when finished.

**Important:** No separate Python, Ollama, GitHub, or VS Code installation is required. The client **does** need Docker Desktop. Model files and accounts are saved in Docker named volumes and survive normal starts/stops. Never use `docker compose down -v` unless you intentionally want to erase them. Do not distribute your own saved accounts or private newsletter data.

## Troubleshooting

- **Docker not running:** Open Docker Desktop, wait until the engine starts, then retry the launcher.
- **Browser cannot connect:** First launch may still be downloading the model. Wait and refresh. For diagnostics use `docker compose logs --tail 80 newsletter`.
- **AI is slow:** Qwen3:4b runs locally. CPU-only generation can take several minutes. The default request timeout is 600 seconds.
- **Port 8501 already in use:** Stop other Streamlit apps or containers using that port.
- **Preserve your account:** Use the Stop launcher or `docker compose down`, without `-v`.

## Developer commands (optional)

From the extracted project folder:

```powershell
docker compose up --build -d
docker compose logs --tail 80 newsletter
docker compose down
```

The default model and AI request timeout are set in `compose.yaml` as `OLLAMA_MODEL: qwen3:4b` and `OLLAMA_TIMEOUT: "600"`. The shell startup script and Python generator both read these settings. To use a different model, update `OLLAMA_MODEL` and rebuild the container.

For a manual non-Docker development setup, install Python 3.12+, Ollama, run `ollama pull qwen3:4b`, install packages with `pip install -r requirements.txt`, and start `python -m streamlit run streamlit_app.py`. This manual setup is not required for clients.
