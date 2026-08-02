# AGENTS.md

Servidor meteorológico **FastAPI v4.0.0** com pipeline modular: **captação** (NOAA GFS GRIB2 + METAR, com scheduler contínuo), **tratamento** (pygrib/numpy), **análise** (estatística, perfis, séries com statsmodels), **persistência** (SQLite) e **distribuição** (mapas PNG, GIFs, matrizes CSV, BlueSky, site interativo). Pacote: `server_MET`, entrypoint `server_MET.api.app:app` (uvicorn, porta 8000).

## README.md

`README.md` é a fonte única de documentação (v4.0.0, em português — linguagem simples na primeira parte, referência técnica no apêndice). Se mudar comportamento, atualize-o.

## Comandos

```bash
~/envs/met/bin/python -m pytest tests/ -v   # venv do projeto; 121 testes, offline
./scripts/run.sh server          # uvicorn server_MET.api.app:app --port 8000 (scheduler incluso)
./scripts/run.sh download [YYYYMMDD] [HH] [0p25|0p50|1p00]   # GFS download
./scripts/run.sh analysis [YYYYMMDD]   # exemplo de análise (SP)
./scripts/run.sh db-status       # tabelas/contagens do SQLite
./scripts/run.sh scheduler       # uma verificação de ciclo GFS (worker avulso)
./scripts/run.sh scheduler-status
./scripts/run.sh clean [days]    # remove dados antigos (default 2)
```

O venv é `~/envs/met` (inclui pandas, statsmodels, Pillow). Sem toolchain de lint/typecheck configurado (ruff/black em `pyproject.toml` apenas); não invente comandos de lint.

## Arquitetura (camadas)

```
server_MET/
├── core/            # Settings (path.conf), constants (VAR_MAP, VAR_LABELS_PT, níveis, horas),
│                    #   models Pydantic, logging_conf
├── acquisition/     # [captação] grib_downloader (wget + registro), grib_reader (pygrib),
│                    #   metar_client (aviationweather + parser), scheduler (contínuo + pipeline)
├── processing/      # [tratamento] processor (seleção, unidades, níveis, extração),
│                    #   wind (cálculos centralizados), regions (estados + cidades)
├── analysis/        # [análise] statistics, profiles, timeseries (statsmodels OLS), charts, summary
├── persistence/     # [persistência] database (sqlite3 WAL), schemas, repositories (+ ingest_state)
├── output/          # [resultados] maps (Cartopy/Basemap), animation (GIF/Pillow),
│                    #   matrices (+ BlueSky), base
├── web/             # site estático servido por FastAPI (index.html, css, js, Leaflet vendored)
├── api/             # [servidor] app.py (lifespan + StaticFiles + site em "/") + routers/
│   └── routers/     # health, catalog, gribs, maps (gerar + animar), matrices, analysis,
│                    #   metar, files, history, scheduler
└── METAR/           # parser PythonMETAR vendado (import from server_MET.METAR)
```

## Regiões (v4)

- `REGIOES_PREDEFINIDAS` = **estados** com bboxes precisas (SP agora é o estado real, não mais a caixa de 14°).
- `CIDADES_PREDEFINIDAS` = chaves `SP-CIDADE`... (centro da capital ±0.5°, via `CIDADE_RAIO_GRAUS`).
- `Region` tem `kind` (estado/cidade/visao_geral/bbox/centro) e `full_name` (ex.: "Cidade de São Paulo") — usado em títulos e nomes de arquivo. `RegionName` enum na API inclui as cidades.
- `todas_as_regioes()` e `cidades_predefinidas()` auxiliam pipeline e catálogo.

## Gotchas

