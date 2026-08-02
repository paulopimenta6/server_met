# Servidor Meteorológico — MET Server (v3.0.0)

Servidor **FastAPI** completo para **captação, tratamento, análise, persistência e distribuição** de dados meteorológicos do modelo **GFS (Global Forecast System)** da **NOAA**.

```
captação  →  tratamento  →  análise  →  persistência  →  resultados  →  servidor
(GRIBs,      (extração,      (estatís-    (SQLite,        (mapas,        (API REST,
 METAR)       unidades,      tica,         histórico,      matrizes,      HTTP)
              níveis,        perfis,       cache de        gráficos,
              vento)         séries)       análises)       BlueSky)
```

---

## 1. O que o sistema faz

| Recurso | Descrição |
|---|---|
| **Download GFS** | Arquivos GRIB2 do NOMADS (3 resoluções × previsões 00/06/12/18) via `wget`, com registro no banco |
| **Leitura GRIB2** | `pygrib` + numpy: latitudes, longitudes e valores por variável/nível |
| **Tratamento** | Conversão de unidades (K→°C, Pa→hPa), snap de níveis 150–1000 hPa, recorte por região |
| **Vento** | Magnitude, direção (meteorológica/azimute), nós e altitude por pressão — cálculo centralizado |
| **Análise** | Estatística descritiva por região, **perfil vertical** por nível, **série temporal** com **tendência estatística** (statsmodels) e gráficos profissionais |
| **Mapas** | PNG com contornos e campo de vento (Cartopy, fallback Basemap) |
| **Matrizes** | CSV por variável/campo de vento e matriz **BlueSky** (nós + altitude em ft) |
| **METAR** | Fetch da API aviationweather.gov + parser local (offline) com **arquivo histórico** |
| **Persistência** | Banco **SQLite** (`data/met_server.db`) com histórico de downloads, saídas, METAR, tarefas e análises |
| **Servidor de arquivos** | Artefatos gerados baixáveis via HTTP com proteção contra path traversal |

## 2. Arquitetura (camadas)

```
server_MET/
├── core/          # base: Settings (path.conf), constantes, modelos Pydantic, logging
├── acquisition/   # [1. captação] GribDownloader, GribReader, MetarClient
├── processing/    # [2. tratamento] DataProcessor (unidades/níveis/extração), WindProcessor, Region
├── analysis/      # [3. análise] Statistics, ProfileAnalyzer, TimeSeriesAnalyzer, charts, summary
├── persistence/   # [3.5 persistência] Database (sqlite3), schemas, repositories (CRUD)
├── output/        # [4. resultados] MapGenerator, MatrixGenerator (+ BlueSky)
├── api/           # [5. servidor] app FastAPI modular (lifespan) + routers/
│   └── routers/   # health, catalog, gribs, maps, matrices, analysis, metar, files, history
└── METAR/         # parser PythonMETAR (cópia vendada, funciona offline)
```

Fluxo de dados:

1. **Captação** — `GribDownloader` baixa GRIBs do NOMADS com `wget` e registra cada arquivo na tabela `downloads` (status pending/downloaded/skipped/failed). `MetarClient` busca METARs na API da aviationweather.gov.
2. **Tratamento** — `DataProcessor` seleciona variáveis (via `VAR_MAP`), resolve níveis de pressão, recorta a região e converte unidades. `WindProcessor` é o único lugar que calcula vento.
3. **Análise** — `StatisticsAnalyzer` (média, mediana, desvio, percentis…), `ProfileAnalyzer` (perfil 150–1000 hPa), `TimeSeriesAnalyzer` (tendência via OLS com p-valor e R²) e `AnalysisCharts` (gráficos PNG).
4. **Persistência** — resultados e metadados gravados em `data/met_server.db` (tabelas `downloads`, `outputs`, `metar_obs`, `tasks`, `analysis_results`).
5. **Resultados** — mapas PNG e matrizes CSV (incl. BlueSky) salvos em disco e registrados na tabela `outputs`.
6. **Servidor** — FastAPI expõe tudo via REST; artefatos baixáveis em `GET /files/...`.

## 3. Banco de dados (SQLite)

