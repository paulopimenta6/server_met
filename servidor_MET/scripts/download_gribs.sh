#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DIR_GRIBS="${PROJECT_DIR}/data/gribs"
DIR_MAPAS="${PROJECT_DIR}/data/mapasGrib"
DIR_MATRIZES="${PROJECT_DIR}/data/matrizGrib"

DATA_ANO=$(date +"%Y")
DATA_MES=$(date +"%m")
DATA_DIA=$(date +"%d")
DATA_COMPLETA="${DATA_ANO}${DATA_MES}${DATA_DIA}"

URL="https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs."

echo "=========================================="
echo " Downloading GFS GRIB2 files"
echo " Date: $DATA_COMPLETA"
echo "=========================================="

mkdir -p "$DIR_GRIBS/$DATA_COMPLETA"
cd "$DIR_GRIBS/$DATA_COMPLETA"

for tAnalise in 00 06 12 18; do
    if [ -d "$tAnalise" ]; then
        echo "Directory $tAnalise exists"
        cd "$tAnalise"
    else
        echo "Creating directory $tAnalise..."
        mkdir "$tAnalise"
        cd "$tAnalise"
    fi

    for tPrev in 00 06 12 18; do
        file_025="gfs.t${tAnalise}z.pgrb2.0p25.f0${tPrev}"
        file_100="gfs.t${tAnalise}z.pgrb2.1p00.f0${tPrev}"

        if [ -f "$file_025" ] && [ -f "$file_100" ]; then
            echo "  [$tAnalise] f0${tPrev} already exists"
            continue
        fi

        echo "  [$tAnalise] Checking URL: ${URL}${DATA_COMPLETA}/${tAnalise}/atmos/"
        if wget --spider --quiet "${URL}${DATA_COMPLETA}/${tAnalise}/atmos/"; then
            echo "  Downloading f0${tPrev}... ($tAnalise)"
            wget -q "${URL}${DATA_COMPLETA}/${tAnalise}/atmos/${file_025}" || true
            wget -q "${URL}${DATA_COMPLETA}/${tAnalise}/atmos/${file_100}" || true
        else
            echo "  Site not available for $tAnalise"
        fi
    done
    cd ..
done

echo "=========================================="
echo " Download complete"
echo "=========================================="
