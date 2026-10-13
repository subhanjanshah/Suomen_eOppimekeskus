# Start with Ollama already installed.
FROM ollama/ollama:latest

# Install Python and tools needed by Python dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    python3-dev \
    build-essential \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create an isolated Python environment inside the container.
RUN python3 -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OLLAMA_HOST="127.0.0.1:11434" \
    OLLAMA_MODELS="/models" \
    NEWSLETTER_ACCOUNTS_FILE="/data/accounts.json"

WORKDIR /app

# Install dependencies before copying the application.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project, respecting .dockerignore.
COPY . .

# Persistent storage will be attached to these folders later.
RUN mkdir -p /data /models \
    && chmod +x /app/start.sh

EXPOSE 8501

# Replace Ollama's default entrypoint with our startup script.
ENTRYPOINT ["/bin/bash", "/app/start.sh"] 