Banco padrão: **`data/met_server.db`** (configurável com `db_file=` em `environment/path.conf`). Usa `sqlite3` da stdlib com modo **WAL** (leitura/escrita concorrente segura).

| Tabela | Conteúdo | Populada por |
|---|---|---|
| `downloads` | data, análise, resolução, previsão, caminho, tamanho, status, erro | `GribDownloader` |
| `outputs` | tipo (map/matrix/bluesky/chart), variável, nível, região, data, caminho | geradores de saída |
| `metar_obs` | ICAO, região, texto bruto, parsed/metadata JSON, hora da observação | `MetarClient` |
| `tasks` | tarefas em background (download) — status persiste entre reinícios | API |
| `analysis_results` | resultados de análise em JSON (cache + histórico) | API de análise |

- **Cache de análises**: ao repetir o mesmo cálculo (`/analysis/*`), o resultado é re-servido do banco com a marca `"**cached**": true` — sem recomputar.
- **Backup**: basta copiar `data/met_server.db` (o WAL gera `-wal`/`-shm` adjacentes).
- **Inspeção**: `./scripts/run.sh db-status` ou `GET /db/status`.

## 4. Pré-requisitos e instalação

- Linux (Ubuntu 22.04+, Debian 12+, CentOS 7+), Python 3.11+, `wget` no PATH;
- Libs de sistema para `pygrib` (instalação local): `libeccodes-dev`;
- Ambiente virtual recomendado: `~/envs/met` (já contém pygrib, Cartopy, scipy, pandas, statsmodels).

```bash
python3 -m venv ~/envs/met
source ~/envs/met/bin/activate
pip install -r requirements.txt
./scripts/run.sh install    # cria diretórios e valida imports
./scripts/run.sh test       # 102 testes, offline
./scripts/run.sh server     # uvicorn server_MET.api.app:app na porta 8000
```

## 5. Configuração — `environment/path.conf`

Formato `chave=valor` (sem seções). Todos os caminhos são relativos à raiz do projeto:

```
dir_gribs=data/gribs
dir_mapas=data/mapasGrib
dir_matrizes=data/matrizGrib
dir_matrizes_predi=data/matrizGrib/predi
dir_matrizes_bluesky=data/matrizGrib/bluesky
dir_analise=data/analise
dir_tmp=data/tmp
db_file=data/met_server.db
```

Acesse via o singleton `Settings` (`server_MET.core.config`) — **nunca hardcode `data/...`**:

```python
from server_MET.core.config import Settings
s = Settings()
print(s.dir_gribs, s.db_path)
```

## 6. Variáveis e níveis

### 6.1. Chaves internas (`VAR_MAP` em `server_MET/core/constants.py`)

| Chave | Variável GRIB | Nível | Unidade exibida |
|---|---|---|---|
| `ps` | Surface pressure | surface | hPa |
| `prnm` | Pressure reduced to MSL | meanSea | hPa |
| `temp` | Temperature | isobaricInhPa | °C |
| `temps` | Temperature | surface | °C |
| `nuvem` | Total Cloud Cover | isobaricInhPa | % |
| `chuvaNaoConvec` | Total Precipitation | surface | mm |
| `chuvaConvec` | Convective precipitation | surface | mm |
| `umidadeRel` | Relative humidity | isobaricInhPa | % |
| `u` / `v` | U/V component of wind | isobaricInhPa | m/s |
| `uSupe` / `vSupe` | U/V component of wind | heightAboveGround | m/s |

> `wind` e `winds` (API) são **calculados** a partir de `u`/`v` e `uSupe`/`vSupe` — não são variáveis GRIB.

### 6.2. Níveis

`PRESSURE_LEVELS = [150…1000] hPa` (passo de 50, mais 925/950/975). Níveis fora do intervalo são limitados e ajustados ao nível mais próximo. Variáveis de superfície esperam `level=None`.

## 7. Regiões

Regiões predefinidas (`server_MET/processing/regions.py`): `SP, RJ, AM, DF, PR, RS, MG, PA, PE, CE, SA`. O **nome da região é preservado** nos arquivos gerados e nos registros do banco (ex.: `GFS_0.25_SP_N500_temp_20260731_00.png`).

