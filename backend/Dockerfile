FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps for building native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first (saves ~1.5GB vs default CUDA bundle)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Create storage dirs (used if no volume is mounted)
RUN mkdir -p storage/uploads storage/references storage/exports storage/indices
# Create persistent data dir (Railway volume mount point)
RUN mkdir -p /data/storage/uploads /data/storage/references /data/storage/exports /data/storage/indices

EXPOSE 8000

# Railway sets $PORT; shell form allows variable expansion
# --timeout-keep-alive 300 prevents Railway proxy from killing long-running generation requests
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 300
