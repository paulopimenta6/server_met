# Servidor Meteorológico — MET Server (v2.0.0)

Servidor **FastAPI** para aquisição, processamento e distribuição de dados meteorológicos do modelo **GFS (Global Forecast System)** da **NOAA**, incluindo:

- Download automático de GRIBs GFS (resoluções 0.25°, 0.50° e 1.00°);
- Leitura e extração de variáveis com `pygrib`/`numpy`;
- Geração de **mapas meteorológicos** (contorno e campo de vento) com **Cartopy**;
- Geração de **matrizes CSV** de variáveis e de **matrizes de vento para BlueSky**;
- Consulta e decodificação de **METAR** de aeródromos brasileiros;
- API REST completa para integração.

---

## 1. Funcionalidades

| Recurso | Descrição |
|---|---|
| Download GFS | Arquivos completos do NOMADS (3 resoluções × horas de previsão 00/06/12/18) via `wget` |
| Leitura GRIB2 | `pygrib` + numpy: latitudes, longitudes, valores por variável/nível |
| Mapas | PNG com contornos (temperatura, pressão, umidade...) e streamplot de vento (Cartopy) |
| Matrizes | CSV por variável e por campo de vento (u, v, velocidade, direção) |
| BlueSky | CSV de vento em nós e altitude (ft) para a ferramenta BlueSky |
| METAR | Fetch da API aviationweather.gov + parser PythonMETAR (vendado) |
| Limpeza | Remoção automática de dados antigos (GRIBs, mapas e matrizes) |

## 2. Arquitetura

```
NOAA NOMADS (nomads.ncep.noaa.gov)  ──── wget ────▶  data/gribs/YYYYMMDD/HH/gfs.t{HH}z.pgrb2.{res}.f0{FF}
                                                        │
                                                        ▼
                              GribReader (pygrib) ──▶  DataProcessor (VAR_MAP, níveis, conversão de unidades)
                                                        │
                                    ┌───────────────────┼──────────────────────┐
                                    ▼                   ▼                      ▼
                           MapGenerator         MatrixGenerator          MetarClient
                           (Cartopy/Basemap)     (CSV, BlueSky)          (aviationweather.gov)
                                    │                   │                      │
                                    ▼                   ▼                      ▼
                              data/mapasGrib     data/matrizGrib          server_MET/METAR/
                                                                           (parser vendado)
                                    │                   │
                                    └───────────┬───────┘
                                                ▼
                                   FastAPI (server_MET/server.py, porta 8000)
```

Fluxo de dados:

1. **Download** — `GribDownloader` baixa arquivos GRIB2 completos do NOMADS
   (`https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{data}/{hh}/atmos/`)
   com o binário `wget` (obrigatório). Não há filtragem por variável/região.
2. **Leitura** — `GribReader` abre o arquivo com `pygrib` e extrai as mensagens GRIB.
3. **Processamento** — `DataProcessor` mapeia chaves internas para variáveis GRIB
   (`VAR_MAP`), resolve níveis de pressão e converte unidades (K→°C, Pa→hPa).
4. **Vento** — componentes U/V convertidos em magnitude e direção (convenção
   meteorológica: 0° = N, ângulo de onde o vento vem).
5. **Mapas** — PNG via matplotlib (Agg) com Cartopy como backend principal;
   Basemap é fallback caso Cartopy não esteja instalado.
6. **Matrizes** — CSV de variáveis ou campo de vento, e CSV BlueSky (nós/ft).
7. **METAR** — fetch na API JSON da aviationweather.gov e decodificação local
   com o parser PythonMETAR embutido em `server_MET/METAR/`.
8. **API** — FastAPI expõe tudo via REST.

## 3. Pré-requisitos e instalação

### 3.1. Sistema

- Linux (Ubuntu 22.04+, Debian 12+, CentOS 7+);
- Python 3.11+;
- `wget` instalado e no PATH;
- Bibliotecas do sistema para `pygrib` (compilação local): `libeccodes-dev`.

### 3.2. Ambiente virtual (recomendado)

