# AGENTS.md

FastAPI server (v2.0.0) that downloads NOAA GFS GRIB2 data, processes it with `pygrib`/`numpy`, generates maps and BlueSky wind matrices, and decodes METAR reports. Package: `server_MET`, entrypoint `server_MET.server:app` (uvicorn, port 8000).

## README.md

`README.md` is up to date with the current architecture (v2.0.0). If you change behavior, update it; it is the single source of documentation. User-facing docs are in Portuguese.

## Commands

```bash
~/envs/met/bin/python -m pytest tests/ -v   # venv do projeto; or: ./scripts/run.sh test (52 tests, pass, offline)
./scripts/run.sh server          # uvicorn server_MET.server:app --port 8000
./scripts/run.sh download [YYYYMMDD] [HH] [0p25|0p50|1p00]   # GFS download; also ./scripts/download_gribs.sh
./scripts/run.sh clean [days]    # remove data antigos de gribs+mapas+matrizes (default 2)
```

The project venv is `~/envs/met` (activate with `source ~/envs/met/bin/activate`). There is no configured lint/typecheck toolchain installed; ruff/black config lives in `pyproject.toml`. Don't invent lint commands.

## Layout and gotchas

- `Settings` (server_MET/config.py) is a singleton reading `environment/path.conf` (plain `key=value`); paths resolve relative to `PROJECT_ROOT` (repo root). `ensure_dirs()` auto-creates all data dirs on server startup. Never hardcode `data/...` paths — go through `Settings`.
- Data dirs: `data/gribs`, `data/mapasGrib`, `data/matrizGrib/{predi,bluesky}`, `data/tmp` (outputs temporários da API).
- GRIB files live at `data/gribs/YYYYMMDD/HH/gfs.t{HH}z.pgrb2.{0p25|0p50|1p00}.f0{FF}`. `GribReader.find_grib_file` matches by `.f0{ff}` suffix + resolution substring. Downloads use the `wget` binary via subprocess (required; `check_url_exists` silently fails without it).
- Variable keys are Portuguese-ish internal names defined in `VAR_MAP` (server_MET/data_processor.py): `ps, prnm, temp, temps, nuvem, chuvaNaoConvec, chuvaConvec, umidadeRel, u, v, uSupe, vSupe`. `wind`/`winds` exist in the API enum (`models.py`) and in `/variables`, but are **not** in `VAR_MAP` (computed from u/v).
- Pressure levels clamp to 150–1000 hPa and snap to `PRESSURE_LEVELS`; surface variables expect `level=None`/"surface".
- METAR parsing uses a vendored copy of PythonMETAR at `server_MET/METAR/` (import `from server_MET.METAR import Metar`) — not installed from PyPI. Parsing is offline; fetching uses the **new** aviationweather JSON API (`https://aviationweather.gov/api/data/metar?ids={icao}&format=json&hours=2`) — the old `adds/dataserver_current` endpoint is retired (403).
- API quirks: `POST /gribs/download` takes **query params** (`date_str`, `analysis_hour`), not a JSON body. `POST /maps/generate` and `/matrices/generate` return JSON with file paths written under `data/tmp/<uuid>` — not PNG responses. Region requests need `region` name, a lon/lat bbox, or center `lon`/`lat` (see `_build_region` in server.py).
- Map generation uses matplotlib (Agg) with **Cartopy** as primary backend (installed in `~/envs/met`); Basemap is a fallback if Cartopy is absent. Feature data (coastlines/borders) degrades gracefully offline.
- `tests/` uses httpx `ASGITransport` + `@pytest.mark.asyncio`; METAR/network tests assert tolerant status codes (`200`/`404`), so failures don't depend on network.

## Don't touch: legacy artifacts

`legacy/`, `classes_MET/`, `METARpy/`, `bash/`, root scripts `goGribV2.sh`/`remove_GRIBS_antigos.sh`, text files `variables.txt`, `variable_inside_list.txt`, `varMET`, `varPythonGrib`, and the empty root dirs `gribs/`, `mapasGrib/`, `matrizGrib/` are old backups/artifacts (untracked and gitignored; kept on disk only). The live surface is `server_MET/`, `scripts/`, `environment/`, `tests/`.

## Misc

- Docs and user-facing strings are in Portuguese; keep that for user-facing output.
- Dockerfile needs `wget` + `libgfortran5` + `libgomp1` on python:3.11-slim (pygrib comes prebuilt). For local installs, pygrib may require system eccodes libraries.
- opencode MCP servers (context7, github) are configured in `opencode.json` — config is loaded at startup; remind the user to restart opencode after changing it.
- The project venv is `~/envs/met`; it includes scipy (needed by Cartopy streamplot). If `scipy` is missing, wind maps fall back to `quiver`.
