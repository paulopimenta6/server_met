# Documentação do Servidor Meteorológico — MET Server

## Índice

1. [Visão Geral](#1-visão-geral)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Pré-requisitos e Instalação](#3-pré-requisitos-e-instalação)
4. [Configuração do Ambiente](#4-configuração-do-ambiente)
5. [Estrutura do Projeto](#5-estrutura-do-projeto)
6. [Módulos em Detalhe](#6-módulos-em-detalhe)
7. [API REST Completa](#7-api-rest-completa)
8. [Sistema METAR](#8-sistema-metar)
9. [Testes](#9-testes)
10. [Docker e Produção](#10-docker-e-produção)
11. [Scripts Úteis](#11-scripts-úteis)
12. [Exemplos de Uso](#12-exemplos-de-uso)
13. [Manutenção e Troubleshooting](#13-manutenção-e-troubleshooting)
14. [Referência das Variáveis GFS](#14-referência-das-variáveis-gfs)

---

## 1. Visão Geral

O **MET Server** é um sistema completo para download, processamento e visualização de dados
meteorológicos do modelo **GFS (Global Forecast System)** da **NOAA**, combinado com
observações **METAR** de aeródromos brasileiros.

### Funcionalidades Principais

- **Download automático** de dados GFS (resoluções 0.25°, 0.50°, 1.00°)
- **Extração de variáveis**: temperatura, vento (U/V), umidade, precipitação, nebulosidade
- **Geração de mapas** meteorológicos (contour, streamplot)
- **Geração de matrizes** de vento para ferramentas como BlueSky
- **Consulta METAR** com parser completo (vento, temperatura, pressão, nuvens, visibilidade)
- **API REST** com FastAPI para integração com outros sistemas
- **Limpeza automática** de arquivos antigos

---

## 2. Arquitetura do Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                         NOAA GFS NOMADS                         │
│          https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  grib_downloader.py      ───→    Arquivos .grb2/.grib2          │
│  (download filtrado por     dados/gfs/YYYYMMDD/HH/              │
│   variável + região)                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  grib_reader.py          ───→    Extrai mensagens GRIB2         │
│  (pygrib)                ───→    Arrays numpy: lats, lons,      │
│                                  valores da variável            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  data_processor.py      ───→    Mapa de variáveis              │
│  wind_processor.py      ───→    Vento: direção, velocidade     │
│                                  u/v → magnitude nautical       │
└──────────┬──────────────────────────────────┬───────────────────┘
           │                                  │
           ▼                                  ▼
┌─────────────────────────┐   ┌─────────────────────────────┐
│  map_generator.py       │   │  matrix_generator.py        │
│  (matplotlib)           │   │  CSV/TXT de vento BlueSky   │
│  → mapas PNG            │   │  → matrizes de vento        │
└─────────────────────────┘   └─────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  metar_client.py         ───→   NOAA aviationweather.gov      │
│  + PythonMETAR (parser)  ───→   Dados decodificados:          │
│                                  wind, temp, qnh, cloud, etc  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Server (server.py)                  │
│  Endpoints: /health, /variables, /regions, /gribs, /maps,     │
│             /matrices, /metar, /bluesky, /cleanup              │
│  Formato: JSON + PNG                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Fluxo de Dados Detalhado

1. **Download**: O `GribDownloader` baixa arquivos GRIB2 filtrados da NOAA NOMADS
   — a filtragem seleciona apenas as variáveis e sub-região necessárias
2. **Leitura**: O `GribReader` usa `pygrib` para abrir o arquivo e extrair
   mensagens GRIB. Cada mensagem contém uma variável em um nível de pressão
3. **Processamento**: O `DataProcessor` mapeia nomes de variáveis (ex: `TMP` → temperatura)
   e gerencia níveis de pressão, datas, horas de análise
4. **Vento**: O `WindProcessor` converte componentes U/V em magnitude e direção
   (convenção meteorológica: 0° = N, 90° = L, ângulo de onde o vento VEM)
5. **Mapas**: O `MapGenerator` gera imagens PNG usando matplotlib
   — contorno para temperatura/pressão, streamplot para vento
6. **Matrizes**: O `MatrixGenerator` exporta dados de vento em formato CSV/TXT
   compatível com o sistema BlueSky
7. **METAR**: O `MetarClient` consulta a NOAA ou aviationweather.gov,
   obtém o METAR bruto e o decodifica usando o parser PythonMETAR
8. **API**: O FastAPI expõe todas as funcionalidades via REST

---

## 3. Pré-requisitos e Instalação

### 3.1. Sistema

- **Sistema Operacional**: Linux (Ubuntu 22.04+, Debian 12+, CentOS 7+)
- **Python**: 3.11 ou superior
- **pip**: 23.0+

### 3.2. Dependências do Sistema

Bibliotecas necessárias para compilar o `pygrib`:

```bash
sudo apt update
sudo apt install -y libeccodes-dev libgrib-api-dev python3-dev build-essential
```

### 3.3. Python Dependencies

Arquivo `requirements.txt`:

```
numpy>=2.4.6
matplotlib>=3.10.1
pygrib>=2.1.8
fastapi>=0.115.0
uvicorn>=0.34.0
pydantic>=2.0.0
httpx>=0.28.0
pytest>=9.0.0
pytest-asyncio>=0.25.0
anyio>=4.0.0
netCDF4>=1.7.0        # dependência pygrib
pandas>=2.0.0
Pillow>=11.0.0
```

### 3.4. Instalação Passo a Passo

```bash
# 1. Clone/Copie o projeto
cd /caminho/para/servidor_MET

# 2. Crie ambiente virtual (recomendado)
python3 -m venv venv
source venv/bin/activate

# 3. Instale dependências
pip install --upgrade pip
pip install -r requirements.txt

# 4. Verifique a instalação do pygrib
python -c "import pygrib; print(f'pygrib {pygrib.__version__} OK')"

# 5. Verifique o sistema completo
./scripts/run.sh test
```

### 3.5. Verificação Rápida

```python
from server_MET.config import Settings
s = Settings()
print(s.dir_projeto)       # Diretório raiz do projeto
print(s.dir_gribs)         # Onde os GRIBs serão salvos
print(s.url_gfs_0p25)      # URL de download
```

---

## 4. Configuração do Ambiente

### 4.1. Arquivo `environment/path.conf`

```ini
[DIRS]
DIR_PROJETO = .
DIR_SCRIPTS = scripts
DIR_DADOS   = dados/gfs
DIR_IMAGENS = imagens
DIR_MATRIZ  = matrizes

[URL_GFS]
URL_GFS_0P25 = https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl
URL_GFS_0P50 = https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p50.pl
URL_GFS_1P00 = https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_1p00.pl

[PARAM_GFS]
RESOLUTION = 0.25
LAST_FCST_HOUR = 384
EMPTY_HOURS_AT_END_FILE = 384

[REGIOES]
REGIOES = sul,sudeste,centroeste,nordeste,norte,brasil
```

### 4.2. Como o Config é Carregado

O singleton `Settings` (em `server_MET/config.py`) lê o `path.conf` e resolve
todos os caminhos **relativos ao diretório do projeto** (onde o `path.conf` está):

```python
from server_MET.config import Settings
s = Settings()
# s.dir_projeto → /caminho/para/servidor_MET
# s.dir_gribs   → /caminho/para/servidor_MET/dados/gfs
# s.dir_imagens → /caminho/para/servidor_MET/imagens
```

### 4.3. Personalizando Diretórios

Para mudar os diretórios, edite o `path.conf`:

```ini
DIR_DADOS = /dados/gfs     # Caminho absoluto
# ou
DIR_DADOS = ../dados/gfs   # Caminho relativo
```

---

## 5. Estrutura do Projeto

```
servidor_MET/
│
├── server_MET/                    # Pacote principal do servidor
│   ├── __init__.py
│   ├── config.py                  # Singleton Settings (path.conf)
│   ├── region.py                  # Regiões predefinidas
│   ├── grib_reader.py             # Leitura de arquivos GRIB2
│   ├── grib_downloader.py         # Download GFS da NOAA
│   ├── data_processor.py          # Processamento de variáveis
│   ├── wind_processor.py          # Cálculos de vento (u/v → direção)
│   ├── map_generator.py           # Geração de mapas PNG
│   ├── matrix_generator.py        # Geração de matrizes de vento
│   ├── metar_client.py            # Cliente METAR (fetch + parser)
│   ├── models.py                  # Modelos Pydantic
│   ├── server.py                  # Servidor FastAPI
│   └── METAR/                     # Parser METAR (PythonMETAR)
│       ├── __init__.py
│       └── metar.py               # Decodificador METAR completo
│
├── tests/                         # Testes automatizados
│   ├── test_core.py               # 32 testes unitários
│   └── test_server.py             # 13 testes de API
│
├── docs/
│   └── documentation.md           # Esta documentação
│
├── scripts/
│   ├── run.sh                     # Script principal
│   ├── download_gribs.sh          # Download batch de GFS
│   └── clean_old_gribs.sh         # Limpeza de GRIBs antigos
│
├── environment/
│   └── path.conf                  # Configuração de caminhos
│
├── dados/gfs/                     # Dados GRIB baixados (auto-criado)
├── imagens/                       # Mapas gerados (auto-criado)
├── matrizes/                      # Matrizes geradas (auto-criado)
│
├── Dockerfile                     # Container Docker
├── docker-compose.yml             # Orquestração Docker
├── pyproject.toml                 # Configuração Python moderna
├── requirements.txt               # Dependências Python
├── pytest.ini                     # Configuração do pytest
├── README.md                      # Visão rápida
│
├── legacy/                        # Código original (backup)
│   ├── classes_MET/               # Classes originais
│   ├── bash/                      # Scripts bash originais
│   └── METARpy/                   # Scripts METAR originais
│       └── GoMETAR.py             # Wrapper original do METAR
│
└── METARpy/                       # Biblioteca METAR original
    ├── PythonMETAR-1.0.0.1/       # Pacote PythonMETAR (parser)
    │   └── PythonMETAR/
    │       └── metar.py           # Código do parser
    └── python-metar-master/       # Biblioteca metar alternativa
```

---

## 6. Módulos em Detalhe

### 6.1. `config.py` — Configuração Singleton

Carrega o arquivo `path.conf` e disponibiliza todos os parâmetros como
atributos de objeto. Usa o padrão **Singleton** — a mesma instância é
compartilhada por toda a aplicação.

**Atributos principais:**

| Atributo | Descrição |
|---|---|
| `dir_projeto` | Diretório raiz do projeto |
| `dir_scripts` | Diretório de scripts |
| `dir_gribs` | Diretório de dados GRIB |
| `dir_imagens` | Diretório de imagens geradas |
| `dir_matriz` | Diretório de matrizes |
| `url_gfs_0p25` | URL download GFS 0.25° |
| `url_gfs_0p50` | URL download GFS 0.50° |
| `url_gfs_1p00` | URL download GFS 1.00° |
| `resolution` | Resolução padrão |
| `last_fcst_hour` | Última hora de previsão |
| `regioes` | Lista de regiões configuradas |

**Método `ensure_dirs()`**: Cria todos os diretórios necessários
se não existirem.

### 6.2. `region.py` — Regiões

Define regiões predefinidas como bounding boxes (lon_min, lon_max, lat_min, lat_max).

**Regiões disponíveis:**

| Nome | Lon Min | Lon Max | Lat Min | Lat Max | Cobre |
|---|---|---|---|---|---|
| SP | -56° | -42° | -28° | -18° | São Paulo |
| RJ | -46° | -36° | -27° | -17° | Rio de Janeiro |
| AM | -65° | -55° | -7° | 7° | Amazonas |
| DF | -54° | -44° | -20° | -10° | Distrito Federal |
| PR | -54° | -44° | -30° | -20° | Paraná |
| RS | -56° | -46° | -34° | -24° | Rio Grande do Sul |
| MG | -48° | -38° | -24° | -14° | Minas Gerais |
| PA | -53° | -43° | -6° | 4° | Pará |
| PE | -39° | -29° | -13° | -3° | Pernambuco |
| CE | -43° | -33° | -8° | 2° | Ceará |
| SA | -100° | -20° | -60° | 25° | América do Sul |

**Formas de criar uma região:**

```python
from server_MET.region import Region

# Por nome predefinido
r = Region(name="SP")

# Por bounding box
r = Region(lon_min=-50, lon_max=-40, lat_min=-25, lat_max=-15)

# Por centro + tamanho fixo (degrees)
r = Region(center_lon=-46.63, center_lat=-23.55)
```

### 6.3. `grib_reader.py` — Leitor GRIB

Usa a biblioteca `pygrib` para abrir arquivos GRIB2 e extrair dados.

**Métodos principais:**

| Método | Descrição |
|---|---|
| `find_grib_file(date, ana, prev)` | Encontra arquivo GRIB no diretório |
| `open_grib(path)` | Abre arquivo, retorna `pygrib.open` |
| `list_variables(path)` | Lista variáveis no arquivo |
| `read_variable(path, var_name, level)` | Lê dados de uma variável |
| `read_wind_components(path, level)` | Lê U e V para cálculo de vento |
| `get_available_dates()` | Lista datas com GRIB disponível |

**Exemplo:**

```python
from server_MET.grib_reader import GribReader
reader = GribReader()
grib_file = reader.find_grib_file("20260101", "00", "06")
if grib_file:
    lats, lons, values = reader.read_variable(grib_file, "TMP", 500)
    print(f"Temperatura em 500hPa: {values.min():.1f} a {values.max():.1f} K")
```

### 6.4. `data_processor.py` — Processador de Dados

Gerencia o mapeamento entre nomes de variáveis internas e parâmetros GRIB,
além de resolução de níveis de pressão e datas.

**Mapa de Variáveis (`VAR_MAP`):**

| Chave | Nome GRIB | Tipo | Nível Padrão |
|---|---|---|---|
| `ps` | Pressão superfície | `sfc` | superfície |
| `prnm` | Pressão nível médio mar | `sfc` | superfície |
| `temp` | Temperatura | `pressure` | 500 hPa |
| `temps` | Temperatura superfície | `sfc` | superfície |
| `nuvem` | Nebulosidade | `sfc` | superfície |
| `chuvaNaoConvec` | Chuva não-convectiva | `sfc` | superfície |
| `chuvaConvec` | Chuva convectiva | `sfc` | superfície |
| `umidadeRel` | Umidade relativa | `pressure` | 500 hPa |
| `u` | Vento U (leste-oeste) | `pressure` | 500 hPa |
| `v` | Vento V (norte-sul) | `pressure` | 500 hPa |
| `uSupe` | Vento U superfície | `sfc` | superfície |
| `vSupe` | Vento V superfície | `sfc` | superfície |
| `wind` | Magnitude vento | `pressure` | 500 hPa |
| `winds` | Magnitude vento sup. | `sfc` | superfície |

**Níveis de Pressão Suportados:** 1000, 950, 900, 850, 800, 700, 500, 300, 250, 200, 100, 70, 50, 30, 20, 10, 5, 1 hPa

### 6.5. `wind_processor.py` — Processador de Vento

Converte componentes U/V em direção e velocidade meteorológica.

**Cálculos:**

| Método | Fórmula | Descrição |
|---|---|---|
| `compute_speed(u, v)` | `sqrt(u² + v²)` | Velocidade em m/s |
| `compute_speed_knot(u, v)` | `sqrt(u² + v²) * 1.94384` | Velocidade em nós |
| `compute_direction_met(u, v)` | `(270 - atan2(v, u) * 180/π) % 360` | Direção (0°=N, de onde vem) |
| `pressure_to_altitude(p)` | `44330 * (1 - (p/1013.25)^(1/5.255))` | Altitude em metros |
| `get_near_surface_levels()` | [20, 30, 40, 50, 80] | Níveis próximos à superfície |

### 6.6. `metar_client.py` — Cliente METAR

**Funcionalidades:**

1. **Fetch bruto** da NOAA aviationweather.gov (XML → raw_text)
2. **Parser completo** usando a biblioteca PythonMETAR (integrada em `server_MET/METAR/`)
3. **Parsing local** sem consulta à rede (passando texto METAR diretamente)

**Métodos do `MetarClient`:**

| Método | Retorno | Descrição |
|---|---|---|
| `get_raw_metar(icao)` | `str` | METAR bruto da NOAA |
| `get_parsed_metar(icao, raw_text)` | `dict` | METAR decodificado (sem rede) |
| `get_metar(icao)` | `dict` | METAR completo (raw + parsed) |
| `get_metar_light(icao)` | `str` | METAR via PythonMETAR (com rede) |
| `get_metar_for_region(region)` | `dict` | METAR da região |
| `get_all_metars()` | `list[dict]` | METAR de todas as regiões |
| `metar_to_json(icao)` | `str` | JSON formatado do METAR |

**Uso:**

```python
from server_MET.metar_client import MetarClient

client = MetarClient()

# 1. Apenas METAR bruto
raw = client.get_raw_metar("SBPA")

# 2. Parse local (sem rede)
parsed = client.get_parsed_metar("SBPA", "METAR SBPA 212200Z 12005KT 9999 SCT030 18/12 Q1020=")

# 3. Completo (fetch + parse)
metar = client.get_metar("SBGR")
print(metar["raw_metar"])      # Texto METAR original
print(metar["parsed"]["wind"]) # {'direction': 120, 'speed': 5, 'gust': None, 'variation': None}
print(metar["parsed"]["temperatures"])  # {'temperature': 18, 'dewpoint': 12}
print(metar["parsed"]["qnh"])  # 1020
```

**Formato do METAR decodificado:**

```json
{
  "station": "SBGR",
  "station_code": "SBGR",
  "timestamp": "2026-07-21T22:00:00",
  "raw_metar": "METAR SBGR 212200Z 12005KT 9999 SCT030 18/12 Q1020=",
  "parsed": {
    "station_code": "SBGR",
    "wind": {
      "direction": 120,
      "speed": 5,
      "gust": null,
      "variation": null
    },
    "visibility": 9999,
    "weather": null,
    "cloud": [
      {
        "code": "SCT",
        "meaning": "Scattered",
        "altitude": 3000,
        "presenceCB": false,
        "presenceTCU": false
      }
    ],
    "temperatures": {
      "temperature": 18,
      "dewpoint": 12
    },
    "qnh": 1020,
    "auto": false,
    "changements": null
  }
}
```

**Estações METAR disponíveis:**

| Região | Código ICAO | Aeroporto |
|---|---|---|
| SP | SBGR | Guarulhos |
| RJ | SBGL | Galeão |
| CW | SBCT | Curitiba |
| PA | SBPA | Porto Alegre |
| BH | SBCF | Belo Horizonte |
| BE | SBBE | Belém |
| MA | SBEG | Manaus |
| RF | SBRF | Recife |
| FZ | SBFZ | Fortaleza |

### 6.7. `map_generator.py` — Gerador de Mapas

Gera imagens PNG de variáveis meteorológicas usando matplotlib.

**Tipos de mapa:**

- **Contour**: Temperatura, pressão, umidade (linhas de nível)
- **Streamplot**: Vento (linhas de fluxo)

**Exemplo:**

```python
from server_MET.map_generator import MapGenerator
from server_MET.region import Region

gen = MapGenerator()
region = Region(name="SP")
files = gen.generate(
    var_name="temp",
    region=region,
    level=500,
    date_str="20260101",
    analysis="00",
    output_dir="/tmp/mapas"
)
print(files)  # Lista de caminhos PNG gerados
```

### 6.8. `matrix_generator.py` — Gerador de Matrizes

Exporta dados de vento em formato compatível com o sistema BlueSky
(ferramenta de simulação de dispersão de fumaça).

**Formatos de saída:** CSV, TXT, JSON

**Nomenclatura de arquivos:**
```
vYYYYMMDDHH_ICAO_LEVEL_region_FTYPE.extension
```

### 6.9. `grib_downloader.py` — Downloader GFS

Faz download de dados GFS filtrados da NOAA NOMADS.

**Filtros aplicados:**
- Sub-região (bounding box da América do Sul)
- Variáveis selecionadas (temperatura, vento, umidade, etc.)
- Níveis de pressão selecionados

### 6.10. `models.py` — Modelos Pydantic

Define os schemas de validação para a API:

| Modelo | Uso |
|---|---|
| `MetVariable` | Enum de variáveis meteorológicas |
| `RegionName` | Enum de regiões |
| `OutputFormat` | Enum: csv, json, png |
| `GribRequest` | Request para dados GRIB (variável, nível, região, data) |
| `MetarRequest` | Request para METAR (icao_code, região) |
| `MapRequest` | Request para mapas (herda GribRequest) |
| `WindRequest` | Request para vento BlueSky |
| `HealthResponse` | Response do health check |

---

## 7. API REST Completa

### 7.1. `GET /health`

Verifica se o servidor está operacional.

**Resposta:**
```json
{
  "status": "ok",
  "version": "2.0.0",
  "grib_files_available": false,
  "uptime": 1234.56
}
```

**Campos:**
- `status`: "ok" se o servidor está rodando
- `version`: Versão do servidor
- `grib_files_available`: true se existem arquivos GRIB no diretório
- `uptime`: Segundos desde o início do servidor

### 7.2. `GET /variables`

Lista todas as variáveis meteorológicas disponíveis.

**Resposta:**
```json
{
  "variables": [
    {"key": "ps", "name": "Pressure of surface", "level_type": "sfc"},
    {"key": "temp", "name": "Temperature", "level_type": "pressure"},
    {"key": "uSupe", "name": "U-Component of wind (surface)", "level_type": "sfc"},
    {"key": "vSupe", "name": "V-Component of wind (surface)", "level_type": "sfc"}
  ]
}
```

### 7.3. `GET /regions`

Lista regiões predefinidas com bounding boxes.

**Resposta:**
```json
{
  "regions": [
    {"name": "SP", "bounds": [-56.0, -42.0, -28.0, -18.0]},
    {"name": "RJ", "bounds": [-46.0, -36.0, -27.0, -17.0]}
  ]
}
```

Cada bounds é `[lon_min, lon_max, lat_min, lat_max]`.

### 7.4. `GET /gribs/list`

Lista arquivos GRIB disponíveis.

**Parâmetros query:**
- `date` (opcional): Filtra por data (YYYYMMDD)

**Resposta:**
```json
{
  "gribs": ["20260101/00/gfs_0p25_00.grb2", "20260101/06/gfs_0p25_06.grb2"],
  "count": 2
}
```

### 7.5. `POST /gribs/download`

Inicia download de GFS em background.

**Body:**
```json
{
  "date": "20260101",
  "analysis": "00"
}
```

**Resposta:**
```json
{
  "status": "download_started",
  "date": "20260101",
  "analysis": "00"
}
```

### 7.6. `POST /gribs/info`

Obtém informações das variáveis em um arquivo GRIB.

**Body:**
```json
{
  "variable": "temp",
  "level": 500,
  "region": "SP",
  "date": "20260101"
}
```

### 7.7. `POST /maps/generate`

Gera mapas meteorológicos.

**Body:**
```json
{
  "variable": "temp",
  "level": 500,
  "region": "SP",
  "date": "20260101",
  "analysis": "00"
}
```

**Resposta:** PNG do mapa (FileResponse).

### 7.8. `POST /matrices/generate`

Gera matrizes de dados.

**Body:**
```json
{
  "variable": "wind",
  "level": 500,
  "region": "SP",
  "date": "20260101",
  "analysis": "00",
  "output_format": "csv"
}
```

### 7.9. `POST /metar/fetch`

Obtém METAR decodificado.

**Body (por região):**
```json
{"region": "SP"}
```

**Body (por ICAO):**
```json
{"icao_code": "SBGR"}
```

**Resposta:**
```json
{
  "station": "SBGR",
  "timestamp": "2026-07-21T22:00:00",
  "raw_metar": "METAR SBGR 212200Z 12005KT 9999 SCT030 18/12 Q1020=",
  "parsed": {
    "wind": {"direction": 120, "speed": 5, "gust": null, "variation": null},
    "temperatures": {"temperature": 18, "dewpoint": 12},
    "qnh": 1020,
    "visibility": 9999,
    "cloud": [{"code": "SCT", "meaning": "Scattered", "altitude": 3000}]
  }
}
```

### 7.10. `GET /metar/all`

Obtém METAR de todas as regiões.

### 7.11. `GET /metar/stations`

Lista estações METAR disponíveis.

**Resposta:**
```json
{
  "stations": {
    "SP": "SBGR",
    "RJ": "SBGL",
    "CW": "SBCT",
    "PA": "SBPA",
    "BH": "SBCF",
    "BE": "SBBE",
    "MA": "SBEG",
    "RF": "SBRF",
    "FZ": "SBFZ"
  }
}
```

### 7.12. `POST /bluesky/wind`

Gera arquivo de vento para BlueSky.

**Body:**
```json
{
  "level": 500,
  "region": "SP"
}
```

### 7.13. `POST /cleanup`

Remove arquivos antigos.

**Parâmetros query:**
- `days_old` (int, default=2): Remove arquivos mais velhos que N dias

**Resposta:**
```json
{
  "removed_files": ["/path/to/old/file.grb2"],
  "days_old": 2
}
```

---

## 8. Sistema METAR

### 8.1. Arquitetura do METAR

```
                    ┌──────────────────────────┐
                    │  aviationweather.gov      │
                    │  (NOAA ADD)               │
                    └────────────┬─────────────┘
                                 │ XML via HTTP
                                 ▼
┌──────────────────────────────────────────────────────┐
│  metar_client.py                                      │
│                                                        │
│  1. fetch_raw_xml(icao)     → XML da NOAA             │
│  2. extract_raw_text_from_xml() → raw METAR string    │
│  3. get_parsed_metar()      → dicionário decodificado │
│  4. get_metar()             → raw + parsed completo   │
└─────────────────────┬────────────────────────────────┘
                      │ PythonMETAR.metar.Metar
                      ▼
┌──────────────────────────────────────────────────────┐
│  server_MET/METAR/metar.py (PythonMETAR library)     │
│                                                        │
│  Metar(icao_code, text="METAR ...")                   │
│    .wind        → {'direction': 120, 'speed': 5}      │
│    .temperatures → {'temperature': 18, 'dewpoint': 12}│
│    .qnh         → 1020                                 │
│    .visibility  → 9999                                 │
│    .cloud       → tuple of cloud layers               │
│    .weather     → precipitação, fenômenos             │
│    .auto        → True/False (estação automática?)    │
│    .getAll()    → dict com todas as propriedades      │
└──────────────────────────────────────────────────────┘
```

### 8.2. Biblioteca PythonMETAR

**Origem:** Matthieu BOUCHET (https://github.com/MatthieuBOUCHET/PythonMETAR)

**Localização no projeto:** `server_MET/METAR/metar.py` (cópia integrada)

**Capacidades (campos decodificados):**

| Campo | Tipo | Exemplo |
|---|---|---|
| `airport` | string | "SBGR" |
| `metar` | string | "METAR SBGR 212200Z 12005KT 9999..." |
| `data_date` | string | "2026/07/21 22:00" |
| `date_time` | tuple | ("21","22","00") |
| `auto` | bool | False |
| `wind` | dict | {direction, speed, gust, variation} |
| `visibility` | int | 9999 |
| `rvr` | tuple | (runway, visibility) |
| `weather` | dict | {intensity, prefix, weather} |
| `cloud` | tuple | [{code, meaning, altitude, okta}] |
| `temperatures` | dict | {temperature, dewpoint} |
| `qnh` | int/float | 1013 (hPa) ou 29.92 (inHg) |
| `changements` | dict | {TEMPO, BECMG, NOSIG} |
| `vmc` | dict | {controlled, uncontrolled} |
| `properties` | dict | Todos os acima em um dict |

### 8.3. Exemplos de Parsing METAR

**Exemplo 1: Vento com direção variável**

```python
>>> client = MetarClient()
>>> raw = "METAR SBGL 212200Z VRB03KT CAVOK 22/15 Q1015="
>>> p = client.get_parsed_metar("SBGL", raw)
>>> p["wind"]
{'direction': 'VRB', 'speed': 3, 'gust': None, 'variation': None}
```

**Exemplo 2: Com rajada e variação**

```python
>>> raw = "METAR SBCT 211800Z 33015G25KT 320V040 9999 SCT020 19/14 Q1018="
>>> p = client.get_parsed_metar("SBCT", raw)
>>> p["wind"]
{'direction': 330, 'speed': 15, 'gust': 25, 'variation': (320, 40)}
```

**Exemplo 3: Fenômenos e nuvens**

```python
>>> raw = "METAR SBGR 211900Z 18008KT 5000 -RA BKN012 OVC020 17/16 Q1019="
>>> p = client.get_parsed_metar("SBGR", raw)
>>> p["weather"]
{'intensity': (False,), 'prefix': None, 'weather': ('Rain',)}
>>> p["cloud"]
({'code': 'BKN', 'meaning': 'Broken', 'altitude': 1200},
 {'code': 'OVC', 'meaning': 'Overcast', 'altitude': 2000})
```

### 8.4. Como Usar o METAR via API

```bash
# Por região
curl -X POST http://localhost:8000/metar/fetch \
  -H "Content-Type: application/json" \
  -d '{"region": "SP"}'

# Por código ICAO
curl -X POST http://localhost:8000/metar/fetch \
  -H "Content-Type: application/json" \
  -d '{"icao_code": "SBPA"}'

# Todas as estações
curl http://localhost:8000/metar/all

# Listar estações
curl http://localhost:8000/metar/stations
```

---

## 9. Testes

### 9.1. Executando Testes

```bash
# Todos os testes (45 testes)
python -m pytest tests/ -v

# Apenas testes unitários
python -m pytest tests/test_core.py -v

# Apenas testes de API
python -m pytest tests/test_server.py -v

# Com cobertura
python -m pytest tests/ --cov=server_MET --cov-report=term
```

### 9.2. Testes Unitários (32 testes)

| Classe de Teste | Testes | Descrição |
|---|---|---|
| `TestConfig` | 4 | Singleton, diretórios, URLs, ensure_dirs |
| `TestRegion` | 6 | Regiões predefinidas, bbox, centro, validação |
| `TestDataProcessor` | 7 | VAR_MAP, níveis, resolução, datas |
| `TestWindProcessor` | 5 | Velocidade, direção, altitude, níveis |
| `TestMetarClient` | 4 | Aeródromos, URL, parsing local (2) |
| `TestMatrixGenerator` | 2 | Nomenclatura de arquivos |
| `TestServerHealth` | 2 | Modelos HealthResponse, GribRequest |

### 9.3. Testes de API (13 testes)

| Teste | Descrição |
|---|---|
| `test_health_endpoint` | GET /health retorna status ok |
| `test_variables_endpoint` | GET /variables lista variáveis |
| `test_regions_endpoint` | GET /regions lista regiões |
| `test_gribs_list_endpoint` | GET /gribs/list funciona |
| `test_metar_stations` | GET /metar/stations retorna estações |
| `test_grib_info_no_file` | POST /gribs/info com data inválida → 404 |
| `test_generate_map_missing_grib` | POST /maps/generate sem GRIB |
| `test_generate_matrix_missing_grib` | POST /matrices/generate sem GRIB |
| `test_metar_fetch_invalid` | POST /metar/fetch ICAO inválido |
| `test_metar_fetch_by_region` | POST /metar/fetch por região |
| `test_bluesky_wind_missing_grib` | POST /bluesky/wind sem GRIB |
| `test_cleanup_endpoint` | POST /cleanup funciona |
| `test_health_response_model` | Validação do modelo HealthResponse |

---

## 10. Docker e Produção

### 10.1. Dockerfile

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y libeccodes-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8000
CMD ["uvicorn", "server_MET.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 10.2. Build e Execução

```bash
# Build
docker build -t met-server .

# Executar com docker-compose
docker-compose up -d

# Executar manualmente
docker run -d --name met-server -p 8000:8000 \
  -v $(pwd):/app \
  met-server

# Ver logs
docker logs -f met-server
```

### 10.3. docker-compose.yml

```yaml
services:
  servidor-met:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    environment:
      - TZ=America/Sao_Paulo
```

### 10.4. Produção (gunicorn + systemd)

**Service systemd:**

```ini
[Unit]
Description=MET Weather Server
After=network.target

[Service]
Type=simple
User=met
WorkingDirectory=/opt/servidor_MET
ExecStart=/opt/servidor_MET/venv/bin/gunicorn \
  -k uvicorn.workers.UvicornWorker \
  -w 4 \
  server_MET.server:app \
  --bind 0.0.0.0:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 10.5. Proxy Reverso (Nginx)

```nginx
server {
    listen 80;
    server_name met.exemplo.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /opt/servidor_MET/imagens/;
    }
}
```

---

## 11. Scripts Úteis

### 11.1. `scripts/run.sh` — Script Principal

```bash
./scripts/run.sh install    # Instala dependências
./scripts/run.sh dev        # Inicia em modo desenvolvimento (reload)
./scripts/run.sh test       # Executa testes
./scripts/run.sh server     # Inicia em produção
./scripts/run.sh all        # Install + test + server
```

### 11.2. `scripts/download_gribs.sh` — Download Batch

```bash
# Download para data/hora específica
./scripts/download_gribs.sh 20260101 00

# Especificar resolução
./scripts/download_gribs.sh 20260101 00 0.25

# Últimos 7 dias
./scripts/download_gribs.sh -7
```

### 11.3. `scripts/clean_old_gribs.sh` — Limpeza

```bash
# Remove GRIBs mais velhos que 30 dias
./scripts/clean_old_gribs.sh -d 30

# Remove GRIBs mais velhos que 7 dias (padrão)
./scripts/clean_old_gribs.sh
```

---

## 12. Exemplos de Uso

### 12.1. Iniciar o Servidor

```bash
# Desenvolvimento (com auto-reload)
cd /caminho/para/servidor_MET
source venv/bin/activate
uvicorn server_MET.server:app --host 0.0.0.0 --port 8000 --reload

# Ou usando o script
./scripts/run.sh dev
```

### 12.2. Health Check

```bash
curl http://localhost:8000/health
```

### 12.3. Listar Variáveis

```bash
curl http://localhost:8000/variables | python3 -m json.tool
```

### 12.4. Ver METAR de São Paulo

```bash
curl -X POST http://localhost:8000/metar/fetch \
  -H "Content-Type: application/json" \
  -d '{"region": "SP"}' | python3 -m json.tool
```

### 12.5. METAR Decodificado (parser local, sem rede)

```python
from server_MET.metar_client import MetarClient

client = MetarClient()
raw = "METAR SBPA 212200Z 12005KT 9999 SCT030 18/12 Q1020="
metar = client.get_metar("SBPA")  # Faz fetch da NOAA
# OU apenas parse local:
parsed = client.get_parsed_metar("SBPA", raw)
print("Vento:", parsed["wind"]["direction"], "° a", parsed["wind"]["speed"], "kt")
print("Temp:", parsed["temperatures"]["temperature"], "°C")
print("QNH:", parsed["qnh"], "hPa")
```

### 12.6. Listar Arquivos GRIB

```bash
curl http://localhost:8000/gribs/list
```

### 12.7. Gerar Mapa

```bash
curl -X POST http://localhost:8000/maps/generate \
  -H "Content-Type: application/json" \
  -d '{"variable":"temp","level":850,"region":"SP"}' \
  --output mapa.png
```

### 12.8. Limpeza

```bash
curl -X POST "http://localhost:8000/cleanup?days_old=30"
```

---

## 13. Manutenção e Troubleshooting

### 13.1. Logs

O servidor loga no stderr com formato:
```
2026-07-21 22:33:33 [INFO] server_MET.server: HTTP Request: GET /health "200 OK"
```

Para capturar logs em arquivo:
```bash
uvicorn server_MET.server:app --host 0.0.0.0 --port 8000 2>> /var/log/met-server.log
```

### 13.2. Problemas Comuns

| Problema | Causa | Solução |
|---|---|---|
| `pygrib` não instala | Faltam libs do sistema | `apt install libeccodes-dev` |
| `No GRIB files found` | Download não realizado | Executar `POST /gribs/download` ou `scripts/download_gribs.sh` |
| `Basemap not installed` | Cartopy/Basemap ausente | Instalar: `pip install cartopy` (mapas continuam funcionando sem) |
| METAR não retorna dados | Estação ICAO inválida ou rede | Verificar código ICAO, conexão com aviationweather.gov |
| `404` em `/maps/generate` | Arquivo GRIB não existe | Fazer download primeiro |
| Permissão negada | Diretórios sem write | Verificar `ensure_dirs()` ou criar manualmente |

### 13.3. Cron para Download Automático

```bash
# /etc/cron.d/met-server
# Download GFS a cada 6 horas
0 */6 * * * met /opt/servidor_MET/scripts/download_gribs.sh $(date +\%Y\%m\%d) $(date +\%H | cut -c1)0 0.25

# Limpeza semanal
0 3 * * 0 met /opt/servidor_MET/scripts/clean_old_gribs.sh -d 14
```

---

## 14. Referência das Variáveis GFS

### Mapeamento Nomes GRIB → Variáveis Internas

| Nome GRIB | Abrev. | Descrição | Unidades |
|---|---|---|---|
| `Pressure surface` | PRMSL | Pressão ao nível médio do mar | Pa |
| `Pressure` | PRES | Pressão atmosférica | Pa |
| `Temperature` | TMP | Temperatura | K |
| `U-Component of wind` | UGRD | Vento componente U | m/s |
| `V-Component of wind` | VGRD | Vento componente V | m/s |
| `Relative humidity` | RH | Umidade relativa | % |
| `Total cloud cover` | TCDC | Nebulosidade total | % |
| `Total precipitation` | APCP | Precipitação total | kg/m² |

### Chaves do Sistema (server_MET/data_processor.py)

| Chave | Nome para Usuário | Tipo | Nível Padrão |
|---|---|---|---|
| `ps` | Pressão superfície | sfc | - |
| `prnm` | Pressão nível médio mar | sfc | - |
| `temp` | Temperatura | pressure | 500 |
| `temps` | Temperatura superfície | sfc | - |
| `nuvem` | Nebulosidade | sfc | - |
| `chuvaNaoConvec` | Chuva não-convectiva | sfc | - |
| `chuvaConvec` | Chuva convectiva | sfc | - |
| `umidadeRel` | Umidade relativa | pressure | 500 |
| `u` | Vento U | pressure | 500 |
| `v` | Vento V | pressure | 500 |
| `uSupe` | Vento U superfície | sfc | - |
| `vSupe` | Vento V superfície | sfc | - |
| `wind` | Vento magnitude | pressure | 500 |
| `winds` | Vento magnitude sup. | sfc | - |
