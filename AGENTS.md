# AGENTS.md

Servidor meteorológico **FastAPI v4.4.0** (API REST pura) com pipeline modular: **captação** (NOAA GFS GRIB2 + METAR, scheduler contínuo), **tratamento** (pygrib/numpy), **análise** (estatística, perfis, séries com statsmodels, dashboard OLS/HC3), **persistência** (SQLite WAL, dupla persistência CSV + `grid_data` + tabela `statistics`) e **distribuição** (mapas PNG, GIFs, matrizes CSV, BlueSky). Pacote: `server_MET`, entrypoint `server_MET.api.app:app` (uvicorn, porta 8000).

## README.md

`README.md` é a fonte única de documentação (v4.4.0, em português — linguagem simples + referência técnica no apêndice). Se mudar comportamento, atualize-o.

## Comandos

```bash
~/envs/met/bin/python -m pytest tests/ -v   # venv do projeto; 135 testes, offline
./scripts/run.sh server          # uvicorn server_MET.api.app:app --port 8000 (scheduler incluso)
./scripts/run.sh download [YYYYMMDD] [HH] [0p25|0p50|1p00]   # GFS download
./scripts/run.sh analysis [YYYYMMDD]   # exemplo de análise (SP)
./scripts/run.sh db-status       # tabelas/contagens do SQLite
./scripts/run.sh scheduler       # uma verificação de ciclo GFS (worker avulso)
./scripts/run.sh scheduler-status
./scripts/run.sh clean [days]    # remove dados antigos (default 2)
```

O venv é `~/envs/met` (inclui pandas, statsmodels, Pillow, Cartopy). Sem toolchain de lint/typecheck configurado (ruff/black em `pyproject.toml` apenas); não invente comandos de lint.

## Arquitetura (camadas)

```
server_MET/
├── core/            # Settings (path.conf), constants (VAR_MAP, VAR_LABELS_PT, níveis, horas),
│                    #   models Pydantic, logging_conf
├── acquisition/     # [captação] grib_downloader (wget + registro), grib_reader (pygrib),
│                    #   metar_client (aviationweather + parser), scheduler (contínuo + pipeline)
├── processing/      # [tratamento] processor (seleção, unidades, níveis, extração),
│                    #   wind (cálculos centralizados), regions (estados + cidades + países)
├── analysis/        # [análise] statistics, profiles, timeseries (statsmodels OLS), charts, summary, dashboard
├── persistence/     # [persistência] database (sqlite3 WAL), schemas, repositories (+ ingest_state)
├── output/          # [resultados] maps (Cartopy/Basemap), animation (GIF/Pillow),
│                    #   matrices (+ BlueSky), base
├── api/             # [servidor] app.py (lifespan) + routers/
│   └── routers/     # health, catalog, gribs, maps, matrices, analysis, metar, files, history, scheduler
└── METAR/           # parser PythonMETAR vendado (import from server_MET.METAR)
```

## Regiões (v4)

- `REGIOES_PREDEFINIDAS` = **estados** com bboxes precisas.
- `PAISES_AMERICA_DO_SUL` = **12 países** (BR, AR, BO, CL, CO, EC, GY, PY, PEU, SR, UY, VE) com bboxes precisas.
- `CIDADES_PREDEFINIDAS` = chaves `SP-CIDADE`... (centro da capital ±0.5°, via `CIDADE_RAIO_GRAUS`).
- `Region` tem `kind` (estado/cidade/pais/visao_geral/bbox/centro) e `full_name` — usado em títulos e nomes de arquivo.
- `todas_as_regioes()` e `cidades_predefinidas()` auxiliam pipeline e catálogo. `REGIOES_ICAO` → `AERODROMOS` mapeia região → aeródromo.

## Gotchas

