# Dockerfile for Anti-Jamming Environment
# Base image: Python 3.11 slim for efficiency

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY anti_jamming_env/ ./anti_jamming_env/
COPY app.py .
COPY frontend/ ./frontend/
COPY inference.py .
COPY openenv.yaml .

# Expose port for API server
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV OPENENV_HOST=0.0.0.0
ENV OPENENV_PORT=8000
ENV ANTI_JAMMING_TASK=easy

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health')" || exit 1

# Run modern FastAPI server
CMD ["python", "app.py"]