# ---- Runtime image ----
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Build deps only needed to compile wheels (playwright/PyPDF2 need a C compiler)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application source (secrets are injected as container env vars,
# NOT copied in — see .dockerignore)
COPY . .

# Create the runtime database directory (SQLite lives here at runtime)
RUN mkdir -p /app/data

EXPOSE 8080

# Bind to $PORT (set via env var) so the service is portable across hosts.
CMD ["sh", "-c", "exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