- `Settings` (server_MET/core/config.py) é singleton lendo `environment/path.conf` (`chave=valor`); caminhos relativos a `PROJECT_ROOT`. **Nunca hardcode `data/...`** — use `Settings`. `ensure_dirs()` roda no lifespan. Chaves: `scheduler_enabled`, `scheduler_grib_interval_min`, `scheduler_metar_interval_min`, `scheduler_auto_pipeline`, `scheduler_auto_statistics`, `scheduler_resolution` (default `0p25`), `forecast_hours` (CSV `00,06,12,18`), `pipeline_levels` (CSV `850,500,200`).
- Diretórios de dados: `data/gribs`, `data/mapasGrib`, `data/matrizGrib/{bluesky}`, `data/analise`, `data/tmp`. Banco: `data/met_server.db`.
- GRIBs: `data/gribs/YYYYMMDD/HH/gfs.t{HH}z.pgrb2.{0p25|0p50|1p00}.f0{FF}`. Download usa `wget` via subprocess (obrigatório; `check_url_exists` falha silenciosamente sem ele).
- **Validação GRIB obrigatória em subprocesso** (`GribDownloader.validate_grib`, `GribReader.is_healthy`/`filter_healthy`): pygrib/eccodes travam em loop infinito em arquivo corrompido — try/except no mesmo processo não funciona.
- **`extract_data` (v4)**: `_normalize_lat` inverte DADOS e latitude juntos (S→N). Não altere só a latitude.
- `VAR_MAP` em `server_MET/core/constants.py` (não em processor). Inclui superfície/próximas da superfície (2m/10m/100m, CAPE, CIN, helicidade, rajada, neve, precipitação), **poluição** (`ozonio` por nível, `ozonioTot` coluna) e **níveis médios/altos** (`gh`, `omega`, `vortabs` — `isobaricInhPa`). `VAR_FIXED_LEVEL` fixa nível (2/10/100m). `wind`/`winds` calculados (u/v) — **não** estão no VAR_MAP.
- Níveis de pressão: clamp 1–1000 hPa com snap para `PRESSURE_LEVELS` (GFS 0.25°). Variáveis de superfície esperam `level=None`. `GribReader.available_levels()` descobre níveis via subprocesso.
- `load_gribs` retorna `pygrib.open` (nível arquivo), sem `.dataDate`/`.forecastTime` — use mensagens de `select_variable_from_gribs` para metadados. Feche com `close_gribs()`.
- `Region.name` preserva nome predefinido; `Region.full_name` para exibição. Arquivos usam slug de `full_name`.
- Vento só em `WindProcessor`. Unidades só em `DataProcessor.convert_units`.
- Repos em `persistence/repositories.py` (SQL parametrizado, nunca f-string). Conexão única `check_same_thread=False` + RLock; WAL. `get_database()` cria schema; `set_database()` para testes. `SCHEMA_VERSION = 3`.
- Análises cacheadas em `analysis_results` com `"**cached**": true`. Limpar registros para forçar recálculo.
- **Persistência dupla**: `MatrixGenerator` salva CSV + pontos em `grid_data`. Consulta via `GET /matrices/data`.
- **Dashboard/estatísticas**: `DashboardAnalyzer` → cards/hora + OLS (HC3, IC95, R², p-valor, Jarque-Bera) + perfil. Grava em tabela `statistics` + CSV em `data/analise`. API: `POST /analysis/dashboard` (computa+cache), `GET /analysis/dashboard` (cache), `GET /analysis/statistics` (tabela). Pipeline popula auto (`scheduler_auto_statistics`, `PIPELINE_STATS_VARS`).
- **Ciclos reais**: `GribReader.latest_available_cycle()`/`available_cycles()` lêem do disco. `GET /catalog/cycles` alimenta seletores — nunca inventar horas; vêm de `msg.forecastTime`/`msg.dataDate`.
- **Scheduler** (`acquisition/scheduler.py`): `SchedulerRunner` no lifespan (asyncio); `get_scheduler_runner()` singleton. `latest_published_cycle()` = agora − 5h (atraso NOMADS). Baixa resolução `scheduler_resolution` (default `0p25`). **Ciclo só marcado processado quando TODAS as `forecast_hours` existem e saudáveis** (`_cycle_has_complete_forecast`); parcial → re-verifica. Pipeline: `PIPELINE_VARS` = `MAIN_VARIABLES` + `winds`; `PIPELINE_LEVELED_VARS` = `temp,umidadeRel,ozonio` expandidas nos `pipeline_levels` (850,500,200). Mapas+matrizes para **todas regiões** (`todas_as_regioes()` exceto SA). Summary/timeseries sob demanda. `_run_pipeline`/`_run_statistics` compartilham `DataProcessor` (validação 1x/ciclo). Regiões restringíveis por `scheduler_auto_pipeline`. Estado em `ingest_state.processed_cycles` (JSON).
- **Startup imediato**: scheduler dispara verificação GRIB+METAR no lifespan
  **antes** de aceitar requests. `initial_acquisition()` é **bloqueante**:
  garante GRIBs do ciclo publicado (horas `forecast_hours` 00/06/12/18) e
  METARs no disco antes de servir — valida rápido arquivos existentes, baixa
  só o que falta; pipeline segue em segundo plano via `start()`.
- Animação GIF: `AnimationGenerator` usa `MapGenerator` + Pillow (`_compose_gif`). Kind `"gif"`. `.gif` → `image/gif` em `files.py`.
- METAR: API JSON `https://aviationweather.gov/api/data/metar?ids={icao}&format=json&hours=2`. Parser offline vendado. `MetarClient` extrai **todos** campos (runway, recent, trend, qfe, pressure_tendency, max/min_temp, precipitation, sunshine, snow_depth, present_weather, cloud_type/base/amount, wind_shear, icing, turbulence, remarks, metar_type, corrected) + derivados (vento km/h, direção cardinal, umidade, QNH inHg).
- API: `POST /gribs/download` usa **query params**, retorna `task_id`; `GET /gribs/download/{task_id}` persiste. `POST /maps/generate`, `/maps/animate`, `/matrices/generate`, `/analysis/charts` retornam JSON com caminhos `data/tmp/<uuid>`. Frontend converte para `/files/tmp/<rel>` (regex `/tmp/(.+)$`). `/maps/generate` e `/matrices/generate` respeitam `request.forecast`.
- Servir arquivos: `GET /files/{kind}/{path}` com `safe_join` (anti path-traversal). Kinds: `mapas`, `matrizes`, `bluesky`, `analise`, `tmp`.
- Mapas: matplotlib Agg + Cartopy (primário); Basemap fallback. Feições degradam offline. `HAS_MAP_BACKEND` em `output/maps.py`.
- Testes: httpx `ASGITransport`; `conftest` isola SQLite + **todos `Settings.dir_*`** em `tmp_path` por teste (`set_database` + monkeypatch) e limpa `dependencies._services`. Rede tolera status variáveis. Scheduler usa `FakeDownloader`.
- Dockerfile: `wget` + `libgfortran5` + `libgomp1` (pygrib prebuilt). docker-compose monta volumes dados + banco + `environment/`.

## Não versionar

`data/` inteiro gitignored (GRIBs, saídas, banco `met_server.db`). Artefatos legados deletados na v3 — não recriar.

## Misc

- Docs/strings para usuário em português.
- opencode MCP servers (context7, github) em `opencode.json` — reinicie opencode após alterar.