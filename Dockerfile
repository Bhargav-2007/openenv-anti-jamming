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
COPY pyproject.toml ./pyproject.toml
COPY README.md ./README.md

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV OPENENV_HOST=0.0.0.0
ENV OPENENV_PORT=7860
ENV ANTI_JAMMING_TASK=easy

USER openenv

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import anti_jamming_env; print('ok')" || exit 1

CMD ["openenv", "serve", "server.py"]