```bash
python3 -m venv ~/envs/met
source ~/envs/met/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

O ambiente virtual do projeto é `~/envs/met` (já contém `pygrib`, `Cartopy`,
`scipy`, `matplotlib`, `fastapi`, `pytest`).

### 3.3. Verificação rápida

```bash
python -m pytest tests/ -v          # 52 testes
./scripts/run.sh server             # sobe o servidor na porta 8000
```

## 4. Configuração — `environment/path.conf`

Arquivo em formato `chave=valor` (sem seções INI):

```
dir_gribs=data/gribs
dir_mapas=data/mapasGrib
dir_matrizes=data/matrizGrib
dir_matrizes_predi=data/matrizGrib/predi
dir_matrizes_bluesky=data/matrizGrib/bluesky
dir_tmp=data/tmp
```

O singleton `Settings` (`server_MET/config.py`) lê o arquivo e resolve os
caminhos relativos à raiz do projeto. `ensure_dirs()` cria todos os
diretórios automaticamente na subida do servidor. **Nunca hardcode caminhos
`data/...` no código — use sempre `Settings`.**

```python
from server_MET.config import Settings
s = Settings()
print(s.dir_gribs)   # /caminho/para/server_met/data/gribs
```

## 5. Estrutura do projeto

```
server_met/
├── server_MET/                  # Pacote principal
│   ├── server.py                # FastAPI (app, endpoints)
│   ├── config.py                # Settings singleton (path.conf)
│   ├── grib_downloader.py       # Download GFS via wget + limpeza
│   ├── grib_reader.py           # Leitura GRIB2 (pygrib)
│   ├── data_processor.py        # VAR_MAP, níveis, conversão de unidades
│   ├── wind_processor.py        # Cálculos de vento (u/v → direção, nós, altitude)
│   ├── map_generator.py         # Mapas PNG (Cartopy, fallback Basemap)
│   ├── matrix_generator.py      # Matrizes CSV e BlueSky
│   ├── metar_client.py          # Cliente METAR (nova API aviationweather)
│   ├── region.py                # Regiões predefinidas e bboxes
│   ├── models.py                # Modelos Pydantic e enums
│   └── METAR/                   # Parser PythonMETAR (cópia vendada)
├── scripts/
│   ├── run.sh                   # Script principal (server/test/download/clean)
│   ├── download_gribs.sh        # Download em lote (bash)
│   └── clean_old_gribs.sh       # Limpeza de dados antigos
├── environment/path.conf        # Configuração de caminhos
├── tests/                       # 52 testes (core + API)
├── data/                        # Dados (auto-criado)
│   ├── gribs/YYYYMMDD/HH/       # GRIBs baixados
│   ├── mapasGrib/               # Mapas gerados
│   ├── matrizGrib/{predi,bluesky}/  # Matrizes
│   └── tmp/<uuid>/              # Saídas temporárias da API
├── Dockerfile / docker-compose.yml
├── pyproject.toml / requirements.txt / pytest.ini
└── AGENTS.md                    # Instruções para agentes de IA
```

> Diretórios `METARpy/`, `classes_MET/`, `legacy/`, `bash/`, `gribs/`,
> `mapasGrib/`, `matrizGrib/` e os arquivos de texto `variables.txt`,
> `variable_inside_list.txt`, `varMET`, `varPythonGrib` e os scripts
> `goGribV2.sh`/`remove_GRIBS_antigos.sh` na raiz são **artefatos antigos**
> (backup), fora do versionamento e do funcionamento do sistema.

## 6. Variáveis e níveis

### 6.1. Chaves internas (`VAR_MAP` em `data_processor.py`)

| Chave | Variável GRIB | Tipo de nível | Observação |
|---|---|---|---|
| `ps` | Surface pressure | surface | Pa → hPa |
| `prnm` | Pressure reduced to MSL | meanSea | Pa → hPa |
| `temp` | Temperature | isobaricInhPa | K → °C |
| `temps` | Temperature | surface | K → °C |
| `nuvem` | Total Cloud Cover | isobaricInhPa | % |
| `chuvaNaoConvec` | Total Precipitation | surface | mm |
| `chuvaConvec` | Convective precipitation (water) | surface | mm |
| `umidadeRel` | Relative humidity | isobaricInhPa | % |
| `u` / `v` | U/V component of wind | isobaricInhPa | m/s |
| `uSupe` / `vSupe` | U/V component of wind | heightAboveGround | m/s |

> `wind` e `winds` são chaves válidas na API (listadas em `/variables`) e
> **calculadas** a partir de `u`/`v` e `uSupe`/`vSupe` — não são variáveis GRIB.

### 6.2. Níveis de pressão

`PRESSURE_LEVELS = [150, 200, ..., 1000]` hPa. Níveis solicitados são
limitados ao intervalo 150–1000 hPa e ajustados ao nível mais próximo.
Variáveis de superfície esperam `level=None` (ou `"surface"`).

## 7. Regiões

Regiões predefinidas (`server_MET/region.py`):
`SP, RJ, AM, DF, PR, RS, MG, PA, PE, CE, SA` (América do Sul).

A API aceita três formas de seleção de região:
1. **Nome** — `"region": "SP"`;
2. **Bounding box** — `lon_min/lon_max/lat_min/lat_max`;
3. **Centro** — `lon`/`lat` (cria bbox de ±5°).

## 8. API REST

Base: `http://localhost:8000` — docs interativas em `/docs`.

