#!/bin/bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "=========================================="
echo "  MET Server v3 - Quick Start"
echo "=========================================="

case "${1:-help}" in
    install)
        echo "[1/4] Instalando dependências Python..."
        pip install -r requirements.txt

        echo "[2/4] Garantindo diretórios de dados..."
        mkdir -p data/gribs data/mapasGrib data/matrizGrib
        mkdir -p data/matrizGrib/predi data/matrizGrib/bluesky
        mkdir -p data/analise data/tmp

        echo "[3/4] Testando instalação..."
        python3 -c "from server_MET import *; print('Import OK')"

        echo "[4/4] Pronto! Use './scripts/run.sh server' para iniciar."
        ;;
    server)
        echo "Iniciando MET Server em http://0.0.0.0:8000"
        exec uvicorn server_MET.api.app:app --host 0.0.0.0 --port 8000 --reload
        ;;
    download)
        DATE="${2:-$(date +%Y%m%d)}"
        ANA="${3:-}"
        RES="${4:-}"
        echo "Baixando GRIBs date=$DATE analysis=$ANA resolution=${RES:-all}"
        python3 -c "
from server_MET.acquisition.grib_downloader import GribDownloader
d = GribDownloader()
res = ['$RES'] if '$RES' else None
files = d.download_gribs_all_resolutions(date_str='$DATE', analysis_hour='$ANA' if '$ANA' else None, resolutions=res)
print(f'Baixados: {files}')
"
        ;;
    analysis)
        DATE="${2:-$(date +%Y%m%d)}"
        echo "Gerando resumo estatístico e perfil vertical (SP) para $DATE..."
        python3 -c "
from server_MET.analysis.statistics import StatisticsAnalyzer
from server_MET.analysis.profiles import ProfileAnalyzer
from server_MET.analysis.timeseries import TimeSeriesAnalyzer
from server_MET.processing.regions import Region
r = Region(name='SP')
s = StatisticsAnalyzer(); p = ProfileAnalyzer(); t = TimeSeriesAnalyzer()
print('Summary temp N500:', s.summarize('temp', r, 500, '$DATE'))
print('Perfil umidadeRel:', len(p.profile('umidadeRel', r, '$DATE').get('profile', [])))
print('Série wind:', len(t.timeseries('wind', r, 500, '$DATE').get('series', [])))
"
        ;;
    db-status)
        echo "Status do banco SQLite..."
        python3 -c "
from server_MET.persistence.database import get_database
db = get_database(); db.create_schema()
print('Banco:', db.db_path)
for t, n in db.table_counts().items():
    print(f'  {t}: {n}')
"
        ;;
    test)
        echo "Executando testes..."
        python3 -m pytest tests/ -v --tb=short
        ;;
    clean)
        DAYS="${2:-2}"
        echo "Removendo dados (gribs/mapas/matrizes/análises) mais antigos que $DAYS dias..."
        python3 -c "
from server_MET.acquisition.grib_downloader import GribDownloader
d = GribDownloader()
removed = d.clean_old_data(days_old=$DAYS)
print(f'Removidos {removed} arquivos')
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
        echo "Uso: $0 {install|server|download|analysis|db-status|test|clean|docker-build|docker-up|docker-down|help}"
        echo ""
        echo "  install      Instala dependências e prepara o ambiente"
        echo "  server       Inicia o servidor de desenvolvimento em :8000"
        echo "  download     Baixa GFS GRIB (opcional: YYYYMMDD, hora de análise, resolução 0p25|0p50|1p00)"
        echo "  analysis     Gera análises de exemplo (resumo, perfil, série) para SP"
        echo "  db-status    Mostra o estado do banco SQLite"
        echo "  test         Executa a suíte de testes"
        echo "  clean [N]    Remove dados antigos (default: 2 dias)"
        echo "  docker-build Build da imagem Docker"
        echo "  docker-up    Sobe o Docker Compose"
        echo "  docker-down  Para o Docker Compose"
        ;;
esac
