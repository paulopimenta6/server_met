# Servidor Meteorológico — MET Server (v4.0.0)

Servidor que **capta, organiza, analisa e mostra** dados de previsão do tempo do modelo
**GFS** (da NOAA, agência meteorológica dos EUA), com **mapas, animações, estatísticas**
e observações reais de aeroportos (METAR), tudo em um **site simples de usar**.

> **Linguagem simples:** se você não é da área técnica, comece pela seção
> [Entendendo o sistema](#entendendo-o-sistema-em-linguagem-simples). A referência
> técnica completa fica no [apêndice](#apendice-referencia-tecnica).

```
captação → tratamento → análise → persistência → resultados → servidor + site
(GRIB,     (extração,    (estatís-   (SQLite,       (mapas,      (API REST,
 METAR)     unidades,     tica,       histórico,     animações,   site web)
            níveis,       perfis,     cache)         matrizes,
            vento)        séries)                    gráficos)
```

---

## Entendendo o sistema em linguagem simples

### O que é o GFS?
O **GFS** é um "previsor de tempo" gigante da NOAA. A cada 6 horas (nos horários
00, 06, 12 e 18, horário de Londres), ele calcula como o tempo deve estar nas
próximas horas. Os arquivos que ele gera se chamam **GRIB** — imagine-os como
"fotografias numéricas" do clima, cobrindo o mundo inteiro em vários níveis de
altitude.

### O que é uma "previsão (+6h, +12h, +18h)"?
É o quanto o modelo olha para a frente. **+00h** é o "agora", **+06h** é daqui a
6 horas, e assim por diante. O site consegue **animar** essas previsões: um GIF
que mostra o tempo evoluindo quadro a quadro.

### O que é "análise (00, 06, 12, 18 Z)"?
É o horário em que o modelo "rodou" (o Z indica o horário de Londres). Quando o
servidor baixa dados novos, ele sempre usa o ciclo mais recente já publicado.

### O que é o METAR?
São os **boletins reais** que os aeroportos publicam: vento, visibilidade, nuvens
e temperatura medidos na hora. Eles servem para comparar a previsão com a
realidade.

### O que é "nível (hPa)"?
A **altitude** do mapa: 500 hPa é o meio da atmosfera, 850 hPa e 925 hPa são
perto do chão.

### O que este sistema faz sozinho?
- **Baixa dados continuamente**: a cada poucos minutos verifica se o GFS publicou
  uma nova previsão e se os aeroportos emitiram novos boletins. Quando há novidade,
  baixa e processa tudo automaticamente (mapas, matrizes e análises das regiões
  predefinidas).
- **Guarda histórico**: tudo fica registrado em um banco local (SQLite) — dá para
  consultar previsões e observações antigas.
- **Serve mapas e análises na hora**: pelo site ou pela API.

---

## Começando rápido

```bash
# 1) preparar o ambiente (uma vez)
./scripts/run.sh install

# 2) rodar os testes (opcional, mas recomendado)
./scripts/run.sh test

# 3) ligar o servidor + site
./scripts/run.sh server
```

Abra o navegador em **http://localhost:8000** — o site já estará no ar.
A documentação técnica interativa da API fica em **http://localhost:8000/docs**.

> O download real de dados exige internet. Se não houver dados ainda, o site
> mostra a mensagem de erro com orientação — o servidor continua tentando
> baixar sozinho nos horários certos.

---

## Usando o site (passo a passo)

O site tem 5 abas:

| Aba | O que faz | Como usar |
|---|---|---|
| **Mapas** | Gera mapas de uma variável (temperatura, chuva, vento…) sobre uma região | Escolha cidade/estado na lista **ou clique no mapa** para escolher latitude/longitude; ajuste variável, nível e data; clique em "Gerar mapa" |
| **Animações** | Cria um **GIF** mostrando a evolução da previsão (agora → +6h → +12h → +18h) | Escolha região e variável, clique em "Gerar animação" |
| **Estatísticas** | Números (média, mínima, máxima, desvio…) e gráficos da variável na região | Escolha região/variável e veja tabela + gráficos de perfil, série e histograma |
| **METAR** | Últimas observações reais dos aeroportos | Clique em "Atualizar" |
| **Ajuda** | Este guia em linguagem simples | — |

### Regiões: cidades e estados

Cada localidade tem dois níveis de enquadramento (as coordenadas já vêm
corretas e a cidade inteira aparece no mapa):

| Código | Estado (região) | Código | Cidade (centro ±0.5°) |
|---|---|---|---|
| `SP` | São Paulo | `SP-CIDADE` | São Paulo |
| `RJ` | Rio de Janeiro | `RJ-CIDADE` | Rio de Janeiro |
| `AM` | Amazonas | `AM-CIDADE` | Manaus |
| `DF` | Distrito Federal | `DF-CIDADE` | Brasília |
| `PR` | Paraná | `PR-CIDADE` | Curitiba |
| `RS` | Rio Grande do Sul | `RS-CIDADE` | Porto Alegre |
| `MG` | Minas Gerais | `MG-CIDADE` | Belo Horizonte |
| `PA` | Pará | `PA-CIDADE` | Belém |
| `PE` | Pernambuco | `PE-CIDADE` | Recife |
| `CE` | Ceará | `CE-CIDADE` | Fortaleza |
| `SA` | América do Sul (visão geral) | — | — |

Na API também é possível escolher qualquer ponto: envie `lon`/`lat` (o sistema
monta uma caixa de ±5°) ou uma caixa própria com `lon_min/lon_max/lat_min/lat_max`.

---

## Configuração — `environment/path.conf`

Arquivo simples `chave=valor`. Todos os caminhos são relativos à raiz do projeto:

```
dir_gribs=data/gribs                      # arquivos GRIB baixados
dir_mapas=data/mapasGrib                  # mapas PNG
dir_matrizes=data/matrizGrib              # matrizes CSV
dir_matrizes_predi=data/matrizGrib/predi
dir_matrizes_bluesky=data/matrizGrib/bluesky
dir_analise=data/analise                  # análises
dir_tmp=data/tmp                          # saídas temporárias (mapas/gerações)
db_file=data/met_server.db                # banco SQLite

# --- captação contínua (requisito 4) ---
scheduler_enabled=true                    # liga/desliga a captação automática
scheduler_grib_interval_min=60            # a cada X min verifica novo ciclo GFS
scheduler_metar_interval_min=30           # a cada X min busca METARs
# scheduler_auto_pipeline=SP,SP-CIDADE    # (opcional) só estas regiões no pipeline
# forecast_hours=00,06,12,18              # (opcional) horas de previsão a capturar
```

No código, use sempre o singleton `Settings` (nunca `data/...` direto):

```python
from server_MET.core.config import Settings
s = Settings()
print(s.dir_gribs, s.db_path)
```

---

## Captação contínua (o que o servidor faz sozinho)

O `SchedulerRunner` (`server_MET/acquisition/scheduler.py`) roda dentro do
servidor (ou avulso com `./scripts/run.sh scheduler`):

1. **GRIB**: a cada `scheduler_grib_interval_min` verifica o ciclo GFS mais
   recente que já deveria estar publicado (o NOMADS publica ~5h após o início
   do ciclo). Se ainda não baixado:
   - baixa as resoluções 0.25°/0.50°/1.00° (horas 00–18 de previsão);
   - roda o **pipeline automático**: mapas, matrizes (incl. BlueSky) e análises
     (resumo, perfil, série com tendência) para todas as regiões predefinidas;
   - registra o ciclo em `ingest_state` para não repetir.
2. **METAR**: a cada `scheduler_metar_interval_min` busca os boletins de todas
   as estações e guarda o histórico.

Acompanhe pelo navegador ou API: `GET /scheduler/status` (ou
`./scripts/run.sh scheduler-status`). Para forçar uma verificação agora:
`POST /scheduler/run-now`.

---

## Variáveis disponíveis

| Chave | Significado | Unidade exibida |
|---|---|---|
| `temp` | Temperatura (nível de pressão) | °C |
| `temps` | Temperatura (superfície) | °C |
| `ps` | Pressão na superfície | hPa |
| `prnm` | Pressão ao nível do mar | hPa |
| `nuvem` | Nebulosidade | % |
| `chuvaNaoConvec` | Chuva acumulada | mm |
| `chuvaConvec` | Chuva convectiva | mm |
| `umidadeRel` | Umidade relativa | % |
| `u` / `v` | Componentes do vento | m/s |
| `uSupe` / `vSupe` | Componentes do vento na superfície | m/s |
| `wind` / `winds` | **Calculados** a partir de u/v (não são GRIB) | m/s |

Níveis de pressão: 150–1000 hPa (passo de 50, mais 925/950/975). Níveis fora
do intervalo são ajustados para o mais próximo. Variáveis de superfície usam
`level` vazio/nulo.

---

## Banco de dados (SQLite)

Arquivo padrão: **`data/met_server.db`** (`db_file=` no path.conf), modo WAL
(leitura e escrita simultâneas sem travar).

| Tabela | Conteúdo | Preenchida por |
|---|---|---|
| `downloads` | histórico de downloads GRIB | `GribDownloader` |
| `outputs` | artefatos gerados (mapa/matriz/bluesky/gráfico/GIF) | geradores de saída |
| `metar_obs` | observações METAR (histórico) | `MetarClient` |
| `tasks` | tarefas em segundo plano (download) | API |
| `analysis_results` | análises (cache + histórico) | API / pipeline |
| `ingest_state` | estado da captação contínua (ciclos processados, horários) | scheduler |

- **Cache**: repetir a mesma análise não recalcula — responde do banco com a
  marca `"**cached**": true`.
- **Backup**: basta copiar `data/met_server.db`.
- **Inspeção**: `./scripts/run.sh db-status` ou `GET /db/status`.

---

## Scripts

```bash
./scripts/run.sh install            # dependências + diretórios
./scripts/run.sh server             # sobe o servidor + site em :8000 (captação contínua inclusa)
./scripts/run.sh download [YYYYMMDD] [HH] [0p25|0p50|1p00]   # download manual de GRIB
./scripts/run.sh analysis [YYYYMMDD]   # exemplo de análise (SP)
./scripts/run.sh db-status          # estado do banco
./scripts/run.sh scheduler          # uma verificação de ciclo GFS (worker avulso)
./scripts/run.sh scheduler-status   # estado da captação contínua
./scripts/run.sh test               # testes (121, offline)
./scripts/run.sh clean [days]       # remove dados antigos (default 2)
./scripts/run.sh docker-build | docker-up | docker-down
```

---

## Testes

```bash
~/envs/met/bin/python -m pytest tests/ -v     # 121 testes, offline
```

Cobrem: configuração, regiões (estados + cidades), processamento, METAR offline,
persistência, análises, geradores (mapas/GIF/matrizes), API e captação contínua
(scheduler com downloader simulado). Os testes isolam o banco em `tmp_path` e
toleram ausência de rede.

---

## Docker

```bash
./scripts/run.sh docker-build && ./scripts/run.sh docker-up
```

O `Dockerfile` (python:3.11-slim) instala `wget`, `libgfortran5` e `libgomp1`
(pygrib prebuilt). Volumes nomeados persistem dados e banco; `environment/` é
montado do host. A captação contínua roda dentro do container (ligada por padrão).

---

## Apêndice — Referência técnica (API REST)

Base: `http://localhost:8000` · Docs interativas: `/docs`

### Informação e catálogo

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | **Site** (HTML) |
| GET | `/info` | Informações da API (JSON) |
| GET | `/health` | Status, versão, GRIBs disponíveis, uptime |
| GET | `/variables` | Variáveis (inclui rótulo em português) |
| GET | `/regions` | Regiões (estados, cidades com centro, bboxes) |
| GET | `/catalog` | Datas/análises/resoluções GRIB disponíveis |
| GET | `/db/status` | Tabelas do banco e contagens |

### GRIBs e downloads

| Método | Rota | Descrição |
|---|---|---|
| GET | `/gribs/list?date=YYYYMMDD` | Arquivos GRIB disponíveis |
| POST | `/gribs/download?date_str=…&analysis_hour=…` | Download em background (query params!) |
| GET | `/gribs/download/{task_id}` | Status da tarefa (persistente) |
| POST | `/gribs/info` | Variáveis de um arquivo |

> **Integridade dos GRIBs:** arquivos baixados são validados em subprocesso
> (leitura via pygrib + `select` com timeout). Se o arquivo estiver corrompido
> (download interrompido, por exemplo), ele é removido e o download marcado como
> `failed` — evitando que um arquivo inválido trave o pipeline.

### Mapas, animações e matrizes

| Método | Rota | Descrição |
|---|---|---|
| POST | `/maps/generate` | Mapas PNG (JSON com caminhos em `data/tmp/<uuid>/`) |
| POST | `/maps/animate?duration_ms=…` | **GIF animado** das previsões f00–f18 |
| POST | `/matrices/generate` | Matrizes CSV |
| POST | `/bluesky/wind` | Matriz BlueSky |
| GET | `/files/{kind}/{path}` | Baixa artefato (`mapas`, `matrizes`, `bluesky`, `analise`, `tmp`) — anti path-traversal |

```bash
curl -X POST http://localhost:8000/maps/generate \
  -H "Content-Type: application/json" \
  -d '{"variable":"temp","level":500,"region":"SP-CIDADE","date":"20260731","analysis":"06"}'
# → {"maps": ["…/data/tmp/<uuid>/GFS_0.25_Cidade_de_Sao_Paulo_N500_temp_20260731_06_00.png"], "count": 1}
```

### Análises (estatísticas)

| Método | Rota | Descrição |
|---|---|---|
| POST | `/analysis/summary` | Resumo: min, max, média, mediana, DP, percentis p1–p99 |
| POST | `/analysis/profile` | Perfil vertical em todos os níveis 150–1000 hPa |
| POST | `/analysis/timeseries` | Série nas previsões + tendência (slope, p-valor, R²) |
| POST | `/analysis/charts` | Gráficos PNG (perfil, série, histograma) |
| GET | `/analysis/regions/{region}` | Estado consolidado da região |

### METAR, histórico e captação contínua

| Método | Rota | Descrição |
|---|---|---|
| POST | `/metar/fetch` | METAR por região ou ICAO |
| GET | `/metar/all` | METARs das estações |
| GET | `/metar/history?icao=` | Histórico de observações |
| GET | `/history/downloads` · `/outputs` · `/analysis` | Históricos |
| GET | `/scheduler/status` | Estado da captação contínua |
| POST | `/scheduler/run-now` | Verificação imediata de ciclo GFS |
| POST | `/cleanup?days_old=2` | Remove dados antigos |

### Formas de escolher a região (em qualquer rota com região)

1. **Nome**: `{"region": "SP"}` ou `{"region": "SP-CIDADE"}`;
2. **Caixa**: `lon_min/lon_max/lat_min/lat_max`;
3. **Ponto central**: `lon`/`lat` (caixa de ±5°).

---

## Manutenção e solução de problemas

| Problema | Causa | Solução |
|---|---|---|
| Mapa gerado aparece "sem continente" | Sem Cartopy/Basemap ou offline | `pip install cartopy scipy`; feições geográficas degradam offline |
| Mapa com norte/sul trocados | (bug da v3) | Atualize para a v4 — o flip de latitude agora acompanha os dados |
| Nenhum arquivo baixado | Ciclo GFS ainda não publicado | O NOMADS publica ~5h após a hora; o scheduler tenta sozinho |
| `404` em mapas/análises | Arquivo GRIB não existe | Rodar `/gribs/download` antes ou aguardar a captação contínua |
| Análise retorna `**cached**` | Resultado já computado | Apagar registros de `analysis_results` para recalcular |
| METAR vazio | ICAO inválido ou sem rede | Verificar o código ICAO e acesso a aviationweather.gov |
| Site sem tiles do mapa interativo | Sem internet no servidor | Os tiles (OpenStreetMap) exigem internet; o resto do site funciona offline |
| Captação contínua não roda | `scheduler_enabled=false` | Ligar no `environment/path.conf` |

---

## Changelog

- **v4.0.0** — mapas corrigidos com **regiões cidade/estado** (bboxes precisas,
  flip de latitude consertado, títulos e legendas completos em português);
  **site interativo** (Leaflet, escolha por latitude/longitude, abas de mapas,
  animações, estatísticas, METAR e ajuda); **animações GIF** das previsões
  (`/maps/animate`); **captação contínua** com pipeline automático (scheduler +
  tabela `ingest_state` + `/scheduler/status`); documentação em linguagem
  simples; 121 testes.
- **v3.0.0** — arquitetura modular em camadas; camada de análise (estatística,
  perfil, séries com tendência statsmodels); persistência SQLite com cache;
  servidor de artefatos com anti path-traversal; 102 testes.
- **v2.0.0** — arquitetura FastAPI consolidada; METAR com a nova API
  aviationweather; mapas com Cartopy (fallback Basemap).
