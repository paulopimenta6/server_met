#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=========================================="
echo "  MET Server - Quick Start"
echo "=========================================="

case "${1:-help}" in
    install)
        echo "[1/4] Installing Python dependencies..."
        pip install -r requirements.txt

        echo "[2/4] Ensuring data directories..."
        mkdir -p data/gribs data/mapasGrib data/matrizGrib
        mkdir -p data/matrizGrib/predi data/matrizGrib/bluesky

        echo "[3/4] Testing installation..."
        python3 -c "from server_MET import *; print('Import OK')"

        echo "[4/4] Done! Run './run.sh server' to start."
        ;;
    server)
        echo "Starting MET Server on http://0.0.0.0:8000"
        exec uvicorn server_MET.server:app --host 0.0.0.0 --port 8000 --reload
        ;;
    download)
        DATE="${2:-$(date +%Y%m%d)}"
        ANA="${3:-}"
        echo "Downloading GRIBS for date=$DATE analysis=$ANA"
        python3 -c "
from server_MET.grib_downloader import GribDownloader
d = GribDownloader()
files = d.download_gribs_all_resolutions(date_str='$DATE', analysis_hour='$ANA' if '$ANA' else None)
print(f'Downloaded: {files}')
"
        ;;
    test)
        echo "Running tests..."
        python3 -m pytest tests/ -v --tb=short
        ;;
    clean)
        DAYS="${2:-2}"
        echo "Cleaning GRIB files older than $DAYS days..."
        python3 -c "
from server_MET.grib_downloader import GribDownloader
d = GribDownloader()
removed = d.clean_old_gribs(days_old=$DAYS)
print(f'Removed {removed} files')
"
        ;;
    docker-build)
        docker compose build
        ;;
    docker-up)
        docker compose up -d
        ;;
    docker-down)
        docker compose down
        ;;
    *)
        echo "Usage: $0 {install|server|download|test|clean|docker-build|docker-up|docker-down|help}"
        echo ""
        echo "  install      Install dependencies and prepare environment"
        echo "  server       Start development server on :8000"
        echo "  download     Download GFS GRIB data (optional: YYYYMMDD and analysis hour)"
        echo "  test         Run test suite"
        echo "  clean [N]    Remove GRIB data older than N days (default: 2)"
        echo "  docker-build Build Docker image"
        echo "  docker-up    Start Docker Compose services"
        echo "  docker-down  Stop Docker Compose services"
        ;;
esac
