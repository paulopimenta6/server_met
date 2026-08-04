# 🌤️ Server MET v2.0

> **Servidor de Dados Meteorológicos e de Poluição Atmosférica**
> 
> Baixa, processa e disponibiliza dados do modelo GFS (NOAA) via API REST e interface web interativa.
> 
> [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
> [![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
> [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 O que este projeto faz?

| Funcionalidade | Descrição |
|----------------|-----------|
| 📥 **Download Automático** | Busca arquivos GRIB do NOAA GFS (resolução 0.25° e 1.00°) |
| ⚙️ **Processamento Inteligente** | Extrai variáveis meteorológicas e de poluição por região/nível |
| 💾 **Armazenamento Dual** | SQLite (consultas rápidas) + CSV (exportação/backup) |
| 🔌 **API REST Completa** | FastAPI com documentação automática (`/docs`) |
| 🗺️ **Frontend Interativo** | Mapa Leaflet + gráficos Chart.js em tempo real |
| ⏰ **Agendamento Nativo** | APScheduler ou systemd timer (00:30, 06:30, 12:30, 18:30) |
| 🐳 **Deploy Flexível** | Docker Compose, systemd ou execução local |

---

## 🚀 Início Rápido (3 minutos)

### Pré-requisitos
- **Docker** (recomendado) **OU** Python 3.11+ com ambiente virtual

---

### Opção 1: Docker Compose 🐳 (Mais Fácil)

```bash
# 1. Clone e entre no diretório
git clone <repo-url> server_met
cd server_met

# 2. Suba tudo (API + Scheduler + Banco)
docker-compose up -d

# 3. Pronto! Acesse:
#    🌐 Interface Web:    http://localhost:8000
#    📚 Documentação API: http://localhost:8000/docs
#    ❤️ Health Check:     http://localhost:8000/health
```

---

### Opção 2: Python Local 🐍 (Desenvolvimento)

```bash
# 1. Clone e entre no diretório
git clone <repo-url> server_met
cd server_met

# 2. Ative o ambiente virtual (já configurado)
source ~/envs/met/bin/activate

# 3. Instale dependências
pip install -r requirements.txt

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite .env se necessário

# 5. Execute o pipeline (baixa + processa + salva)
PYTHONPATH=. python scripts/run_pipeline.py

# 6. Inicie a API (terminal 1)
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# 7. Inicie o agendador (terminal 2)
PYTHONPATH=. python scripts/schedule.py
```

---

### Opção 3: Systemd (Produção Linux)

```bash
# Instala serviços systemd
sudo ./deploy/install_systemd.sh

# Inicia API e Scheduler
sudo systemctl start server-met-api server-met-scheduler

# Habilita inicialização automática
sudo systemctl enable server-met-api server-met-scheduler

# Ver logs
journalctl -u server-met-api -f
```

---

## 🎯 Como Usar a Interface Web

1. Acesse **http://localhost:8000**
2. Selecione:
   - **Variável**: Temperatura, Ozônio, Vento, Chuva, etc.
   - **Nível**: Pressão (hPa) ou altura (metros)
   - **Região**: SP, RJ, FOR, REC, etc. (18 disponíveis)
   - **Data/Análise**: Ciclo de previsão (00Z, 06Z, 12Z, 18Z)
3. Clique em **"Carregar Dados"**
4. Explore:
   - 🗺️ **Mapa interativo** - clique nos pontos para ver valores
   - 📊 **Estatísticas** - min, max, média
   - 📈 **Série temporal** - evolução ao longo do tempo
   - 💾 **Exportar CSV** - baixe os dados brutos

---

## 📊 Variáveis Disponíveis

### 🌡️ Meteorológicas (12)
| Código | Nome | Unidade | Níveis |
|--------|------|---------|--------|
| `temp` | Temperatura | °C | 1000, 925, 850, 700, 500, 300, 200, 100, 50, 30, 20, 10 hPa |
| `temps` | Temperatura (superfície) | °C | Superfície |
| `ps` | Pressão (superfície) | hPa | Superfície |
| `prnm` | Pressão (nível do mar) | hPa | Nível do mar |
| `umidadeRel` | Umidade relativa | % | Isobáricos |
| `nuvem` | Nebulosidade total | % | Isobáricos |
| `chuvaNaoConvec` | Precipitação total | mm | Superfície |
| `chuvaConvec` | Precipitação convectiva | mm | Superfície |
| `u`, `v` | Vento (componentes) | m/s | Isobáricos |
| `uSupe`, `vSupe` | Vento (altura) | m/s | 10, 20, 30, 40, 50, 80, 100 m |

### 🏭 Poluição (8) — *NOVO!*
| Código | Nome | Unidade | Status |
|--------|------|---------|--------|
| `o3` | Ozônio | ppbv | ✅ Confirmado no GFS |
| `no2` | Dióxido de nitrogênio | ppbv | 🔬 Experimental |
| `so2` | Dióxido de enxofre | ppbv | 🔬 Experimental |
| `co` | Monóxido de carbono | ppbv | 🔬 Experimental |
| `pm25` | Material particulado 2.5 | µg/m³ | 🔬 Experimental |
| `pm10` | Material particulado 10 | µg/m³ | 🔬 Experimental |
| `aod` | Profundidade óptica aerosóis | - | 🔬 Experimental |
| `dust` | Poeira mineral | ppbv | 🔬 Experimental |

> **Nota**: Variáveis "experimentais" podem não estar disponíveis em todos os arquivos GRIB do NOAA. O sistema tenta extraí-las automaticamente quando presentes.

---

## 🗺️ Regiões Cobertas (18)

| Código | Região | Código | Região |
|--------|--------|--------|--------|
| `SP` | São Paulo | `FOR` | Fortaleza |
| `RJ` | Rio de Janeiro | `REC` | Recife |
| `AM` | Amazonas | `SSA` | Salvador |
| `DF` | Distrito Federal | `BEL` | Belém |
| `PR` | Paraná | `BH` | Belo Horizonte |
| `RS` | Rio Grande do Sul | `CWB` | Curitiba |
| `MG` | Minas Gerais | `POA` | Porto Alegre |
| `PA` | Pará | `CE` | Ceará |
| `PE` | Pernambuco | `SA` | Sul América |

---

## 🔌 API REST — Referência Rápida

Base URL: `http://localhost:8000/api/v1`

| Endpoint | Parâmetros | Descrição |
|----------|------------|-----------|
| `GET /health` | - | Health check do sistema |
| `GET /data/variables` | - | Lista todas as variáveis |
| `GET /data/regions` | - | Lista todas as regiões |
| `GET /data/available` | - | Resumo do que está disponível |
| `GET /data/` | `variable`, `level`, `region`, `date`, `analysis`, `limit` | Consulta dados filtrados |
| `GET /data/latest` | `variable`, `level`, `region` | Último registro |
| `GET /data/stats` | `variable`, `level`, `region`, `date`, `analysis` | Estatísticas |
| `GET /data/levels/{var}` | - | Níveis disponíveis p/ variável |
| `GET /data/export/csv` | `variable`, `level`, `region`, `date`, `analysis` | Exporta CSV |
| `GET /maps/{var}/{region}` | `level`, `date`, `analysis`, `forecast` | Mapa PNG |
| `GET /maps/geojson/{var}/{region}` | `level`, `date`, `analysis` | GeoJSON |

### Exemplos de Uso

```bash
# Temperatura a 1000 hPa em SP no dia 15/01/2024 análise 00Z
curl "http://localhost:8000/api/v1/data/?variable=temp&level=1000&region=SP&date=20240115&analysis=00"

# Último ozônio disponível a 500 hPa no RJ
curl "http://localhost:8000/api/v1/data/latest?variable=o3&level=500&region=RJ"

# Exportar CSV de vento a 850 hPa
curl "http://localhost:8000/api/v1/data/export/csv?variable=u&level=850&region=SP" > vento_sp.csv

# Mapa de ozônio (GeoJSON para Leaflet)
curl "http://localhost:8000/api/v1/maps/geojson/o3/SP?level=500"
```

---

## ⚙️ Configuração (.env)

Copie `.env.example` para `.env` e ajuste:

```env
# NOAA GFS
NOAA_BASE_URL=https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.

# Banco de dados
SQLITE_DB_PATH=data/sqlite/met_data.db

# Servidor API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Logs
LOG_LEVEL=INFO

# Agendador (horário de Brasília)
SCHEDULER_TIMEZONE=America/Sao_Paulo
PIPELINE_SCHEDULE_HOURS=0,6,12,18
```

---

## 🧪 Testes

```bash
# Testes unitários (core, persistence, etc)
PYTHONPATH=. pytest tests/ -v

# Testes E2E (precisa API rodando em localhost:8000)
PYTHONPATH=. pytest scripts/test_e2e.py -v

# Validação completa do pipeline
PYTHONPATH=. python scripts/validate_pipeline.py
```

---

## 📁 Estrutura do Projeto

```
server_met/
├── core/                    # 🧠 Lógica de negócio
│   ├── config.py           # Configurações centralizadas
│   ├── variables.py        # Registry de variáveis (MET + poluição)
│   ├── persistence.py      # SQLite + CSV
│   ├── regions.py          # 18 regiões pré-definidas
│   ├── downloader.py       # Download GRIB assíncrono (NOAA HTTPS)
│   ├── grib_reader.py      # Leitura GRIB com pygrib
│   └── processor.py        # Extração e estatísticas
│
├── api/                     # 🔌 REST API (FastAPI)
│   ├── main.py             # App principal + StaticFiles
│   ├── routes/
│   │   ├── health.py       # /health
│   │   ├── data.py         # /data/* (consultas, export)
│   │   └── maps.py         # /maps/* (PNG, GeoJSON)
│   └── schemas.py          # Pydantic models
│
├── frontend/                # 🌐 Interface Web (servida pela API)
│   ├── index.html          # Mapa Leaflet + controles
│   ├── app.js              # Lógica: fetch API, gráficos Chart.js
│   └── style.css           # Estilos responsivos
│
├── scripts/                 # ⚙️ Automação
│   ├── run_pipeline.py     # Pipeline completo
│   ├── schedule.py         # APScheduler (00:30, 06:30, 12:30, 18:30)
│   ├── test_e2e.py         # Testes Playwright
│   └── validate_pipeline.py # Validação ponta-a-ponta
│
├── data/                    # 💾 Dados (gitignored)
│   ├── grib/               # Arquivos .grb baixados
│   ├── sqlite/             # met_data.db
│   └── csv/                # CSVs exportados
│
├── maps/                    # 🗺️ PNGs gerados (gitignored)
│
├── deploy/                  # 🚀 Deploy
│   ├── systemd/            # 4 service files + timer
│   └── install_systemd.sh  # Instalador automático
│
├── docker-compose.yml       # Orquestração Docker
├── Dockerfile               # Imagem Python 3.11
├── requirements.txt         # Dependências
├── .env / .env.example      # Configuração
├── environment/path.conf    # Paths legados
├── planejamento_atualizacao.txt
├── goGribV2.sh              # Script original (referência)
└── README.md
```

---

## ❓ Perguntas Frequentes

### "O download falha com erro 403"
O NOAA bloqueia alguns IPs no HTTPS. O sistema tenta automaticamente, mas em produção recomenda-se:
- Usar proxy/VPN
- Configurar mirror local
- Ou usar arquivos GRIB de teste para desenvolvimento

### "Não aparece dados na interface"
1. Verifique se o pipeline rodou: `PYTHONPATH=. python scripts/run_pipeline.py`
2. Confirme se há arquivos em `data/grib/`
3. Veja logs da API para erros de consulta

### "Quero adicionar uma nova região"
Edite `core/config.py` → dicionário `REGIOES` com coordenadas (lon_min, lon_max, lat_min, lat_max).

### "Como mudar horários do agendador?"
Altere `PIPELINE_SCHEDULE_HOURS` no `.env` (ex: `0,12` para 2x ao dia).

### "Preciso de dados históricos"
O sistema mantém tudo no SQLite. Use `GET /data/?date=20240101&limit=1000` ou exporte CSV.

---

## 🐛 Problemas Conhecidos

| Problema | Workaround |
|----------|------------|
| NOAA HTTPS 403 | Use Docker (mesma rede) ou mirror local |
| Variáveis de poluição ausentes | Nem todos ciclos GFS têm; marcadas como "experimental" |
| PyGRIB lento em arquivos grandes | Use resolução 1.00° para testes rápidos |
| Frontend não carrega mapa | Verifique se API está em `localhost:8000` (CORS) |

---

## 🤝 Contribuindo

```bash
# 1. Fork o projeto
# 2. Crie branch
git checkout -b feature/minha-melhoria

# 3. Faça alterações + testes
PYTHONPATH=. pytest tests/ -v

# 4. Commit semântico
git commit -m "feat: adiciona suporte a nova variável X"

# 5. Push + Pull Request
git push origin feature/minha-melhoria
```

---

## 📄 Licença

Projeto interno — **Server MET v2.0**  
Desenvolvido para meteorologia e qualidade do ar 🌍

---

## 🙋 Suporte

- **Issues**: Abra no GitHub
- **Logs**: `journalctl -u server-met-api -f` (systemd) ou `docker-compose logs -f api`
- **Documentação API**: http://localhost:8000/docs (Swagger UI)

---

<div align="center">

**Feito com ☕ e 🌤️ para quem ama dados atmosféricos**

[🔝 Voltar ao topo](#-server-met-v20)

</div>