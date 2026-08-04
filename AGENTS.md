# Server MET v2.0 - Agent Instructions

## Project Overview
Meteorological & pollution data server: downloads GRIB from NOAA GFS, processes variables, stores in SQLite+CSV, serves via FastAPI REST + Leaflet frontend.

## Quick Start
```bash
cd /home/paulo/Documentos/meus_codigos/server_met
source ~/envs/met/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

## Key Commands
| Task | Command |
|------|---------|
| Run API (dev) | `uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload` |
| Run pipeline | `PYTHONPATH=. python scripts/run_pipeline.py` |
| Run scheduler | `PYTHONPATH=. python scripts/schedule.py` |
| Validate | `PYTHONPATH=. python scripts/validate_pipeline.py` |
| Docker | `docker-compose up -d` |
| Systemd install | `sudo ./deploy/install_systemd.sh` |

## Architecture
```
core/           # Business logic (config, variables, persistence, regions, downloader, grib_reader, processor)
api/            # FastAPI app + routes (health, data, maps)
frontend/       # Static files served by FastAPI (index.html, app.js, style.css)
scripts/        # Automation (run_pipeline, schedule, validate_pipeline, test_e2e)
data/           # Runtime: grib/, sqlite/, csv/ (gitignored)
maps/           # Generated PNGs (gitignored)
deploy/         # systemd services + Docker
legacy/         # Original shell scripts & classes_MET/ (reference only)
```

## Environment
- Python venv: `~/envs/met/bin/activate` (required)
- Config: `.env` (copy from `.env.example`)
- Paths: `environment/path.conf` → points to `data/grib`, `maps`, `data/csv`

## Variables (20 total)
**Meteorological (12):** ps, prnm, temp, temps, nuvem, chuvaNaoConvec, chuvaConvec, umidadeRel, u, v, uSupe, vSupe
**Pollution (8):** o3 (confirmed in GFS), no2, so2, co, pm25, pm10, aod, dust (experimental)

## Regions (18)
Original: SP, RJ, AM, DF, PR, RS, MG, PA, PE, CE, SA
New: FOR, REC, SSA, BEL, BH, CWB, POA

## API Endpoints (prefix `/api/v1`)
- `GET /health` - health check
- `GET /data/variables` - list all variables
- `GET /data/regions` - list all regions
- `GET /data/available` - available data summary
- `GET /data/` - query with filters (?variable=&level=&region=&date=&analysis=&limit=)
- `GET /data/latest` - latest record
- `GET /data/stats` - statistics
- `GET /data/levels/{var}` - available levels
- `GET /data/export/csv` - export CSV
- `GET /maps/{var}/{region}` - PNG map
- `GET /maps/geojson/{var}/{region}` - GeoJSON

## Testing
```bash
PYTHONPATH=. pytest tests/ -v          # unit tests
PYTHONPATH=. pytest scripts/test_e2e.py -v  # E2E (needs API running)
PYTHONPATH=. python scripts/validate_pipeline.py  # full validation
```

## Gotchas
- **Always set `PYTHONPATH=.`** when running scripts (imports use absolute `core.*`, `api.*`)
- NOAA GFS HTTPS returns 403; FTP also blocked. Use test GRIBs or mock for dev.
- Scheduler runs at 00:30, 06:30, 12:30, 18:30 (America/Sao_Paulo)
- Frontend served at `/` via FastAPI StaticFiles mount
- Legacy code in `classes_MET/`, `bash/`, `goGribV2.sh` - reference only, not used