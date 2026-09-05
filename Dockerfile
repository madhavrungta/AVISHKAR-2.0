FROM python:3.11-slim

# Install system geospatial and database dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libpq-dev \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application modules, datasets, and verified ML artifacts
COPY backend/app/ ./app/
COPY backend/data/ ./data/
COPY backend/ml_artifacts/ ./ml_artifacts/
COPY backend/agent/ ./agent/

EXPOSE 8000

# Bind to Render / Railway dynamic PORT or default to 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
