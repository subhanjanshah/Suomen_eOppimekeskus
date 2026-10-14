#!/usr/bin/env bash
set -Eeuo pipefail

MODEL="${OLLAMA_MODEL:-qwen3:4b}"
OLLAMA_PID=""
STREAMLIT_PID=""
DOWNLOAD_PID=""

# Stop all services when the container stops or startup fails.
cleanup() {
    trap - EXIT
    for pid in "$STREAMLIT_PID" "$DOWNLOAD_PID" "$OLLAMA_PID"; do
        if [[ -n "$pid" ]]; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    wait 2>/dev/null || true
}

trap cleanup EXIT
trap 'exit 0' TERM INT

mkdir -p /data /models

# Keep file-based exports and history in persistent storage.
cd /data

# Preserve the application's Streamlit theme.
mkdir -p /data/.streamlit
if [[ -f /app/.streamlit/config.toml ]]; then
    cp /app/.streamlit/config.toml /data/.streamlit/config.toml
fi

echo "Starting Ollama..."
ollama serve &
OLLAMA_PID=$!

echo "Waiting for Ollama..."
READY=false

for attempt in {1..60}; do
    if ollama list >/dev/null 2>&1; then
        READY=true
        break
    fi

    if ! kill -0 "$OLLAMA_PID" 2>/dev/null; then
        echo "ERROR: Ollama stopped during startup."
        exit 1
    fi

    sleep 1
done

if [[ "$READY" != "true" ]]; then
    echo "ERROR: Ollama did not become ready within 60 seconds."
    exit 1
fi

# Download only when the model is missing.
if ollama show "$MODEL" >/dev/null 2>&1; then
    echo "Model $MODEL is already installed."
else
    echo "Downloading $MODEL. First launch may take several minutes..."
    ollama pull "$MODEL" &
    DOWNLOAD_PID=$!

    if ! wait "$DOWNLOAD_PID"; then
        echo "ERROR: Model download failed. Check internet access and disk space, then restart."
        exit 1
    fi

    DOWNLOAD_PID=""
fi

echo "Starting the newsletter application..."
python -m streamlit run /app/streamlit_app.py \
    --server.address=0.0.0.0 \
    --server.port=8501 \
    --server.headless=true \
    --browser.gatherUsageStats=false &
STREAMLIT_PID=$!

echo "Open http://localhost:8501 once Streamlit is ready."

# If either service exits, stop the other too.
set +e
wait -n "$OLLAMA_PID" "$STREAMLIT_PID"
STATUS=$?
set -e

echo "A service stopped. Shutting down the container."
exit "$STATUS"