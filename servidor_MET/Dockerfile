FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    libgfortran5 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data/gribs /app/data/mapasGrib /app/data/matrizGrib \
    && mkdir -p /app/data/matrizGrib/predi /app/data/matrizGrib/bluesky

EXPOSE 8000

CMD ["uvicorn", "server_MET.server:app", "--host", "0.0.0.0", "--port", "8000"]
