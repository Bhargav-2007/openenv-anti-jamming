<<<<<<< HEAD
# syntax=docker/dockerfile:1
# ────────────────────────────────────────────────────────────────────────────
# Anti-Jamming OpenEnv – production image
# No frontend, non-root, uses openenv-core[cli] server.py entry-point.
# ────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Minimal build deps; clean up immediately to keep image lean
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy source
COPY anti_jamming_env/ ./anti_jamming_env/
COPY server/ ./server/
COPY inference.py .
COPY openenv.yaml .
COPY README.md .

# ── Security: drop to a non-root user ───────────────────────────────────────
RUN adduser --disabled-password --gecos "" appuser
USER appuser

# Runtime configuration
ENV PYTHONUNBUFFERED=1 \
    OPENENV_HOST=0.0.0.0 \
    OPENENV_PORT=8000 \
    ANTI_JAMMING_TASK=easy \
    ENABLE_WEB_INTERFACE=false

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" \
    || exit 1

CMD ["python", "-m", "server.app"]
=======
FROM python:3.11-slim

WORKDIR /app

RUN useradd -m -u 1000 openenv

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY anti_jamming_env/ ./anti_jamming_env/
COPY server.py ./server.py
COPY openenv.yaml ./openenv.yaml
COPY inference.py ./inference.py

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OPENENV_HOST=0.0.0.0
ENV OPENENV_PORT=8000
ENV ANTI_JAMMING_TASK=easy

USER openenv

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import anti_jamming_env; print('ok')" || exit 1

CMD ["openenv", "serve", "server.py"]
>>>>>>> 5242213f (Changes)
