# 🌤️ Server MET v2.0

> Servidor de dados **meteorológicos** e de **poluição atmosférica**.
> Baixa dados reais de **GFS (NOAA)** e **METAR (AviationWeather)**, processa as variáveis,
> gera **mapas PNG**, armazena tudo em **SQLite + CSV** e disponibiliza via **API REST (FastAPI)**
> com um **frontend web** simples e um **dashboard estatístico**.

---

## 📋 Sumário

1. [Funcionalidades](#-funcionalidades)
2. [Arquitetura](#-arquitetura)
3. [Pré-requisitos](#-pré-requisitos)
4. [Instalação](#-instalação)
5. [Configuração (.env)](#-configuração-env)
6. [Como usar](#-como-usar)
7. [Endpoints da API](#-endpoints-da-api)
8. [Variáveis (21)](#-variáveis-21)
9. [Regiões (18)](#-regiões-18)
10. [Frontend](#-frontend)
11. [Testes e validação](#-testes-e-validação)
12. [Solução de problemas](#-solução-de-problemas)
13. [Estrutura do projeto](#-estrutura-do-projeto)

---

## ✨ Funcionalidades

| Funcionalidade | Descrição |
|----------------|-----------|
| 📥 **Ingestão de dados reais** | GRIB do GFS (endpoint *filter* da NOAA, por variável/região) + METAR ao vivo |
| ⚙️ **Processamento** | Extrai variáveis meteorológicas e de poluição por região e nível |
| 🗺️ **Mapas PNG** | Geração automática de mapas com matplotlib + Basemap |
| 💾 **Persistência** | SQLite (consultas) + CSV (exportação) + snapshots JSON de METAR |
| 🔌 **API REST** | FastAPI com documentação interativa automática em `/docs` |
| 📊 **Dashboard** | Frontend simples com estatísticas agregadas por variável/região |
| ⚙️ **Orquestração** | Shell scripts prontos para pipeline, servidor e validação |

**Stack:** Python · SQLite · Shell Script · FastAPI · matplotlib · pygrib

---

## 🏗️ Arquitetura

```
server_met/
├── core/                 # Lógica de negócio (módulos puros)
│   ├── config.py         #   Caminhos, regiões, níveis e URLs
│   ├── variables.py      #   Registro das 21 variáveis (meteo + poluição)
│   ├── regions.py        #   Classes auxiliares das 18 regiões
│   ├── persistence.py    #   Camada SQLite + CSV (dados e METAR)
│   ├── downloader.py     #   Download GFS (endpoint filter da NOAA)
│   ├── grib_reader.py    #   Leitor de arquivos GRIB (pygrib)
│   ├── processor.py      #   Extração de variáveis + estatísticas
│   ├── maps.py           #   Geração de mapas PNG
│   └── metar.py          #   Busca/decodificação de METAR ao vivo
├── api/                  # Aplicação FastAPI
│   ├── main.py           #   App, rotas e montagem do frontend
│   ├── schemas.py        #   Modelos Pydantic (contratos da API)
│   └── routes/           #   health · data · maps · metar
├── frontend/             # Interface web estática (index.html, style.css, app.js)
├── scripts/              # Automação (Python + shell)
│   ├── process_data.py   #   Pipeline GFS + METAR (configurável)
│   ├── pipeline.sh       #   Wrapper shell do pipeline
│   ├── server.sh         #   start / stop / restart / status
│   └── validate.sh       #   Validação E2E com dados reais
├── tests/                # Testes end-to-end (test_e2e.py)
├── data/                 # Runtime (ignorado pelo Git): grib/ sqlite/ csv/ metar/
├── maps/                 # Mapas PNG gerados (ignorado pelo Git)
└── README.md
```

### Fluxo dos dados

```
 NOOA GFS (filter)      ──► core/downloader ──►  data/grib/*.grb2
 AviationWeather        ──► core/metar    ──►  data/metar/*.json
                                        │
     core/processor   (extrai variáveis + calcula estatísticas)
                                        │
     core/persistence (grava em SQLite  + exporta CSV)
                                        │
     core/maps        (gera PNG em maps/)
                                        │
                    FastAPI (api/main.py)
                                        │
              Frontend + Dashboard  ◄───┘   (http://localhost:8000)
```

---

## 🔧 Pré-requisitos

- **Python 3.11+**
- **SQLite** (já embutido no Python)
- Acesso à **internet** (a ingestão baixa dados reais da NOAA)
- Dependências do sistema para `pygrib` (eccodes) e `Basemap` (proj/geos):
  ```bash
  sudo apt-get install -y gcc g++ libeccodes-dev libproj-dev libgeos-dev libsqlite3-dev curl
  ```

---

## 📦 Instalação

```bash
# 1. Criar e ativar o ambiente virtual (exemplo com o venv deste projeto)
python -m venv ~/envs/met
source ~/envs/met/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Preparar configuração
cp .env.example .env       # ajuste os valores se necessário

# 4. Verificar que os principais módulos importam
source ~/envs/met/bin/activate
PYTHONPATH=. python -c "import api.main, core.maps, core.metar, core.persistence; print('OK')"
```

---

## ⚙️ Configuração (.env)

Copie `.env.example` para `.env`. As variáveis têm valores padrão sensatos em `core/config.py`,
então o `.env` só é necessário para personalizar:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `NOAA_BASE_URL` | `https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.` | Base do GFS completo |
| `NOAA_FILTER_URL` | `https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl` | Endpoint filter (subconjuntos) |
| `NOAA_FTP_URL` | `ftp://ftp.ncep.noaa.gov/.../gfs.` | Alternativa FTP |
| `AVIATION_WEATHER_URL` | `https://aviationweather.gov/api/data/metar` | Fonte dos METAR |
| `API_HOST` | `0.0.0.0` | Endereço do servidor |
| `API_PORT` | `8000` | Porta do servidor |
| `API_WORKERS` | `4` | Workers do uvicorn |
| `LOG_LEVEL` | `INFO` | Nível de log |

> **Importante:** todos os caminhos de arquivos são calculados em `core/config.py` a partir do
> diretório do projeto (`BASE_DIR`) — não há caminhos absolutos codificados.

---

## 🚀 Como usar

### 1. Ingestão de dados (pipeline)

```bash
# Pipeline completo: baixa GFS real + METAR real, gera mapas e povoa o SQLite
bash scripts/pipeline.sh
```

Para controlar data, ciclo (análise) e regiões:

```bash
PYTHONPATH=. python scripts/process_data.py \
    --date 20260804 --analysis 00 --regions SP RJ PR
```

**Argumentos do pipeline:**

| Flag | Padrão | Descrição |
|------|--------|-----------|
| `--date` | última disponível | Data no formato `YYYYMMDD` |
| `--analysis` | detecta recente | Ciclo sinótico `00`, `06`, `12`, `18` |
| `--regions` | `SP RJ PR RS MG AM` | Códigos de região |
| `--all-variables` | — | Processa **todas** as 21 variáveis de `core/variables.py` (as que não existem no GFS são ignoradas com erro registrado) |
| `--skip-metar` | — | Não busca METAR |

> O conjunto padrão de variáveis/ níveis processado está em `DEFAULT_VARIABLES`
> em `scripts/process_data.py` (ex.: `temp` em 1000/850/500 hPa, `o3` em 500 hPa, `ps` superfície).
>
> Exemplo com todas as variáveis:
>
> ```bash
> PYTHONPATH=. python scripts/process_data.py --date 20260804 --analysis 00 --regions SP RJ PR --all-variables
> ```

### 2. Subir o servidor

```bash
bash scripts/server.sh start      # ou: stop | restart | status
```

Também é possível rodar em modo de desenvolvimento:

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Acessar

- **Frontend/Dashboard:** <http://localhost:8000/>
- **Documentação da API (Swagger):** <http://localhost:8000/docs>
- **Documentação alternativa (ReDoc):** <http://localhost:8000/redoc>

---

## 🌐 Endpoints da API

Base: `/api/v1` (exceto `/health` e `/docs`).

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Status do servidor e do banco |
| GET | `/data/variables` | Catálogo das 21 variáveis |
| GET | `/data/regions` | As 18 regiões |
| GET | `/data/dashboard` | Resumo estatístico agregado |
| GET | `/data/available` | Variáveis/regiões/datas disponíveis no banco |
| GET | `/data/` | Consulta de dados (`?variable&level&region&date&analysis&limit`) |
| GET | `/data/latest` | Registro mais recente de uma seleção |
| GET | `/data/stats` | Estatísticas (min/max/média) de uma seleção |
| GET | `/data/levels/{var}` | Níveis disponíveis para a variável |
| GET | `/data/export/csv` | Exportação em CSV |
| GET | `/maps/{var}/{region}` | Mapa PNG (opcional `?level=`, `?date=`, `?analysis=`) |
| GET | `/maps/list/{var}/{region}` | Lista os mapas disponíveis |
| GET | `/metar/stations` | Estações METAR |
| GET | `/metar/{code}` | METAR mais recente + decodificação |
| GET | `/metar/latest/all` | METAR de todas as estações |

### Exemplos com `curl`

```bash
BASE=http://localhost:8000/api/v1

# Status do servidor
curl -s http://localhost:8000/health

# Consultar temperatura no nível 1000 hPa na região SP
curl -s "$BASE/data/?variable=temp&level=1000&region=SP"

# Estatísticas da seleção
curl -s "$BASE/data/stats?variable=temp&level=850&region=SP"

# Exportar CSV
curl -s "$BASE/data/export/csv?variable=temp&level=850&region=SP" -o dados.csv

# Baixar o mapa PNG (data + análise)
curl -s "$BASE/maps/temp/SP?level=850&date=20260804&analysis=00" -o mapa.png

# Listar mapas disponíveis
curl -s "$BASE/maps/list/temp/SP"

# METAR mais recente de Guarulhos (SBGR)
curl -s "$BASE/metar/SBGR"

# Dashboard agregado
curl -s "$BASE/data/dashboard"
```

> **Dica:** para variáveis de superfície (ex.: `ps`), não use o parâmetro `level` —
> elas são gravadas com nível `0`. O frontend já gerencia isso automaticamente.

---

## 🎯 Variáveis (21)

**Meteorológicas (12):** `ps`, `prnm`, `temp`, `temps`, `nuvem`, `chuvaNaoConvec`,
`chuvaConvec`, `umidadeRel`, `u`, `v`, `uSupe`, `vSupe`

**Poluição (9):** `o3`, `total_o3`, `no2`, `so2`, `co`, `pm25`, `pm10`, `aod`, `dust`

> As variáveis **confirmadas no GFS pgrb2** (`ps`, `prnm`, `temp`, `temps`, `nuvem`,
> `umidadeRel`, `u`, `v`, `uSupe`, `vSupe`, `o3`, `total_o3`) são processáveis com dados
> reais. As demais estão registradas no catálogo (`core/variables.py`) mas **não existem**
> no produto GFS pgrb2 0p25 (confirmado via inventário `varMET` do próprio arquivo), ficando
> disponíveis assim que o dado existir na fonte.
>
> O endpoint `/data/variables` retorna o campo `available` para cada variável; o frontend
> exibe **apenas as disponíveis** — na categoria **Poluição**, apenas `o3` e `total_o3`.

Níveis isobáricos suportados: `1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10` hPa.
Níveis de altura (`uSupe`/`vSupe`): `10, 20, 30, 40, 50, 80, 100` m.

---

## 📍 Regiões (18)

`SP, RJ, AM, DF, PR, RS, MG, PA, PE, CE, SA, FOR, REC, SSA, BEL, BH, CWB, POA`

Cada região é um retângulo de coordenadas (min/max de longitude e latitude) definido
em `core/config.py` (`REGIOES`).

---

## 🖥️ Frontend

O frontend é servido pela própria API em `/` e contém:

- **Dashboard** — cartões com o total de registros, variáveis, regiões e estatísticas METAR;
  tabelas agregadas por variável e por região.
- **Mapa** — seleção de categoria (Meteorológicas/Poluição), variável, nível, região, data e
  análise; carrega o mapa PNG e mostra min/max/média da seleção; botão **CSV** exporta os dados.
- **METAR** — seleção de estação e visualização do boletim cru + decodificado.

> Os ativos estáticos são servidos sob `/static`. O `index.html` referencia
> `static/style.css` e `static/app.js` (não caminhos de raiz, o que evita 404).

---

## 🧪 Testes e validação

```bash
# Suíte de testes end-to-end (TestClient in-process, sem servidor externo)
PYTHONPATH=. pytest tests/test_e2e.py -v

# Validação completa: dependências + pipeline real + banco + mapas + testes
bash scripts/validate.sh
```

O `validate.sh` faz, nesta ordem:

1. Verifica se as dependências Python estão instaladas.
2. Executa o pipeline com dados reais (GFS região SP + METAR).
3. Confere que há registros no SQLite (GRIB e METAR) e que mapas PNG foram gerados.
4. Roda a suíte de testes E2E da API.

---

## 🛠️ Solução de problemas

| Problema | Causa provável | Solução |
|----------|----------------|---------|
| Pip falha em `pygrib`/`basemap` | Faltam libs de sistema | `sudo apt-get install -y gcc g++ libeccodes-dev libproj-dev libgeos-dev libsqlite3-dev` |
| `ModuleNotFoundError: core...` | `PYTHONPATH` não aponta para o projeto | Rode sempre com `PYTHONPATH=.` (ex.: `PYTHONPATH=. python scripts/process_data.py ...`) |
| Pipeline não encontra ciclo GFS | Data/ciclo ainda indisponível na NOAA | Use `--date` de um dia anterior ou rode mais tarde; o script tenta a data atual e a anterior |
| Mapa retorna 404 | Não há mapa gerado para var/região/nível/data | Rode o pipeline para esse conjunto; consulte `/maps/list/{var}/{region}` |
| Dados "vazios" em variáveis de poluição | Variável ainda não existe no GRIB pgrb2 | Só `o3` está confirmada; as demais ficam no catálogo até existirem |
| Porta 8000 em uso | Outro processo | `bash scripts/server.sh stop` ou troque `API_PORT` no `.env` |

---

## 📁 Estrutura do projeto

Veja a seção [Arquitetura](#-arquitetura). Resumo dos diretórios relevantes:

```
core/          Lógica de negócio (import absolutos core.*)
api/           FastAPI (import absolutos api.*)
frontend/      Interface web estática
scripts/       Automação (process_data.py, pipeline.sh, server.sh, validate.sh)
tests/         Testes end-to-end
data/          Runtime (grib/, sqlite/, csv/, metar/) — ignorado pelo Git
maps/          Mapas PNG gerados — ignorado pelo Git
```

---

## 📓 Notas finais

- `data/` e `maps/` são ignorados pelo Git (artefatos gerados em execução).
- Não há scheduler/systemd embutido: para agendamento use `cron` com
  `bash scripts/pipeline.sh` (ex.: executar a cada 6h).
- Para produção use `bash scripts/server.sh start` ou `uvicorn api.main:app`.
- A API é somente leitura; em ambiente local não exige autenticação.