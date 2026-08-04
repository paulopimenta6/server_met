# Server MET v2.0 - Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (eccodes for pygrib, proj/geos for Basemap)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libeccodes-dev \
    libproj-dev \
    libgeos-dev \
    libsqlite3-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -c "import matplotlib, numpy, fastapi, uvicorn, httpx, pygrib"

COPY . .

RUN mkdir -p /app/data/grib /app/data/sqlite /app/data/csv /app/data/metar /app/maps

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]