- `Settings` (server_MET/core/config.py) é singleton lendo `environment/path.conf` (`chave=valor`); caminhos relativos a `PROJECT_ROOT`. **Nunca hardcode `data/...`** — use `Settings`. `ensure_dirs()` roda no lifespan. Novas chaves: `scheduler_enabled`, `scheduler_grib_interval_min`, `scheduler_metar_interval_min`, `scheduler_auto_pipeline`, `forecast_hours` (CSV `00,06,12,18`; limita horas de previsão capturadas/processadas).
- Diretórios de dados: `data/gribs`, `data/mapasGrib`, `data/matrizGrib/{predi,bluesky}`, `data/analise`, `data/tmp`. Banco: `data/met_server.db`.
- GRIBs vivem em `data/gribs/YYYYMMDD/HH/gfs.t{HH}z.pgrb2.{0p25|0p50|1p00}.f0{FF}`. Download usa o binário `wget` via subprocess (obrigatório; `check_url_exists` falha silenciosamente sem ele).
- **Arquivos baixados são validados** (`GribDownloader.validate_grib`): subprocesso pygrib com timeout (leitura + `select`); corrompido → removido e marcado `failed` (pygrib/eccodes podem **travar em loop infinito** lendo arquivo corrompido — não dá para usar try/except no mesmo processo; validação em subprocesso é obrigatória).
- **`extract_data` (v4)**: `_normalize_lat` inverte DADOS e latitude juntos (S→N) — sem isso o mapa fica com norte/sul trocados. Não altere só a latitude.
- `VAR_MAP` está em `server_MET/core/constants.py` (não em processor). `wind`/`winds` são calculados (u/v, uSupe/vSupe) e **não** estão no VAR_MAP. `VAR_LABELS_PT`/`var_label()` dão o nome em português para títulos e o site.
- Níveis de pressão: clamp 150–1000 hPa com snap para `PRESSURE_LEVELS`. Variáveis de superfície esperam `level=None`.
- **`load_gribs` retorna objetos `pygrib.open` (nível de arquivo), sem `.dataDate`/`.forecastTime`** — use as mensagens retornadas por `select_variable_from_gribs` para metadados. Feche com `close_gribs()` ou `grb.close()`.
- `Region.name` preserva o nome predefinido; `Region.full_name` é o nome completo para exibição. Nomes de arquivo usam slug (`_slugify`) de `full_name`.
- Cálculo de vento apenas em `WindProcessor` (speed, nós, direção met/azimute, altitude). Unidades só em `DataProcessor.convert_units`.
- Persistência: repos em `server_MET/persistence/repositories.py` (SQL parametrizado, nunca f-string). Conexão única com `check_same_thread=False` + RLock; WAL mode. `get_database()` cria schema no primeiro uso; `set_database()` é usado nos testes. `SCHEMA_VERSION = 2` (tabela `ingest_state`).
- Análises persistidas em `analysis_results` e re-servidas com `"**cached**": true` (não recomputa). Limpar registros para forçar recálculo.
- **Scheduler** (`acquisition/scheduler.py`): `SchedulerRunner` roda no lifespan (loops asyncio); `get_scheduler_runner()` é o singleton compartilhado com as rotas. `latest_published_cycle()` = agora − 5h (atraso de publicação do NOMADS). Pipeline automático (`PIPELINE_VARS`): mapas+matrizes+análises das regiões (estados+cidades, exceto SA) — regiões restringíveis por `scheduler_auto_pipeline`. Ciclos processados ficam em `ingest_state.processed_cycles` (JSON).
- Animação GIF: `output/animation.py` (`AnimationGenerator`) gera os quadros com `MapGenerator` e monta com Pillow (`_compose_gif`). Kind de saída: `"gif"` (em `OUTPUT_KINDS`). `.gif` → `image/gif` em `files.py`.
- **Site**: `GET /` serve `server_MET/web/static/index.html` (não é mais JSON — o JSON mudou para `/info`). `StaticFiles` montado em `/static`. Leaflet vendored em `web/static/vendor/leaflet/` (inclui `images/`). Tiles OSM exigem internet; o resto funciona offline.
- METAR: API JSON nova (`https://aviationweather.gov/api/data/metar?ids={icao}&format=json&hours=2`); a antiga `adds/dataserver_current` está morta (403). Parsing offline com parser vendado.
- API: `POST /gribs/download` usa **query params** e retorna `task_id`; `GET /gribs/download/{task_id}` persiste. `POST /maps/generate`, `/maps/animate`, `/matrices/generate` e `/analysis/charts` retornam JSON com caminhos em `data/tmp/<uuid>`. O frontend converte caminhos absolutos para `/files/tmp/<rel>` (regex `/tmp/(.+)$`).
- Servir arquivos: `GET /files/{kind}/{path}` com `safe_join` (anti path-traversal). Kinds: `mapas`, `matrizes`, `bluesky`, `analise`, `tmp`.
- Mapas: matplotlib Agg + Cartopy (primário, está no venv); Basemap fallback. Feições geográficas degradam offline. `HAS_MAP_BACKEND` em `server_MET/output/maps.py`.
- `tests/` usa httpx `ASGITransport`; conftest isola o SQLite em `tmp_path` por teste (`set_database`) e limpa `dependencies._services`. Testes de rede toleram status variáveis. Testes do scheduler usam `FakeDownloader` (sem rede).
- Dockerfile precisa `wget` + `libgfortran5` + `libgomp1` (pygrib prebuilt); docker-compose monta volumes para dados + banco e `environment/` do host.

## Não versionar

`data/` inteiro é gitignored (GRIBs, saídas e o banco `met_server.db`). Artefatos legados (legacy/, classes_MET/, METARpy/, bash/, raiz gribs/ etc.) foram **deletados** na v3 — não recriar.

## Misc

- Docs e strings para o usuário são em português.
- opencode MCP servers (context7, github) configurados em `opencode.json` — carregados no startup; reinicie o opencode após alterar.