A API aceita três formas de seleção:
1. **Nome** — `"region": "SP"`;
2. **Bounding box** — `lon_min/lon_max/lat_min/lat_max`;
3. **Centro** — `lon`/`lat` (bbox de ±5°).

## 8. API REST

Base: `http://localhost:8000` — docs interativas em `/docs`.

### Informação e catálogo

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Informações da API |
| GET | `/health` | Status, versão, disponibilidade de GRIBs, uptime |
| GET | `/variables` | Chaves de variáveis (inclui `wind`/`winds`) |
| GET | `/regions` | Regiões predefinidas com bounds e descrição |
| GET | `/catalog` | Datas/análises/resoluções GRIB disponíveis no disco |
| GET | `/db/status` | Tabelas do banco SQLite e contagem de registros |

### GRIBs e downloads

| Método | Rota | Descrição |
|---|---|---|
| GET | `/gribs/list?date=YYYYMMDD` | Arquivos GRIB disponíveis |
| POST | `/gribs/download?date_str=…&analysis_hour=…` | Inicia download em background (query params!) |
| GET | `/gribs/download/{task_id}` | Status da tarefa (pending/running/done/failed + arquivos) |
| POST | `/gribs/info` | Variáveis do arquivo de uma data/análise/previsão |

```bash
curl -X POST "http://localhost:8000/gribs/download?date_str=20260731&analysis_hour=06"
# {"status": "download_started", "task_id": "a1b2c3…"}
```

### Mapas e matrizes

| Método | Rota | Descrição |
|---|---|---|
| POST | `/maps/generate` | Gera mapas PNG (retorna caminhos em `data/tmp/<uuid>/`) |
| POST | `/matrices/generate` | Gera matrizes CSV |
| POST | `/bluesky/wind` | Gera matriz BlueSky em `data/matrizGrib/bluesky/` |
| GET | `/files/{kind}/{path}` | Baixa artefato gerado (`mapas`, `matrizes`, `bluesky`, `analise`, `tmp`) |

```bash
curl -X POST http://localhost:8000/maps/generate \
  -H "Content-Type: application/json" \
  -d '{"variable":"temp","level":500,"region":"SP","date":"20260731","analysis":"06"}'
# {"maps": ["…/data/tmp/<uuid>/GFS_0.25_SP_N500_temp_20260731_00.png"], "count": 2}
```

### Análise (novo na v3)

| Método | Rota | Descrição |
|---|---|---|
| POST | `/analysis/summary` | Estatística descritiva por previsão (min, max, média, mediana, DP, percentis p1–p99) |
| POST | `/analysis/profile` | Perfil vertical da variável em todos os níveis 150–1000 hPa |
| POST | `/analysis/timeseries` | Série nas previsões f00–f18 + tendência linear (statsmodels: slope, p-valor, R²) |
| POST | `/analysis/charts` | Gráficos PNG (perfil, série com tendência, histograma) |
| GET | `/analysis/regions/{region}` | Estado consolidado da região (dados disponíveis + METAR) |

Resultados são persistidos em `analysis_results` e re-servidos como cache.

```bash
curl -X POST http://localhost:8000/analysis/timeseries \
  -H "Content-Type: application/json" \
  -d '{"variable":"temp","level":500,"region":"SP","date":"20260731","analysis":"06"}'
# {"variable":"temp","region":"SP","series":[{"forecast":0,"value":-9.9},…],
#  "trend":{"slope":0.012,"p_value":0.04,"r_squared":0.9,"direction":"crescente"}}
```

### METAR e histórico

| Método | Rota | Descrição |
|---|---|---|
| POST | `/metar/fetch` | METAR por região ou ICAO (`{"region":"SP"}` ou `{"icao_code":"SBGR"}`) |
| GET | `/metar/all` | METARs das 9 estações |
| GET | `/metar/stations` | Mapa de estações por região |
| GET | `/metar/history?icao=` | **Arquivo histórico** de observações (SQLite) |
| GET | `/history/downloads` | Histórico de downloads |
| GET | `/history/outputs` | Histórico de artefatos gerados |
| GET | `/history/analysis` | Histórico de análises |
| POST | `/cleanup?days_old=2` | Remove dados antigos (gribs+mapas+matrizes+análises) |

## 9. Sistema METAR

