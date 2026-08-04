#!/usr/bin/env bash
# Server MET v2.0 - end-to-end validation with real data
# 1. Checks dependencies
# 2. Runs the pipeline (GFS + METAR) with real data
# 3. Runs the full API test-suite (in-process TestClient)
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${HOME}/envs/met/bin/activate"
PASS=0
FAIL=0

if [[ -f "$VENV" ]]; then
    # shellcheck disable=SC1090
    source "$VENV"
fi

cd "$PROJECT_DIR"

log() { printf '\033[1;34m[TEST]\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m  ✓ %s\033[0m\n' "$*"; PASS=$((PASS+1)); }
bad()  { printf '\033[1;31m  ✗ %s\033[0m\n' "$*"; FAIL=$((FAIL+1)); }

# ---- 1. dependencies ----
log "Verificando dependências"
python -c "import pygrib, fastapi, uvicorn, httpx, matplotlib" \
    && ok "Módulos Python instalados" || bad "Faltam módulos Python"

# ---- 2. pipeline com dados reais ----
log "Executando pipeline (GFS + METAR) para SP"
PYTHONPATH=. python scripts/process_data.py --date 20260804 --analysis 00 --regions SP >/tmp/pipeline_out.txt 2>&1 \
    && ok "Pipeline executado" || bad "Pipeline falhou ($(tail -1 /tmp/pipeline_out.txt))"

PYTHONPATH=. python - <<'EOF' && ok "Registros persistidos (GRIB + METAR)" || bad "Sem registros no banco"
from core.persistence import persistence
assert persistence.get_available_regions(), "sem regiões"
assert persistence.get_available_variables(), "sem variáveis"
assert persistence.get_metar_stats()["reports"] > 0, "sem METAR"
EOF

[[ -n "$(ls -A maps/*.png 2>/dev/null)" ]] && ok "Mapas PNG gerados" || bad "Nenhum mapa gerado"

# ---- 3. suites de testes ----
log "Executando suíte de testes da API (in-process)"
if PYTHONPATH=. python -m pytest tests/test_e2e.py -q >/tmp/e2e_out.txt 2>&1; then
    ok "Todos os testes E2E passaram"
else
    bad "Testes E2E falharam"
    tail -20 /tmp/e2e_out.txt
fi

echo
echo "=============================="
echo "RESULTADO: $PASS passaram, $FAIL falharam"
echo "=============================="
[[ "$FAIL" -eq 0 ]]