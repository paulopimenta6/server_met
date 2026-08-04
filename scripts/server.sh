#!/usr/bin/env bash
# Server MET v2.0 - start / stop the FastAPI server
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${HOME}/envs/met/bin/activate"
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

if [[ -f "$VENV" ]]; then
    # shellcheck disable=SC1090
    source "$VENV"
fi

cd "$PROJECT_DIR"

start() {
    if pgrep -f "uvicorn api.main:app" >/dev/null 2>&1; then
        echo "API já está em execução."
        return
    fi
    nohup python -m uvicorn api.main:app --host "$HOST" --port "$PORT" > server_met_api.log 2>&1 &
    echo "API iniciada em http://$HOST:$PORT (PID $!)"
    sleep 2
}

stop() {
    pkill -f "uvicorn api.main:app" 2>/dev/null && echo "API parada." || echo "API não estava em execução."
}

status() {
    if pgrep -f "uvicorn api.main:app" >/dev/null 2>&1; then
        echo "API em execução. Health:"
        curl -s "http://$HOST:$PORT/health" || true
        echo
    else
        echo "API parada."
    fi
}

case "${1:-start}" in
    start) start ;;
    stop) stop ;;
    restart) stop; start ;;
    status) status ;;
    *) echo "Uso: $0 {start|stop|restart|status}" ;;
esac