- **Fetch**: `https://aviationweather.gov/api/data/metar?ids={icao}&format=json&hours=2` (a antiga `adds/dataserver_current` foi descontinuada — 403).
- **Parser**: cópia vendada de PythonMETAR em `server_MET/METAR/` — funciona offline.
- **Estações**: SP=SBGR, RJ=SBGL, CW=SBCT, PA=SBPA, BH=SBCF, BE=SBBE, MA=SBEG, RF=SBRF, FZ=SBFZ.
- Cada observação é salva em `metar_obs` (histórico consultável em `/metar/history`).

```python
from server_MET.acquisition.metar_client import MetarClient
c = MetarClient()
m = c.get_metar("SBGR")          # fetch + parse + persistência
p = c.get_parsed_metar("SBPA", "METAR SBPA 212200Z 12005KT 9999 SCT030 18/12 Q1020=")  # offline
print(m["parsed"]["wind"])       # {'direction': 80, 'speed': 5, ...}
```

## 10. Scripts

```bash
./scripts/run.sh install                          # dependências + diretórios
./scripts/run.sh server                           # uvicorn server_MET.api.app:app --port 8000
./scripts/run.sh download [YYYYMMDD] [HH] [0p25|0p50|1p00]
./scripts/run.sh analysis [YYYYMMDD]              # exemplo de análise para a região SP
./scripts/run.sh db-status                        # estado do banco SQLite
./scripts/run.sh test                             # pytest tests/ (102 testes)
./scripts/run.sh clean [days]                     # remove dados antigos (default 2)
./scripts/run.sh docker-build | docker-up | docker-down
```

## 11. Testes

```bash
~/envs/met/bin/python -m pytest tests/ -v     # 102 testes, offline
```

Organizados por camada: `test_core` (config/regiões/modelos), `test_processing` (vento/METAR offline), `test_persistence` (SQLite CRUD em `tmp_path`), `test_analysis` (estatística/perfis/séries com tendência sintética), `test_output` (geradores sem GRIB) e `test_server` (endpoints via httpx `ASGITransport`). Testes de rede toleram indisponibilidade.

## 12. Docker

```bash
./scripts/run.sh docker-build && ./scripts/run.sh docker-up
```

`Dockerfile` (python:3.11-slim) instala `wget`, `libgfortran5` e `libgomp1` (pygrib prebuilt). Volumes nomeados persistem gribs, mapas, matrizes, análises e o banco SQLite; `environment/` é montado do host.

## 13. Manutenção e troubleshooting

| Problema | Causa | Solução |
|---|---|---|
| `pygrib` não instala | Faltam libs do sistema | `apt install libeccodes-dev` |
| Download não executa | `wget` ausente | Instalar `wget` |
| Nenhum arquivo baixado | Ciclo GFS ainda não publicado | NOMADS publica ~4h após a hora; tente outra data/análise |
| Mapas não gerados | Sem Cartopy nem Basemap | `pip install cartopy scipy` |
| `404` em mapas/matrizes/análises | Arquivo GRIB não existe | Rodar `/gribs/download` primeiro |
| Análise retorna `**cached**` | Resultado já computado | Apagar registros de `analysis_results` ou usar outra data |
| METAR vazio | ICAO inválido ou rede | Verificar código ICAO e acesso a aviationweather.gov |
| Tarefa de download sumiu? | Nunca some — fica em `tasks` | `GET /gribs/download/{task_id}` a qualquer momento |

## 14. Changelog

- **v3.0.0** — arquitetura modular em camadas (core/acquisition/processing/analysis/persistence/output/api); **camada de análise** (estatística descritiva, perfil vertical, séries temporais com tendência statsmodels, gráficos profissionais); **persistência SQLite** (downloads, outputs, metar_obs, tasks, analysis_results com cache); servidor de artefatos via HTTP com anti path-traversal; tarefas de download com status persistente; nome de região preservado em arquivos; `GET /` e `/catalog`; entrypoint `server_MET.api.app:app`; 102 testes.
- **v2.0.0** — arquitetura FastAPI consolidada; METAR com a nova API aviationweather (JSON); mapas com Cartopy (fallback Basemap); saídas em `data/tmp`; limpeza de gribs+mapas+matrizes.
