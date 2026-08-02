# AGENTS.md

Servidor meteorológico **FastAPI v3.0.0** com pipeline modular: **captação** (NOAA GFS GRIB2 + METAR), **tratamento** (pygrib/numpy), **análise** (estatística, perfis, séries com statsmodels), **persistência** (SQLite) e **distribuição** (mapas PNG, matrizes CSV, BlueSky). Pacote: `server_MET`, entrypoint `server_MET.api.app:app` (uvicorn, porta 8000).

## README.md

`README.md` é a fonte única de documentação (v3.0.0, em português). Se mudar comportamento, atualize-o. Documentação de APIs, banco e arquitetura está lá.

## Comandos

```bash
~/envs/met/bin/python -m pytest tests/ -v   # venv do projeto; 102 testes, offline
./scripts/run.sh server          # uvicorn server_MET.api.app:app --port 8000
./scripts/run.sh download [YYYYMMDD] [HH] [0p25|0p50|1p00]   # GFS download
./scripts/run.sh analysis [YYYYMMDD]   # exemplo de análise (SP)
./scripts/run.sh db-status       # tabelas/contagens do SQLite
./scripts/run.sh clean [days]    # remove dados antigos (default 2)
```

O venv é `~/envs/met` (inclui pandas e statsmodels). Sem toolchain de lint/typecheck configurado (ruff/black em `pyproject.toml` apenas); não invente comandos de lint.

## Arquitetura (camadas)

```
server_MET/
├── core/            # Settings (path.conf), constants (VAR_MAP, níveis, horas),
│                    #   models Pydantic, logging_conf
├── acquisition/     # [captação] grib_downloader (wget + registro em downloads),
│                    #   grib_reader (pygrib), metar_client (aviationweather + parser)
├── processing/      # [tratamento] processor (seleção, unidades, níveis, extração),
│                    #   wind (cálculos centralizados), regions (Região + predefinidas)
├── analysis/        # [análise] statistics, profiles, timeseries (statsmodels OLS), charts
├── persistence/     # [persistência] database (sqlite3 WAL), schemas, repositories
├── output/          # [resultados] maps (Cartopy/Basemap), matrices (+ BlueSky), base
├── api/             # [servidor] app.py (lifespan) + dependencies + routers/
│   └── routers/     # health, catalog, gribs, maps, matrices, analysis, metar, files, history
└── METAR/           # parser PythonMETAR vendado (import from server_MET.METAR)
```

## Gotchas

- `Settings` (server_MET/core/config.py) é singleton lendo `environment/path.conf` (`chave=valor`); caminhos relativos a `PROJECT_ROOT`. **Nunca hardcode `data/...`** — use `Settings`. `ensure_dirs()` roda no lifespan.
- Diretórios de dados: `data/gribs`, `data/mapasGrib`, `data/matrizGrib/{predi,bluesky}`, `data/analise`, `data/tmp`. Banco: `data/met_server.db` (`db_file=` no path.conf).
- GRIBs vivem em `data/gribs/YYYYMMDD/HH/gfs.t{HH}z.pgrb2.{0p25|0p50|1p00}.f0{FF}`. `GribReader.find_grib_file` casa por `.f0{ff}` + resolução. Download usa o binário `wget` via subprocess (obrigatório; `check_url_exists` falha silenciosamente sem ele).
- `VAR_MAP` está em `server_MET/core/constants.py` (não em processor). `wind`/`winds` são calculados (u/v, uSupe/vSupe) e **não** estão no VAR_MAP.
- Níveis de pressão: clamp 150–1000 hPa com snap para `PRESSURE_LEVELS`. Variáveis de superfície esperam `level=None`.
- **`load_gribs` retorna objetos `pygrib.open` (nível de arquivo), sem `.dataDate`/`.forecastTime`** — use as mensagens retornadas por `select_variable_from_gribs` para metadados de mensagem. Feche com `close_gribs()` ou `grb.close()`.
- `Region.name` preserva o nome da região predefinida (ex.: `SP`) — usado em nomes de arquivos e no banco. Regiões por bbox geram nome descritivo.
- Cálculo de vento apenas em `WindProcessor` (speed, nós, direção met/azimute, altitude). Unidades só em `DataProcessor.convert_units`.
- Persistência: repos em `server_MET/persistence/repositories.py` (SQL parametrizado, nunca f-string). Conexão única com `check_same_thread=False` + RLock; WAL mode. `get_database()` cria schema no primeiro uso; `set_database()` é usado nos testes.
- Análises persistidas em `analysis_results` e re-servidas com `"**cached"**: true` (não recomputa). Limpar registros para forçar recálculo.
- METAR: API JSON nova (`https://aviationweather.gov/api/data/metar?ids={icao}&format=json&hours=2`); a antiga `adds/dataserver_current` está morta (403). Parsing offline com parser vendado.
- API: `POST /gribs/download` usa **query params** (`date_str`, `analysis_hour`, `resolutions`, `force`) e retorna `task_id`; status em `GET /gribs/download/{task_id}` (persistente). `POST /maps/generate`, `/matrices/generate` e `/analysis/charts` retornam JSON com caminhos em `data/tmp/<uuid>`.
- Servir arquivos: `GET /files/{kind}/{path}` com `safe_join` (anti path-traversal). Kinds: `mapas`, `matrizes`, `bluesky`, `analise`, `tmp`.
- Mapas: matplotlib Agg + Cartopy (primário, está no venv); Basemap fallback. Feições geográficas degradam offline. `HAS_MAP_BACKEND` em `server_MET/output/maps.py`.
- `tests/` usa httpx `ASGITransport`; conftest isola o SQLite em `tmp_path` por teste (`set_database`). Testes de rede toleram status variáveis.
- Dockerfile precisa `wget` + `libgfortran5` + `libgomp1` (pygrib prebuilt); docker-compose monta volumes para dados + banco e `environment/` do host.

## Não versionar

`data/` inteiro é gitignored (GRIBs, saídas e o banco `met_server.db`). Artefatos legados (legacy/, classes_MET/, METARpy/, bash/, raiz gribs/ etc.) foram **deletados** na v3 — não recriar.

## Misc

- Docs e strings para o usuário são em português.
- opencode MCP servers (context7, github) configurados em `opencode.json` — carregados no startup; reinicie o opencode após alterar.
