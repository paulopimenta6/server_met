#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIA_ANTERIOR=$(date -d "-2 days" +"%Y%m%d")

echo "=========================================="
echo " Cleaning old GRIB data"
echo " Removing data from: $DATA_DIA_ANTERIOR"
echo "=========================================="

for dir in "data/gribs" "data/mapasGrib" "data/matrizGrib"; do
    target="$PROJECT_DIR/$dir/$DATA_DIA_ANTERIOR"
    if [ -d "$target" ]; then
        echo "Removing $target..."
        rm -rf "$target"
    else
        echo "Not found: $target"
    fi
done

echo "=========================================="
echo " Cleanup complete"
echo "=========================================="
