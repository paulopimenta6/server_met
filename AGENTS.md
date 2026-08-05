# Server MET v2.0 - Agent Instructions

## Project Overview
Meteorological & pollution data server: downloads real GFS (NOAA filter endpoint) and live METAR (AviationWeather), extracts variables, generates PNG maps, stores everything in SQLite+CSV, and serves via a FastAPI REST + a simple frontend with a statistical dashboard.

## Quick Start
```bash
cd /home/paulo/Documentos/meus_codigos/server_met
source ~/envs/met/bin/activate
bash scripts/pipeline.sh                 # download real GFS + METAR, generate maps, populate SQLite
bash scripts/server.sh start             # start the API (start|stop|restart|status)
```

## Key Commands
| Task | Command |
|------|---------|
| Run pipeline (real data) | `bash scripts/pipeline.sh` |
| Pipeline (custom) | `PYTHONPATH=. python scripts/process_data.py --date 20260804 --analysis 00 --regions SP RJ PR` |
| Run API (dev) | `uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload` |
| Server wrapper | `bash scripts/server.sh {start\|stop\|restart\|status}` |
| E2E validation | `bash scripts/validate.sh` |
| E2E tests | `PYTHONPATH=. pytest tests/test_e2e.py -v` (in-process TestClient) |

## Pipeline behavior (read before running — it hits NOAA)
- **Default scope is huge**: all analyses (00/06/12/18) × all forecasts (f000–f018) for every variable×region — hundreds of NOAA downloads. Narrow with `--analysis 00 06` (accepts multiple) and `--forecast 00 06`; scale regions with `--regions`.
- Default regions: `SP RJ PR RS MG AM` (not all 18). Default dataset: `DEFAULT_VARIABLES` in `scripts/process_data.py` (temp 1000/850/500, umidadeRel/u/v 850, o3 500, total_o3, ps).
- `--all-variables` processes all 21 codes; ones absent from GFS are skipped and logged as errors.
- Unavailable GFS cycles are auto-skipped; without `--date` it tries today then yesterday.
- Downloaded GRIB files are cached in `data/grib/<date>/<ana>/` and skipped if already present (idempotent).

## Architecture
```
core/        # Business logic: config, variables, regions, persistence, downloader, grib_reader, processor, maps, metar
api/         # FastAPI app + routes (health, data, maps, metar) + schemas
frontend/    # Static frontend served by FastAPI (index.html, app.js, style.css) with dashboard
scripts/     # process_data.py + shell wrappers (pipeline.sh, server.sh, validate.sh)
tests/       # test_e2e.py (end-to-end with real data)
data/        # Runtime (gitignored): grib/, sqlite/, csv/, metar/
maps/        # Generated PNGs (gitignored)
```
Optional Docker: `Dockerfile` + `docker-compose.yml` (api service always on; pipeline runs only via `--profile manual`).

## Environment
- Python venv: `~/envs/met/bin/activate` (required).
- Config: `.env` (copy from `.env.example`) and `core/config.py`. Note `core/config.py` also creates its dirs on import.
- All paths are computed from `core/config.py` (BASE_DIR) — no hardcoded absolute paths.
- System libs required for pygrib/basemap: `libeccodes-dev libproj-dev libgeos-dev` (see README/Dockerfile).

## Variables (21 total)
**Meteorological (12):** ps, prnm, temp, temps, nuvem, chuvaNaoConvec, chuvaConvec, umidadeRel, u, v, uSupe, vSupe
**Pollution (9):** o3, total_o3, no2, so2, co, pm25, pm10, aod, dust

Only **12 are available in GFS pgrb2 0p25** — the same set wired to the NOAA filter endpoint (`NOAA_FILTER_VARS` in `core/downloader.py`) and marked available in `AVAILABLE_IN_GFS` (`core/variables.py`): ps, prnm, temp, temps, nuvem, umidadeRel, u, v, uSupe, vSupe, o3, total_o3. Pollution available = only o3 + total_o3. The rest (no2, so2, co, pm25, pm10, aod, dust, chuvaNaoConvec, chuvaConvec) are catalog-only (`experimental`); `/data/variables` returns `available` and the frontend hides unavailable ones.

`varMET` at repo root is an ASCII dump of the GRIB file inventory — the reference used to confirm which variables exist in the product; tests assert exactly `{o3, total_o3}` pollution available, so don't change `AVAILABLE_IN_GFS` casually.

## Regions (18)
SP, RJ, AM, DF, PR, RS, MG, PA, PE, CE, SA, FOR, REC, SSA, BEL, BH, CWB, POA
Bounding boxes defined in `core/config.py` (`REGIOES`); unknown region codes are silently dropped by the pipeline.

## API Endpoints (most under `/api/v1`; `/health` and `/docs` are at root)
- `GET /health` (+ `/health/ready`) - health checks (root, no `/api/v1` prefix)
- `GET /data/variables`, `/data/regions`, `/data/dashboard`, `/data/available`
- `GET /data/` - query (?variable=&level=&region=&date=&analysis=&limit=); `/data/latest`, `/data/stats`, `/data/levels/{var}`, `/data/export/csv`
- `GET /maps/{var}/{region}` - PNG map (?level=&date=&analysis=); `/maps/list/{var}/{region}`
- `GET /metar/stations`, `/metar/{code}`, `/metar/latest/all`
- `GET /api/v1/info` - app metadata; `/docs` and `/redoc` at root

## Testing
```bash
bash scripts/validate.sh                 # deps + pipeline + SQLite + maps + E2E
PYTHONPATH=. pytest tests/test_e2e.py -v # full API E2E (in-process TestClient)
```
- **E2E tests read SQLite/maps and require a prior pipeline run** (they assert `total_records > 0`, METAR reports, PNGs). Run the pipeline first; tests then need no network.
- `scripts/validate.sh` **hardcodes `--date 20260804`** — it will fail once NOAA rotates that data out; for a date-agnostic check run the pipeline + pytest directly.

## Gotchas
- **Always set `PYTHONPATH=.`** when running Python scripts (imports use absolute `core.*`, `api.*`).
- Frontend asset paths must be `static/style.css` / `static/app.js` (bare `style.css` or `/static/...` 404) — enforced by tests.
- Surface variables (`ps`, temps, etc.) have `level_value = 0` / no `level` in maps and queries.
- Map filenames: `GFS_<res>_<REGION>_N<level|SFC>_<variable>_<analysis>_<date>_<forecast>.png` — variable codes may contain underscores (total_o3, umidadeRel, uSupe); `api/routes/maps.py` `_FILENAME_RE` parses them.
- AviationWeather returns the wrong state for some stations (SBGR shown as "PR"); `core/metar.py` corrects names from the local `DEFAULT_STATIONS` registry.
- `data/` and `maps/` are gitignored runtime artifacts; no systemd/scheduler — use `cron` with `scripts/pipeline.sh` if scheduling is needed.