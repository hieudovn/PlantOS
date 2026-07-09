FROM python:3.11-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY edge-v2/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY edge-v2/agent/ ./agent/
COPY edge-v2/console/ ./console/

# Copy Edge v1 reused libraries (buffer, sync, health, publisher)
# Create edge/ package structure for imports
RUN mkdir -p /app/edge/agent
COPY edge/agent/buffer.py /app/edge/agent/buffer.py
COPY edge/agent/sync.py /app/edge/agent/sync.py
COPY edge/agent/health.py /app/edge/agent/health.py
COPY edge/agent/publisher.py /app/edge/agent/publisher.py

# Create data directory
RUN mkdir -p /app/data /app/config

EXPOSE 8011

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8011/api/status || exit 1

CMD ["python", "-m", "agent.main"]
