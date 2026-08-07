# 🌤️ Server MET v2.0

> Servidor de dados **meteorológicos** e de **poluição atmosférica** com dados reais.
> Baixa previsões do **GFS (NOAA)**, boletins **METAR** ao vivo, gera **mapas PNG**,
> armazena tudo em **SQLite + CSV** e serve via **API REST (FastAPI)** com um **dashboard web**.

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white&style=flat-square">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white&style=flat-square">
  <img alt="GFS" src="https://img.shields.io/badge/GFS-NOAA-blue?style=flat-square">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-003B57?logo=sqlite&logoColor=white&style=flat-square">
  <img alt="METAR" src="https://img.shields.io/badge/METAR-AviationWeather-yellowgreen?style=flat-square">
  <br>
  <img alt="Visitas" src="https://visitor-badge.laobi.icu/badge?page_id=paulopimenta6.server_met">
</p>

---

## 📖 Sumário

1. [O que é o Server MET?](#-o-que-é-o-server-met)
2. [Como o sistema funciona](#-como-o-sistema-funciona)
3. [Funcionalidades](#-funcionalidades)
4. [Pré-requisitos](#-pré-requisitos)
5. [Tutorial passo a passo](#-tutorial-passo-a-passo-primeira-vez)
6. [Configuração (.env)](#-configuração-env)
7. [O pipeline em detalhes](#-o-pipeline-em-detalhes)
8. [Entendendo os dados](#-entendendo-os-dados)
9. [Onde os dados ficam armazenados](#-onde-os-dados-ficam-armazenados)
10. [A API REST](#-a-api-rest)
11. [O frontend e o dashboard](#-o-frontend-e-o-dashboard)
12. [Docker (opcional)](#-docker-opcional)
13. [Testes e validação](#-testes-e-validação)
14. [Estrutura do projeto](#-estrutura-do-projeto)
15. [Solução de problemas](#-solução-de-problemas)
16. [Dúvidas frequentes (FAQ)](#-dúvidas-frequentes-faq)

---

## 🌍 O que é o Server MET?

O Server MET é um **servidor completo de dados meteorológicos e de poluição do ar**.
Ele faz sozinho (quase) todo o trabalho:

1. **Baixa previsões reais** do modelo GFS da NOAA (temperatura, umidade, vento, chuva, nuvens, ozônio...)
   já recortadas por região e variável;
2. **Busca boletins METAR ao vivo** das principais estações brasileiras (condições atuais de aeroportos);
3. **Processa** esses dados em estatísticas (mínimo, máximo, média);
4. **Gera mapas PNG** com a distribuição espacial de cada variável;
5. **Salva tudo** em um banco SQLite (e exporta em CSV);
6. **Entrega** os dados e mapas por meio de uma **API REST** e um **frontend** com dashboard.

> 💡 **Em uma frase:** digite um comando, e o Server MET baixa previsões do tempo reais,
> gera mapas do Brasil e deixa tudo pronto para consultar na web ou via API.

---

## 🧭 Como o sistema funciona

Pense no Server MET como uma **pequena fábrica de previsões do tempo**. Ela trabalha em
4 setores, um depois do outro:

**1. Ingestão — os entregadores buscam a matéria-prima.**
O pipeline vai até as fontes reais e traz os dados: previsões do modelo GFS da NOAA
(arquivos GRIB, já recortados por região e variável) e boletins METAR ao vivo da
AviationWeather. Os arquivos crus ficam guardados em `data/grib/` e `data/metar/`.

**2. Processamento — a cozinha transforma os dados crus.**
O `core/processor.py` lê cada arquivo, recorta a região pedida e calcula o que importa:
o mínimo, o máximo e a média de cada variável.

**3. Armazenamento — o almoxarifado organiza tudo.**
Os resultados viram registros no banco **SQLite**, exportações **CSV** e **mapas PNG** na
pasta `maps/`.

**4. Exposição — o balcão de atendimento.**
O **FastAPI** serve tudo para o mundo: o frontend com dashboard em `http://localhost:8000`,
a API REST (base `/api/v1`) e a documentação interativa em `/docs`.

Em uma linha, o caminho dos dados é:

```text
NOAA GFS -> downloader -> processor -> SQLite / CSV / Mapas -> FastAPI -> Frontend
AviationWeather -> metar -> SQLite -> FastAPI -> Frontend
```

A tabela abaixo resume cada etapa:

### Passo a passo, em palavras simples

| Etapa | O que acontece | Onde |
|-------|----------------|------|
| ① **Ingestão** | O `downloader` pede à NOAA apenas a variável, o nível e a região que você quer (arquivos GRIB pequenos, ~1 MB). Em paralelo, o `metar` consulta os boletins ao vivo. | `core/downloader.py`, `core/metar.py` |
| ② **Processamento** | O `processor` lê cada GRIB, recorta a região, calcula mínimo/máximo/média e monta a matriz de valores. | `core/grib_reader.py`, `core/processor.py` |
| ③ **Armazenamento** | A `persistence` grava os resultados no SQLite e exporta CSV. O `maps` gera o PNG da região. | `core/persistence.py`, `core/maps.py` |
| ④ **Exposição** | A API FastAPI serve consultas, estatísticas, CSVs e mapas. O frontend consome a API e mostra o dashboard. | `api/main.py`, `frontend/` |

### 🤖 Como o sistema adquire os dados automaticamente

#### Dados GRIB (previsões do GFS)

Para cada combinação **data × análise × previsão × variável × nível × região**, o pipeline
chama `fetch_filtered_grib()` de `core/downloader.py`, que monta uma URL para o **endpoint
filter** da NOAA pedindo **apenas** aquele recorte:

```text
https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl?file=gfs.t00z.pgrb2.0p25.f000&dir=/gfs.20260807/00/atmos&var_TMP=on&lev_1000_mb=on&leftlon=-56&rightlon=-42&toplat=-18&bottomlat=-28
```

Os parâmetros são preenchidos automaticamente a partir do catálogo `NOAA_FILTER_VARS`
(em `core/downloader.py`), que mapeia cada código interno ao nome GRIB (ex.: `temp` → `TMP`,
`umidadeRel` → `RH`, `u`/`v` → `UGRD`/`VGRD`, `o3` → `O3MR`, `total_o3` → `TOZNE`,
`precipRate` → `PRATE`, `chuvaNaoConvec` → `APCP`, `categChuva` → `CRAIN`,
`nuvemMistura` → `CLWMR`) e ao tipo de nível (que define o seletor `lev_*_mb=on`,
`lev_surface`, `lev_mean_sea_level` ou `lev_*_m_above_ground`; o `total_o3` não usa seletor de
nível). As variáveis derivadas `vento`/`ventoSup` não têm entrada no filter — o pipeline baixa
as componentes `u`/`v` e calcula a magnitude localmente.

Antes de baixar, o pipeline **verifica se o ciclo existe** na NOAA (requisição `HEAD` ao arquivo)
— ciclos indisponíveis são pulados com aviso. Se o arquivo já estiver em
`data/grib/<data>/<análise>/`, ele é **reutilizado** (o pipeline é idempotente, ideal para
agendamentos). Cada GRIB baixado segue para `core/grib_reader.py` → `core/processor.py`
(recorte da região + estatísticas) → SQLite/CSV → mapa PNG.

#### Boletins METAR (condições atuais)

No fim do pipeline, `core/metar.py` (`fetch_and_store()`) consulta a **AviationWeather** com
todos os códigos ICAO do registro local `DEFAULT_STATIONS`:

```text
https://aviationweather.gov/api/data/metar?ids=SBGR,SBGL,SBBR,...&format=json
```

Cada boletim JSON é então processado automaticamente:

1. **Decodificado** para um resumo legível (`_decoded`): temperatura, ponto de orvalho, vento,
   visibilidade, QNH, nuvens e categoria de voo;
2. **Corrigido** quanto ao estado (a API às vezes devolve o estado errado, ex.: SBGR como "PR"
   — o registro local `DEFAULT_STATIONS` corrige para "SP");
3. **Persistido** no SQLite (`save_metar_report` + `upsert_station`);
4. **Snapshotted** como JSON em `data/metar/<CODIGO>/`.

Passe `--skip-metar` no pipeline se não quiser essa etapa.

---

## ✨ Funcionalidades

| Funcionalidade | Descrição |
|----------------|-----------|
| 📥 **Ingestão de dados reais** | GFS (NOAA) por variável/região + METAR ao vivo |
| 🌬️ **Vento resultante** | `vento`/`ventoSup` calculados a partir das componentes `u`/`v` do GFS |
| 🌧️ **Precipitação** | Taxa de chuva, precipitação acumulada e chuva categórica |
| ☁️ **Nuvens** | Cobertura total (`nuvem`) e razão de mistura de nuvens (`nuvemMistura`) |
| 🗺️ **Mapas PNG** | Mapas do Brasil com a distribuição espacial de cada variável |
| 🧮 **Estatísticas** | Mínimo, máximo e média por variável/região/nível |
| 💾 **Persistência** | SQLite para consultas + CSV para exportação + snapshots JSON de METAR |
| 🔌 **API REST** | FastAPI com documentação interativa automática em `/docs` |
| 📊 **Dashboard web** | Frontend simples com cartões, mapas, METAR e exportação CSV |
| ⚙️ **Orquestração** | Scripts prontos: pipeline, servidor e validação (e Docker opcional) |

**Stack:** Python · FastAPI · SQLite · matplotlib + Basemap · pygrib · Shell Script

---

## 🔧 Pré-requisitos

- **Python 3.11+** e `pip`
- **Internet** — a ingestão baixa dados reais da NOAA e da AviationWeather
- **SQLite** — já embutido no Python, não precisa instalar nada

Instale as bibliotecas de sistema necessárias para o `pygrib` (eccodes) e o `Basemap` (proj/geos):

```bash
sudo apt-get install -y gcc g++ libeccodes-dev libproj-dev libgeos-dev libsqlite3-dev curl
```

> 🐧 Se você usa Windows ou macOS, o caminho é usar o **Docker** (veja a seção [Docker](#-docker-opcional)).

---

## 🚀 Tutorial passo a passo (primeira vez)

Siga na ordem. No fim você terá um servidor rodando com dados reais.

### Passo 1 — Crie e ative o ambiente virtual

```bash
python -m venv ~/envs/met
source ~/envs/met/bin/activate
```

### Passo 2 — Instale as dependências

```bash
pip install -r requirements.txt
```

### Passo 3 — Prepare a configuração

```bash
cp .env.example .env
```

O arquivo `.env` já vem com valores padrão sensatos — você só precisa editá-lo se quiser mudar portas, URLs ou o banco.

### Passo 4 — Verifique se tudo importa

```bash
PYTHONPATH=. python -c "import api.main, core.maps, core.metar, core.persistence; print('OK')"
```

> ⚠️ **Importante:** os scripts usam imports absolutos (`core.*`, `api.*`).
> **Sempre** rode com `PYTHONPATH=.` no comando.

### Passo 5 — Rode o pipeline (dados reais)

A primeira vez, use um escopo **pequeno** para não bombardear a NOAA:

```bash
PYTHONPATH=. python scripts/process_data.py --date 20260807 --analysis 00 --forecast 00 --regions SP RJ
```

Esse comando baixa o ciclo das 00Z de 07/08/2026 para SP e RJ, processa as variáveis padrão,
gera os mapas e ainda busca os METAR ao vivo.

> 💡 Quando quiser rodar tudo (todas as análises e previsões), use o atalho:
>
> ```bash
> bash scripts/pipeline.sh
> ```
>
> ⚠️ Atenção: o escopo padrão é grande (4 análises × 4 previsões × variáveis × regiões = **centenas** de downloads).

### Passo 6 — Suba o servidor

```bash
bash scripts/server.sh start        # ou: stop | restart | status
```

Ou, em modo de desenvolvimento (com reload automático):

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### Passo 7 — Explore!

Abra no navegador:

| O quê | Endereço |
|-------|----------|
| 🖥️ **Frontend + Dashboard** | <http://localhost:8000/> |
| 📘 **Documentação da API (Swagger)** | <http://localhost:8000/docs> |
| 📑 **Documentação alternativa (ReDoc)** | <http://localhost:8000/redoc> |

Teste a API pelo terminal:

```bash
curl -s http://localhost:8000/health
curl -s "http://localhost:8000/api/v1/data/?variable=temp&level=1000&region=SP"
```

---

## ⚙️ Configuração (.env)

Copie `.env.example` para `.env`. Todas as variáveis têm padrões sensatos em `core/config.py`,
então o `.env` só é necessário para personalizar:

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `NOAA_BASE_URL` | `https://nomads.ncep.noaa.gov/...` | Base do GFS completo |
| `NOAA_FILTER_URL` | `https://nomads.ncep.noaa.gov/cgi-bin/filter_gfs_0p25.pl` | Endpoint filter (subconjuntos por região) |
| `NOAA_FTP_URL` | `ftp://ftp.ncep.noaa.gov/...` | Alternativa FTP |
| `AVIATION_WEATHER_URL` | `https://aviationweather.gov/api/data/metar` | Fonte dos boletins METAR |
| `SQLITE_DB_PATH` | `data/sqlite/met_data.db` | Caminho do banco |
| `API_HOST` | `0.0.0.0` | Endereço do servidor |
| `API_PORT` | `8000` | Porta do servidor |
| `API_WORKERS` | `4` | Workers do uvicorn |
| `LOG_LEVEL` | `INFO` | Nível de log |

> 📌 Todos os caminhos de arquivo são calculados a partir de `core/config.py` (`BASE_DIR`),
> sem caminhos absolutos codificados. O próprio `core/config.py` cria os diretórios ao ser importado.

---

## 🗺️ O pipeline em detalhes

O pipeline (`scripts/process_data.py`) executa: **download → processamento → SQLite → mapas → METAR**.

> 🏭 **A regra de ouro da fábrica:** a API e o frontend são apenas a **vitrine de atendimento** —
> eles **nunca saem à rua para buscar dados**, somente mostram o que já está no estoque
> (SQLite e mapas). **Todo dado novo entra pela porta da fábrica: o pipeline.** Quer manter a
> vitrine sempre atualizada? Agende o pipeline — por exemplo, via `cron` a cada 6h, cobrindo os
> ciclos 00/06/12/18Z (veja a [FAQ](#-dúvidas-frequentes-faq)). E lembre: `scripts/pipeline.sh` é
> só o porteiro — ele ativa o ambiente e chama o `scripts/process_data.py` por você.

```bash
PYTHONPATH=. python scripts/process_data.py [opções]
```

| Flag | Padrão | Descrição |
|------|--------|-----------|
| `--date YYYYMMDD` | hoje, depois ontem | Data do ciclo GFS |
| `--analysis 00 06` | todas (00 06 12 18) | Ciclos sinóticos (aceita vários) |
| `--forecast 00 06` | todas (f000–f018) | Horas de previsão (aceita vários) |
| `--regions SP RJ` | `SP RJ PR RS MG AM` | Regiões (18 disponíveis) |
| `--all-variables` | desligado | Processa as 26 variáveis (as ausentes no GFS são puladas com erro logado) |
| `--skip-metar` | desligado | Não busca METAR |

### Comportamento que você precisa saber

- **Escopo padrão é grande**: 4 análises × 4 previsões × variáveis × regiões. **Narrow com `--analysis` e `--forecast`**.
- **Ciclos indisponíveis** na NOAA são detectados e pulados automaticamente (com aviso no log).
- **Arquivos já baixados são reutilizados** (cache em `data/grib/<data>/<análise>/`) — o pipeline é idempotente.
- Regiões desconhecidas são **silenciosamente ignoradas**.
- Variáveis fora do produto GFS são registradas no log como **erros** (não derrubam o pipeline).

> 💡 O conjunto padrão de variáveis fica em `DEFAULT_VARIABLES` no topo de `scripts/process_data.py`:
> `temp` (1000/850/500 hPa), `umidadeRel`, `u`, `v` e `vento` (850), `ventoSup` (10 m), `o3` (500),
> `total_o3`, `ps`, `precipRate`, `chuvaNaoConvec` e `categChuva` (superfície) e `nuvemMistura` (850).
> As variáveis de chuva (`precipRate`, `chuvaNaoConvec`) só têm valor em horários com chuva — em
> áreas/tempos secos os mínimos são `0`.

---

## 📊 Entendendo os dados

### Variáveis (26 no total)

**Meteorológicas (17):** `ps`, `prnm`, `temp`, `temps`, `nuvem`, `nuvemMistura`,
`chuvaNaoConvec`, `chuvaConvec`, `precipRate`, `categChuva`, `umidadeRel`, `u`, `v`,
`uSupe`, `vSupe`, `vento`, `ventoSup`

**Poluição (9):** `o3`, `total_o3`, `no2`, `so2`, `co`, `pm25`, `pm10`, `aod`, `dust`

> ⚠️ **Importante:** **18 variáveis têm dados no produto GFS pgrb2 0p25** e estão conectadas ao
> endpoint filter da NOAA: `ps`, `prnm`, `temp`, `temps`, `nuvem`, `nuvemMistura`, `umidadeRel`,
> `u`, `v`, `uSupe`, `vSupe`, `vento`, `ventoSup`, `precipRate`, `chuvaNaoConvec`, `categChuva`,
> `o3`, `total_o3`.
>
> - **`vento` e `ventoSup`** são **derivadas**: a resultante do vento (magnitude) é calculada em
>   `core/processor.py` a partir das componentes `u`/`v` (`vento`) e `uSupe`/`vSupe` (`ventoSup`)
>   — o GFS fornece apenas as componentes direcionais.
> - **Chuva:** `precipRate` (*Precipitation rate*, `PRATE`), `chuvaNaoConvec` (*Total
>   precipitation*, `APCP`) e `categChuva` (*Categorical rain*, `CRAIN`) são confirmadas no
>   inventário `varMET` e verificadas ao vivo no endpoint filter. O `APCP` acumulado só existe
>   a partir de `f006` (no `f000` é vazio/zero) — por isso o pipeline loga erro nesse caso.
> - **Nuvens:** além da cobertura total `nuvem` (`TCDC`), adicionamos `nuvemMistura`
>   (*Cloud mixing ratio*, `CLWMR`) em níveis isobáricos.
>
> Da categoria **poluição**, somente **`o3` e `total_o3`** têm dados reais. As demais
> (`no2`, `so2`, `co`, `pm25`, `pm10`, `aod`, `dust`) e `chuvaConvec` ficam no catálogo como
> *experimentais* — o endpoint `/data/variables` marca isso no campo `available`, e o frontend
> só exibe as disponíveis.
>
> Essa lista foi **confirmada pelo inventário `varMET`** (dump ASCII do conteúdo do arquivo GRIB,
> na raiz do projeto) e **verificada ao vivo** contra o endpoint filter da NOAA. Testes garantem
> exatamente `{o3, total_o3}` como poluição disponível — então não altere `AVAILABLE_IN_GFS` em
> `core/variables.py` por conta própria.

**Níveis isobáricos suportados:** `1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10` hPa
**Níveis de altura (`uSupe`/`vSupe`):** `10, 20, 30, 40, 50, 80, 100` m
**Superfície** (`ps`, `temps`, `total_o3`): nível `0` (sem parâmetro `level` em consultas/mapas)

### Regiões (18)

`SP, RJ, AM, DF, PR, RS, MG, PA, PE, CE, SA, FOR, REC, SSA, BEL, BH, CWB, POA`

Cada região é um retângulo de coordenadas (min/max de longitude e latitude) definido em
`core/config.py` (`REGIOES`). Inclui capitais e cidades com aeroportos.

---

## 🗃️ Onde os dados ficam armazenados

| Caminho | Conteúdo |
|---------|----------|
| `data/grib/<data>/<análise>/` | Arquivos GRIB baixados da NOAA (cache) |
| `data/sqlite/met_data.db` | Banco principal: dados processados + METAR |
| `data/csv/` | Exportações CSV |
| `data/metar/` | Snapshots JSON dos boletins METAR |
| `maps/` | Mapas PNG gerados |

Os mapas seguem o padrão de nome:
`GFS_<resolução>_<REGIÃO>_N<nível|SFC>_<variável>_<análise>_<data>_<previsão>.png`

> ⚠️ Os códigos de variável podem conter **underscores** (`total_o3`, `umidadeRel`, `uSupe`).
> O parser de nomes em `api/routes/maps.py` (`_FILENAME_RE`) já lida com isso.

---

## 🌐 A API REST

A base das rotas é `/api/v1` (exceto `/health` e `/docs`, que ficam na raiz).

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/health` | Status do servidor e do banco (+ `/health/ready`) |
| GET | `/api/v1/data/variables` | Catálogo das 26 variáveis (com campo `available`) |
| GET | `/api/v1/data/regions` | As 18 regiões |
| GET | `/api/v1/data/dashboard` | Resumo estatístico agregado |
| GET | `/api/v1/data/available` | Variáveis/regiões/datas disponíveis no banco |
| GET | `/api/v1/data/` | Consulta de dados (`?variable&level&region&date&analysis&limit`) |
| GET | `/api/v1/data/latest` | Registro mais recente |
| GET | `/api/v1/data/stats` | Estatísticas (mín/máx/média) |
| GET | `/api/v1/data/levels/{var}` | Níveis disponíveis para a variável |
| GET | `/api/v1/data/export/csv` | Exportação CSV |
| GET | `/api/v1/maps/{var}/{region}` | Mapa PNG (`?level&date&analysis`) |
| GET | `/api/v1/maps/list/{var}/{region}` | Lista de mapas disponíveis |
| GET | `/api/v1/metar/stations` | Estações METAR |
| GET | `/api/v1/metar/{code}` | Último METAR + decodificação |
| GET | `/api/v1/metar/latest/all` | METAR de todas as estações |
| GET | `/api/v1/info` | Metadados do app |

### Exemplos com `curl`

```bash
BASE=http://localhost:8000/api/v1

# Status
curl -s http://localhost:8000/health

# Temperatura em 1000 hPa na região SP
curl -s "$BASE/data/?variable=temp&level=1000&region=SP"

# Estatísticas
curl -s "$BASE/data/stats?variable=temp&level=850&region=SP"

# Exportar CSV
curl -s "$BASE/data/export/csv?variable=temp&level=850&region=SP" -o dados.csv

# Baixar mapa PNG (data + análise juntas)
curl -s "$BASE/maps/temp/SP?level=850&date=20260807&analysis=00" -o mapa.png

# Último METAR de Guarulhos (SBGR)
curl -s "$BASE/metar/SBGR"

# Dashboard agregado
curl -s "$BASE/data/dashboard"
```

> 💡 **Dica:** para variáveis de superfície (ex.: `ps`), **não** use o parâmetro `level` —
> elas são gravadas com nível `0`. O frontend já lida com isso automaticamente.

---

## 🖥️ O frontend e o dashboard

O frontend é servido pela própria API em `/` e tem três áreas:

- **Dashboard** — cartões com total de registros, variáveis, regiões e estatísticas METAR;
  tabelas agregadas por variável e por região.
- **Mapa** — seleção de categoria (Meteorológicas/Poluição), variável, nível, região, data e
  análise; carrega o mapa PNG e mostra mín/máx/média; botão **CSV** exporta os dados.
- **METAR** — seleção de estação e visualização do boletim cru + decodificado.

> ⚠️ Os ativos estáticos são servidos sob `/static`. O `index.html` referencia
> `static/style.css` e `static/app.js` (sem `/` na frente, e **não** `style.css` puro) —
> isso é garantido por testes, então não troque esses caminhos.

---

## 🐳 Docker (opcional)

Você pode rodar sem instalar nada localmente:

```bash
docker compose up -d api                       # sobe a API (sempre ativa)
docker compose --profile manual run pipeline   # roda o pipeline manualmente
```

- O serviço `api` sobe sozinho e fica de pé com healthcheck.
- O serviço `pipeline` só roda quando você pede (via perfil `manual`).
- `data/` e `maps/` são montados como volumes — os dados persistem entre execuções.
- O Dockerfile instala as libs de sistema necessárias (eccodes, proj, geos) automaticamente.

---

## 🧪 Testes e validação

```bash
# Suíte de testes end-to-end (TestClient in-process, sem servidor externo)
PYTHONPATH=. pytest tests/test_e2e.py -v

# Unit tests (sem rede/dados) — ex.: lógica do vento resultante
PYTHONPATH=. pytest tests/test_processor.py -v

# Validação completa: dependências + pipeline real + banco + mapas + testes
bash scripts/validate.sh
```

> ⚠️ **Os testes E2E leem o SQLite e os mapas — você precisa rodar o pipeline antes.**
> Eles verificam `total_records > 0`, boletins METAR e PNGs. Depois de populado o banco,
> os testes não precisam de internet.
>
> ⚠️ O `validate.sh` roda o pipeline sem `--date` (usa o ciclo GFS mais recente encontrado pela
> NOAA). Para uma checagem totalmente determinística, rode o pipeline + pytest diretamente.

---

## 📁 Estrutura do projeto

```
core/          Lógica de negócio (config, variáveis, regiões, download, GRIB, processamento, mapas, METAR)
api/           FastAPI (main, schemas, rotas: health, data, maps, metar)
frontend/      Interface web estática (index.html, app.js, style.css)
scripts/       process_data.py + wrappers shell (pipeline.sh, server.sh, validate.sh)
tests/         Testes end-to-end (test_e2e.py) + unit (test_processor.py)
data/          Runtime (grib/, sqlite/, csv/, metar/) — ignorado pelo Git
maps/          Mapas PNG gerados — ignorado pelo Git
varMET         Inventário GRIB (dump ASCII) — referência das variáveis disponíveis
```

---

## 🆘 Solução de problemas

| Problema | Causa provável | Solução |
|----------|----------------|---------|
| Pip falha em `pygrib`/`basemap` | Faltam libs de sistema | `sudo apt-get install -y gcc g++ libeccodes-dev libproj-dev libgeos-dev libsqlite3-dev` |
| `ModuleNotFoundError: core...` | `PYTHONPATH` não aponta para o projeto | Rode sempre com `PYTHONPATH=.` |
| Pipeline não encontra ciclo GFS | Data/ciclo ainda indisponível na NOAA | Use `--date` de um dia anterior ou rode mais tarde (o script tenta hoje e ontem) |
| Pipeline demora muito | Escopo padrão grande | Use `--analysis 00` e `--forecast 00` |
| Mapa retorna 404 | Não há mapa gerado para aquela seleção | Rode o pipeline para o conjunto; consulte `/maps/list/{var}/{region}` |
| Dados "vazios" de poluição | Variável não existe no GRIB pgrb2 | Só `o3` e `total_o3` estão confirmadas |
| Porta 8000 em uso | Outro processo | `bash scripts/server.sh stop` ou mude `API_PORT` no `.env` |
| Testes E2E falham sem dados | Banco/mapas ainda não populados | Rode o pipeline antes dos testes |
| METAR de Guarulhos aparece como "PR" | A AviationWeather devolve o estado errado | Já corrigido em `core/metar.py` (registro local `DEFAULT_STATIONS`) |

---

## ❓ Dúvidas frequentes (FAQ)

### 1. Por que só vejo `o3` e `total_o3` na categoria Poluição?

Porque são as **únicas variáveis de poluição que existem no produto GFS pgrb2 0p25**.
Confirmei isso cruzando o catálogo com o inventário `varMET` (dump do arquivo GRIB).
As outras (`no2`, `so2`, `co`, `pm25`, `pm10`, `aod`, `dust`) ficam registradas no catálogo,
marcadas como `available: false`, prontas para quando a fonte tiver o dado.

### 2. O pipeline demora muito. O que posso fazer?

Por padrão ele processa **4 análises × 4 previsões** para cada variável e região — centenas de
downloads. Restrinja com `--analysis 00` e `--forecast 00`, e use poucas regiões com `--regions SP`.
Os arquivos já baixados são reutilizados, então re-executar é mais rápido.

### 3. Preciso de internet para usar a API?

A **API e o frontend** não: eles leem o SQLite e os mapas já gerados. A **internet só é necessária
na ingestão** (pipeline). Por isso os testes E2E funcionam offline após um pipeline.

### 4. O que é o arquivo `varMET` na raiz?

É um **dump ASCII do inventário do arquivo GRIB** — a lista de variáveis/ níveis que existem no
produto. É a fonte de verdade usada para decidir quais variáveis marcar como `available`.
Você não precisa abri-lo no dia a dia.

### 5. Como agendo o pipeline para rodar sozinho?

Não há scheduler embutido (de propósito). Use o `cron` do sistema:

```bash
0 */6 * * * bash /home/paulo/Documentos/meus_codigos/server_met/scripts/pipeline.sh
```

O exemplo acima roda a cada 6 horas (ciclos 00/06/12/18Z).

### 6. Quero adicionar uma nova variável. O que preciso saber?

1. Ela precisa existir no GFS pgrb2 0p25 (verifique no `varMET` e, de preferência, teste a URL do
   endpoint filter ao vivo — alguns campos só existem a partir de `f006`, como o `APCP`);
2. Adicione o registro em `core/variables.py` (nome GRIB, tipo de nível, conversão de unidade);
3. Se usar o endpoint filter, mapeie o short name em `NOAA_FILTER_VARS` em `core/downloader.py`;
4. **Variáveis derivadas** (calculadas de outras, como a resultante do vento) usam o campo
   `derived: ["u", "v"]` no registro — o pipeline baixa as componentes e combina em
   `core/processor.py` (`combine_wind_resultant`);
5. Adicione em `AVAILABLE_IN_GFS` **somente** se o dado realmente existir — os testes E2E
   garantem que as variáveis de poluição disponíveis sejam exatamente `{o3, total_o3}`.

### 7. O mapa retorna 404. O que fazer?

Significa que não há PNG para aquela combinação variável/região/nível/data/análise.
Rode o pipeline para esse conjunto (ex.: `--date 20260807 --analysis 00 --forecast 00 --regions SP`)
e confira em `/maps/list/{var}/{region}`.

### 8. A API precisa de autenticação?

Não. A API é **somente leitura** e, em ambiente local, não exige autenticação.
Para expor em produção, coloque atrás de um proxy com `HTTPS` e controle de acesso.

### 9. Por que o METAR do SBGR aparece como estado "PR"?

Um erro conhecido da **AviationWeather**: ela às vezes devolve o estado errado no nome da
estação (ex.: Guarulhos → "PR"). O `core/metar.py` corrige o nome usando o registro local
`DEFAULT_STATIONS`, e um teste garante que SBGR fique como "SP".

### 10. Os dados são reais ou simulados?

**Reais.** O pipeline baixa as previsões vigentes do modelo GFS da NOAA e boletins METAR ao vivo
da AviationWeather. A qualidade depende da disponibilidade dessas fontes (ciclos indisponíveis são
pulados com aviso).

---

## 🔮 Notas finais

- `data/` e `maps/` são **ignorados pelo Git** (artefatos gerados em execução).
- Para produção, use `bash scripts/server.sh start` ou Docker.
- A API é somente leitura e não exige autenticação em ambiente local.
- Quer saber mais? A documentação interativa da API está em `/docs` quando o servidor estiver no ar.

Feito com ☕, Python e dados abertos da NOAA. 🛰️
