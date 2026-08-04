#!/usr/bin/env bash
# Server MET v2.0 - main pipeline (GFS + METAR)
# Downloads real GFS subsets from NOAA, processes into SQLite, generates maps
# and fetches live METAR reports.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${HOME}/envs/met/bin/activate"

if [[ -f "$VENV" ]]; then
    # shellcheck disable=SC1090
    source "$VENV"
fi

cd "$PROJECT_DIR"

PYTHONPATH=. python scripts/process_data.py "$@"

echo
echo "Pipeline concluído. Banco: data/sqlite/met_data.db | Mapas: maps/"