### 8.1. `GET /health`

```json
{"status": "ok", "version": "2.0.0", "grib_files_available": true, "uptime": 1234.5}
```

### 8.2. `GET /variables`

Lista as chaves de variáveis (inclui `wind`/`winds` calculados).

### 8.3. `GET /regions`

Regiões predefinidas com bounds `[lon_min, lon_max, lat_min, lat_max]`.

### 8.4. `GET /gribs/list?date=YYYYMMDD`

Lista os arquivos GRIB disponíveis (`{"gribs": [...], "count": N}`).

### 8.5. `POST /gribs/download`

Inicia o download em background. **Usa query params, não body JSON:**

```bash
curl -X POST "http://localhost:8000/gribs/download?date_str=20260731&analysis_hour=06"
```

```json
{"status": "download_started", "date": "20260731", "analysis": "06"}
```

Baixa as 3 resoluções × horas de previsão 00/06/12/18 da análise escolhida.

### 8.6. `POST /gribs/info`

```bash
curl -X POST http://localhost:8000/gribs/info \
  -H "Content-Type: application/json" \
  -d '{"variable":"temp","level":500,"region":"SP","date":"20260731","analysis":"06","forecast":"00"}'
```

Retorna o arquivo encontrado e a lista de variáveis GRIB. Sem `analysis`,
tenta a hora de análise atual e faz fallback para análises disponíveis.
`404` quando não há arquivo.

### 8.7. `POST /maps/generate`

Gera mapas PNG e **retorna JSON com os caminhos** dos arquivos (escritos em
`data/tmp/<uuid>/`), não o PNG em si:

```bash
curl -X POST http://localhost:8000/maps/generate \
  -H "Content-Type: application/json" \
  -d '{"variable":"temp","level":500,"region":"SP","date":"20260731","analysis":"06"}'
```

```json
{"maps": ["/caminho/.../data/tmp/<uuid>/GFS_0.25_..._N500_temp_20260731_00.png", "..."], "count": 2}
```

`variable` aceita qualquer chave de `/variables`, inclusive `wind`/`winds`
(campo de vento). Campos opcionais: `dpi` (72–600) e `title`.

### 8.8. `POST /matrices/generate`

Idem, para matrizes CSV (`{"matrices": [...], "count": N}`).

### 8.9. `POST /metar/fetch`

Por região ou ICAO:

```bash
curl -X POST http://localhost:8000/metar/fetch -H "Content-Type: application/json" -d '{"region": "SP"}'
curl -X POST http://localhost:8000/metar/fetch -H "Content-Type: application/json" -d '{"icao_code": "SBGR"}'
```

Resposta: `station`, `timestamp`, `raw_metar`, `metadata` (lat/lon, altim,
temp...) e `parsed` (vento, temperatura, QNH, nuvens...).

### 8.10. `GET /metar/all` e `GET /metar/stations`

Todos os METARs das 9 estações / mapa de estações por região.

### 8.11. `POST /bluesky/wind`

```bash
curl -X POST http://localhost:8000/bluesky/wind \
  -H "Content-Type: application/json" \
  -d '{"level":500,"region":"SP","date":"20260731"}'
```

Gera a matriz BlueSky em `data/matrizGrib/bluesky/` e retorna o caminho.

### 8.12. `POST /cleanup?days_old=2`

Remove dados (GRIBs, mapas e matrizes) mais antigos que `days_old` dias.

## 9. Sistema METAR

- **Fetch**: nova API JSON da aviationweather.gov
  (`https://aviationweather.gov/api/data/metar?ids={icao}&format=json&hours=2`).
  A antiga `adds/dataserver_current` foi **descontinuada** (retorna 403).
- **Parser**: cópia vendada de PythonMETAR em `server_MET/METAR/`
  (import `from server_MET.METAR import Metar`) — funciona offline.
- **Estações** (9 regiões): SP=SBGR, RJ=SBGL, CW=SBCT, PA=SBPA, BH=SBCF,
  BE=SBBE, MA=SBEG, RF=SBRF, FZ=SBFZ.

```python
from server_MET.metar_client import MetarClient
c = MetarClient()
m = c.get_metar("SBGR")            # fetch + parse
p = c.get_parsed_metar("SBPA", "METAR SBPA 212200Z 12005KT 9999 SCT030 18/12 Q1020=")  # offline
print(m["parsed"]["wind"])         # {'direction': 80, 'speed': 5, ...}
```

## 10. Scripts

```bash
./scripts/run.sh install                          # dependências + diretórios
./scripts/run.sh server                           # uvicorn server_MET.server:app --port 8000
./scripts/run.sh download [YYYYMMDD] [HH] [0p25|0p50|1p00]   # download GFS
./scripts/run.sh test                             # pytest tests/
./scripts/run.sh clean [days]                     # limpa dados antigos (default 2)
./scripts/run.sh docker-build | docker-up | docker-down
```

`scripts/download_gribs.sh` e `scripts/clean_old_gribs.sh` são alternativas
em bash puro para download em lote e limpeza.

## 11. Testes

```bash
~/envs/met/bin/python -m pytest tests/ -v     # 52 testes, offline
```

- `tests/test_core.py` — config, regiões, processamento, vento, METAR (parse
  local), matrizes, mapas;
- `tests/test_server.py` — endpoints via httpx `ASGITransport`.

Os testes de rede são tolerantes (`200`/`404`) e não dependem de conexão.

## 12. Docker

```bash
./scripts/run.sh docker-build && ./scripts/run.sh docker-up
# ou
docker compose up -d
```

`Dockerfile` (python:3.11-slim) instala `wget`, `libgfortran5` e `libgomp1`
(pygrib vem prebuilt). Volumes nomeados persistem `data/gribs`,
`data/mapasGrib` e `data/matrizGrib`; `environment/` é montado do host.

> Nota: para **mapas** em Docker é necessário Cartopy no container
> (`pip install cartopy` já está em `requirements.txt`).

## 13. Manutenção e troubleshooting

| Problema | Causa | Solução |
|---|---|---|
| `pygrib` não instala | Faltam libs do sistema | `apt install libeccodes-dev` |
| Download não executa | `wget` ausente | Instalar `wget` |
| Nenhum arquivo baixado | Ciclo GFS ainda não publicado | O NOMADS publica cada ciclo ~4h após a hora; tente outra data/análise |
| Mapas não gerados | Sem Cartopy nem Basemap | `pip install cartopy scipy` |
| `404` em mapas/matrizes | Arquivo GRIB não existe | Rodar `/gribs/download` primeiro |
| METAR vazio | ICAO inválido ou rede | Verificar código ICAO e acesso a aviationweather.gov |
| `403` em METAR | Endpoint antigo | Já corrigido — usar `api/data/metar` (v2.x) |

## 14. Changelog

- **v2.0.0** — arquitetura FastAPI consolidada; METAR com a nova API
  aviationweather (JSON); mapas com Cartopy (fallback Basemap); saídas da API
  em `data/tmp`; limpeza abrangendo gribs+mapas+matrizes; fallback de análise
  disponível; aceleração das matrizes CSV com `np.savetxt`.
