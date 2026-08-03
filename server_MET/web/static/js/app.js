/* MET Server — frontend do site meteorológico (v4.2). */
"use strict";

/* ---------------------------------------------------------------- utils */
function apiUrl(path) { return path; }

async function apiPost(path, body) {
  const res = await fetch(apiUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Erro ${res.status}`);
  return data;
}

async function apiGet(path) {
  const res = await fetch(apiUrl(path));
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || `Erro ${res.status}`);
  return data;
}

/* Converte caminho absoluto (data/tmp/...) em URL servível /files/tmp/... */
function tmpUrl(serverPath) {
  const m = String(serverPath).match(/\/tmp\/(.+)$/);
  return m ? "/files/tmp/" + m[1] : null;
}

/* Converte caminho absoluto (data/analise/...) em URL servível /files/analise/... */
function analiseUrl(serverPath) {
  const m = String(serverPath).match(/\/analise\/(.+)$/);
  return m ? "/files/analise/" + m[1] : null;
}

function el(id) { return document.getElementById(id); }

function showMsg(container, text, kind) {
  container.innerHTML = `<div class="msg ${kind}">${text}</div>`;
}

function busy(btn, on) {
  btn.disabled = on;
  btn.innerHTML = on
    ? '<span class="spinner"></span> Aguarde…'
    : btn.dataset.label || btn.textContent;
}

function setBusy(btn) {
  if (!btn.dataset.label) btn.dataset.label = btn.innerHTML;
}

/* ---------------------------------------------------------------- abas */
document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById("tab-" + tab.dataset.tab).classList.add("active");
  });
});

/* ---------------------------------------------------------------- dados */
const REGION_GROUPS = [
  {
    label: "Estados (Brasil)",
    options: [
      { value: "SP", label: "São Paulo" },
      { value: "RJ", label: "Rio de Janeiro" },
      { value: "AM", label: "Amazonas" },
      { value: "DF", label: "Distrito Federal" },
      { value: "PR", label: "Paraná" },
      { value: "RS", label: "Rio Grande do Sul" },
      { value: "MG", label: "Minas Gerais" },
      { value: "PA", label: "Pará" },
      { value: "PE", label: "Pernambuco" },
      { value: "CE", label: "Ceará" },
    ],
  },
  {
    label: "América do Sul",
    options: [
      { value: "SA", label: "América do Sul (visão geral)" },
      { value: "BR", label: "Brasil" },
      { value: "AR", label: "Argentina" },
      { value: "BO", label: "Bolívia" },
      { value: "CL", label: "Chile" },
      { value: "CO", label: "Colômbia" },
      { value: "EC", label: "Equador" },
      { value: "GY", label: "Guiana" },
      { value: "PY", label: "Paraguai" },
      { value: "PEU", label: "Peru" },
      { value: "SR", label: "Suriname" },
      { value: "UY", label: "Uruguai" },
      { value: "VE", label: "Venezuela" },
    ],
  },
  {
    label: "Cidades",
    options: [
      { value: "SP-CIDADE", label: "São Paulo (cidade)" },
      { value: "RJ-CIDADE", label: "Rio de Janeiro (cidade)" },
      { value: "AM-CIDADE", label: "Manaus (cidade)" },
      { value: "DF-CIDADE", label: "Brasília (cidade)" },
      { value: "PR-CIDADE", label: "Curitiba (cidade)" },
      { value: "RS-CIDADE", label: "Porto Alegre (cidade)" },
      { value: "MG-CIDADE", label: "Belo Horizonte (cidade)" },
      { value: "PA-CIDADE", label: "Belém (cidade)" },
      { value: "PE-CIDADE", label: "Recife (cidade)" },
      { value: "CE-CIDADE", label: "Fortaleza (cidade)" },
    ],
  },
];

const VARIABLE_GROUPS = [
  {
    label: "Temperatura e umidade",
    options: [
      { value: "temp", label: "Temperatura (nível de pressão)" },
      { value: "temps2m", label: "Temperatura a 2 m" },
      { value: "temps", label: "Temperatura na superfície" },
      { value: "dewpoint2m", label: "Ponto de orvalho a 2 m" },
      { value: "aparente", label: "Temperatura aparente" },
      { value: "rh2m", label: "Umidade relativa a 2 m" },
      { value: "umidadeRel", label: "Umidade relativa (nível)" },
    ],
  },
  {
    label: "Vento",
    options: [
      { value: "wind", label: "Vento (nível de pressão)" },
      { value: "winds", label: "Vento na superfície (10 m)" },
      { value: "u", label: "Vento componente U (nível)" },
      { value: "v", label: "Vento componente V (nível)" },
      { value: "uSupe", label: "Vento componente U (10 m)" },
      { value: "vSupe", label: "Vento componente V (10 m)" },
      { value: "vento10u", label: "Vento U a 10 m" },
      { value: "vento10v", label: "Vento V a 10 m" },
      { value: "vento100u", label: "Vento U a 100 m" },
      { value: "vento100v", label: "Vento V a 100 m" },
      { value: "rajada", label: "Rajada de vento" },
    ],
  },
  {
    label: "Precipitação e nuvens",
    options: [
      { value: "chuvaNaoConvec", label: "Chuva acumulada" },
      { value: "chuvaConvec", label: "Chuva convectiva" },
      { value: "precipitacao", label: "Taxa de precipitação" },
      { value: "nuvem", label: "Nebulosidade total" },
      { value: "nuvemTot", label: "Nebulosidade total (coluna)" },
      { value: "aguaPrecipitavel", label: "Água precipitável" },
      { value: "neve", label: "Profundidade de neve" },
    ],
  },
  {
    label: "Pressão e visibilidade",
    options: [
      { value: "ps", label: "Pressão na superfície" },
      { value: "prnm", label: "Pressão ao nível do mar" },
      { value: "visibilidade", label: "Visibilidade" },
      { value: "ventilacao", label: "Ventilação" },
    ],
  },
  {
    label: "Instabilidade e severidade",
    options: [
      { value: "cape", label: "CAPE (energia potencial)" },
      { value: "cin", label: "CIN (inibição convectiva)" },
      { value: "indiceLift", label: "Índice de levantamento" },
      { value: "helicidade", label: "Helicidade relativa à tempestade" },
      { value: "indiceHaines", label: "Índice de Haines" },
    ],
  },
  {
    label: "Poluição do ar",
    options: [
      { value: "ozonio", label: "Ozônio (nível)" },
      { value: "ozonioTot", label: "Ozônio total (coluna)" },
    ],
  },
  {
    label: "Atmosfera (níveis médios e altos)",
    options: [
      { value: "gh", label: "Altura geopotencial (nível)" },
      { value: "omega", label: "Velocidade vertical (nível)" },
      { value: "vortabs", label: "Vorticidade absoluta (nível)" },
      { value: "temp", label: "Temperatura (nível)" },
      { value: "umidadeRel", label: "Umidade relativa (nível)" },
      { value: "u", label: "Vento U (nível)" },
      { value: "v", label: "Vento V (nível)" },
      { value: "ozonio", label: "Ozônio (nível)" },
    ],
  },
];

/* Variáveis que aceitam nível de pressão (mesmas de server_MET.processor.LEVELED_VARIABLES).
   É reforçado pela resposta de /variables quando disponível. */
const LEVELED_VARS = new Set([
  "temp", "umidadeRel", "u", "v", "ozonio", "gh", "omega", "vortabs", "wind",
]);

/* Níveis padrão de pressão (hPa) para o seletor; substituído por /catalog/levels. */
let STANDARD_LEVELS = [100, 150, 200, 250, 300, 400, 500, 600, 700, 850, 925, 1000];
let leveledMap = {};

function fillSelect(select, groups, withEmpty) {
  select.innerHTML = "";
  if (withEmpty) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = withEmpty === true ? "—" : withEmpty;
    select.appendChild(opt);
  }
  groups.forEach((g) => {
    const group = document.createElement("optgroup");
    group.label = g.label;
    g.options.forEach((o) => {
      const opt = document.createElement("option");
      opt.value = o.value;
      opt.textContent = o.label;
      group.appendChild(opt);
    });
    select.appendChild(group);
  });
}

["map-region", "anim-region", "stat-region"].forEach((id) => fillSelect(el(id), REGION_GROUPS));
["map-variable", "anim-variable", "stat-variable"].forEach((id) => fillSelect(el(id), VARIABLE_GROUPS));

/* --------------------------------------------------- níveis (por variável) */
function isLeveled(variable) {
  if (leveledMap[variable] !== undefined) return leveledMap[variable] === true;
  return LEVELED_VARS.has(variable);
}

function fillLevelSelect(prefix, variable) {
  const sel = el(prefix + "-level");
  const hint = el(prefix + "-level-hint");
  sel.innerHTML = "";
  if (isLeveled(variable)) {
    STANDARD_LEVELS.forEach((lv) => {
      const opt = document.createElement("option");
      opt.value = lv;
      opt.textContent = lv + " hPa";
      if (lv === 500) opt.selected = true;
      sel.appendChild(opt);
    });
    sel.disabled = false;
    if (hint) hint.textContent = "Nível de pressão (altitude do mapa)";
  } else {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "Superfície";
    sel.appendChild(opt);
    sel.disabled = true;
    if (hint) hint.textContent = "Variável de superfície — nível não se aplica";
  }
}

function levelValueFor(prefix, variable) {
  if (!isLeveled(variable)) return null;
  const v = parseInt(el(prefix + "-level").value, 10);
  return Number.isFinite(v) ? v : 500;
}

function bindLevelSelector(prefix) {
  const varSel = el(prefix + "-variable");
  fillLevelSelect(prefix, varSel.value);
  varSel.addEventListener("change", () => fillLevelSelect(prefix, varSel.value));
}
["map", "anim", "stat"].forEach(bindLevelSelector);

/* ------------------------------------------- ciclos (data/análise/previsão) */
let cycles = [];

function fmtDate(ymd) {
  if (!ymd || ymd.length !== 8) return ymd;
  return `${ymd.slice(0, 4)}-${ymd.slice(4, 6)}-${ymd.slice(6, 8)}`;
}

function cyclesForDate(date) {
  return cycles.filter((c) => c.date === date);
}

function populateDateSelect(prefix) {
  const sel = el(prefix + "-date");
  sel.innerHTML = "";
  const auto = document.createElement("option");
  auto.value = "";
  auto.textContent = "Mais recente";
  sel.appendChild(auto);

  const dates = [...new Set(cycles.map((c) => c.date))].sort().reverse();
  if (!dates.length) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "— (sem dados ainda)";
    sel.appendChild(opt);
  }
  dates.forEach((d) => {
    const opt = document.createElement("option");
    opt.value = d;
    opt.textContent = fmtDate(d);
    sel.appendChild(opt);
  });
}

function populateAnalysisSelect(prefix) {
  const date = el(prefix + "-date").value;
  const sel = el(prefix + "-analysis");
  sel.innerHTML = "";
  const auto = document.createElement("option");
  auto.value = "";
  auto.textContent = "Automática";
  sel.appendChild(auto);
  const horas = [...new Set(cyclesForDate(date).map((c) => c.analysis))].sort();
  horas.forEach((h) => {
    const opt = document.createElement("option");
    opt.value = h;
    opt.textContent = h + " Z";
    sel.appendChild(opt);
  });
}

function populateForecastSelect(prefix) {
  const date = el(prefix + "-date").value;
  const analysis = el(prefix + "-analysis").value;
  const sel = el(prefix + "-forecast");
  if (!sel) return;
  sel.innerHTML = "";
  const all = document.createElement("option");
  all.value = "";
  all.textContent = "Todas as disponíveis";
  sel.appendChild(all);

  let matches = cyclesForDate(date);
  if (analysis) matches = matches.filter((c) => c.analysis === analysis);
  const hours = [...new Set(matches.flatMap((c) => c.forecast_hours || []))].sort();
  hours.forEach((h) => {
    const opt = document.createElement("option");
    opt.value = h;
    opt.textContent = "+" + h + "h";
    sel.appendChild(opt);
  });
}

function bindCycleSelectors(prefix) {
  const dateSel = el(prefix + "-date");
  const anaSel = el(prefix + "-analysis");
  dateSel.addEventListener("change", () => {
    populateAnalysisSelect(prefix);
    populateForecastSelect(prefix);
  });
  anaSel.addEventListener("change", () => populateForecastSelect(prefix));
}

["map", "anim", "stat"].forEach(bindCycleSelectors);

/* ------------------------------------------------- mapa interativo */
let picked = null;
if (document.getElementById("interactive-map") && typeof L !== "undefined") {
  const map = L.map("interactive-map").setView([-15, -52], 4);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: "© OpenStreetMap",
  }).addTo(map);

  let pickMarker = null;
  map.on("click", (e) => {
    picked = { lon: e.latlng.lng, lat: e.latlng.lat };
    el("pick-lat").textContent = picked.lat.toFixed(4);
    el("pick-lon").textContent = picked.lon.toFixed(4);
    if (pickMarker) pickMarker.setLatLng(e.latlng);
    else pickMarker = L.marker(e.latlng).addTo(map);
  });
}

/* ------------------------------------------------------------ mapas */
el("btn-generate-map").addEventListener("click", async () => {
  setBusy(el("btn-generate-map"));
  busy(el("btn-generate-map"), true);
  const container = el("map-results");
  container.innerHTML = "";
  try {
    const variable = el("map-variable").value;
    const body = {
      variable,
      level: levelValueFor("map", variable),
      region: el("map-region").value,
      date: el("map-date").value || null,
      analysis: el("map-analysis").value || null,
      forecast: el("map-forecast").value || null,
    };
    const data = await apiPost("/maps/generate", body);
    const figs = data.maps
      .map((p) => tmpUrl(p))
      .filter(Boolean)
      .map((url) => `<figure class="map-item"><img src="${url}" alt="Mapa meteorológico GFS"></figure>`)
      .join("");
    container.innerHTML =
      `<div class="msg ok">${data.count} mapa(s) gerado(s).</div>` + figs;
  } catch (err) {
    showMsg(container, "Não foi possível gerar o mapa: " + err.message, "err");
  } finally {
    busy(el("btn-generate-map"), false);
  }
});

el("btn-use-coords").addEventListener("click", async () => {
  if (!picked) {
    showMsg(el("map-results"), "Clique no mapa para escolher um ponto primeiro.", "info");
    return;
  }
  setBusy(el("btn-use-coords"));
  busy(el("btn-use-coords"), true);
  const container = el("map-results");
  container.innerHTML = "";
  try {
    const variable = el("map-variable").value;
    const body = {
      variable,
      level: levelValueFor("map", variable),
      lon: picked.lon,
      lat: picked.lat,
      date: el("map-date").value || null,
      analysis: el("map-analysis").value || null,
    };
    const data = await apiPost("/maps/generate", body);
    const figs = data.maps
      .map((p) => tmpUrl(p))
      .filter(Boolean)
      .map((url) => `<figure class="map-item"><img src="${url}" alt="Mapa meteorológico GFS"></figure>`)
      .join("");
    container.innerHTML =
      `<div class="msg ok">Mapa centrado em ${picked.lat.toFixed(3)}, ${picked.lon.toFixed(3)}.</div>` + figs;
  } catch (err) {
    showMsg(container, "Não foi possível gerar o mapa: " + err.message, "err");
  } finally {
    busy(el("btn-use-coords"), false);
  }
});

/* -------------------------------------------------------- animações */
el("btn-generate-anim").addEventListener("click", async () => {
  setBusy(el("btn-generate-anim"));
  busy(el("btn-generate-anim"), true);
  const container = el("anim-results");
  container.innerHTML = "";
  try {
    const qs = new URLSearchParams({
      duration_ms: el("anim-speed").value,
    });
    const fc = el("anim-forecast").value;
    if (fc) qs.set("forecast_hours", fc);
    const variable = el("anim-variable").value;
    const body = {
      variable,
      level: levelValueFor("anim", variable),
      region: el("anim-region").value,
      date: el("anim-date").value || null,
      analysis: el("anim-analysis").value || null,
    };
    const res = await fetch(`/maps/animate?${qs}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || `Erro ${res.status}`);
    const url = tmpUrl(data.gif);
    if (!url) throw new Error("Caminho da animação não reconhecido");
    container.innerHTML = `
      <div class="msg ok">Animação gerada com sucesso.</div>
      <figure class="gif-item">
        <img src="${url}" alt="Animação GIF da previsão meteorológica">
        <figcaption>GIF da previsão — atualize a página para reiniciar a animação.</figcaption>
      </figure>`;
  } catch (err) {
    showMsg(container, "Não foi possível gerar a animação: " + err.message, "err");
  } finally {
    busy(el("btn-generate-anim"), false);
  }
});

/* ---------------------------------------------------- dashboard */
function esc(v) {
  return v === null || v === undefined || v === "" ? "—" : v;
}

function num(v, d = 2) {
  return v === null || v === undefined || Number.isNaN(Number(v)) ? "—" : Number(v).toFixed(d);
}

function summaryCards(rows) {
  return (rows || [])
    .map(
      (r) => `
        <div class="stat-card">
          <div class="k">Previsão +${String(r.forecast).padStart(2, "0")}h</div>
          <div class="v">${num(r.mean)} ${esc(r.units)}</div>
          <div>média (min ${num(r.min)} / máx ${num(r.max)})</div>
        </div>`
    )
    .join("");
}

function summaryTable(rows) {
  const thead = `
    <tr>
      <th>Previsão</th><th>n</th><th>Mín</th><th>Máx</th><th>Média</th><th>Mediana</th>
      <th>Desvio</th><th>IQR</th><th>p5</th><th>p25</th><th>p75</th><th>p95</th><th>Assimetria</th>
    </tr>`;
  const tbody = (rows || [])
    .map(
      (r) => `
        <tr>
          <td>+${String(r.forecast).padStart(2, "0")}h</td>
          <td>${esc(r.n_points)}</td>
          <td>${num(r.min)}</td><td>${num(r.max)}</td><td>${num(r.mean)}</td>
          <td>${num(r.median)}</td><td>${num(r.std)}</td><td>${num(r.iqr)}</td>
          <td>${num(r.p5)}</td><td>${num(r.p25)}</td><td>${num(r.p75)}</td>
          <td>${num(r.p95)}</td><td>${num(r.skewness)}</td>
        </tr>`
    )
    .join("");
  return `<div class="table-wrap"><table class="data-table">
    <thead>${thead}</thead><tbody>${tbody}</tbody></table></div>`;
}

function trendPanel(trend) {
  if (!trend || trend.slope === null || trend.slope === undefined) {
    return `<div class="trend-panel"><strong>Tendência:</strong> ${trend && trend.note ? trend.note : "indisponível (menos de 2 pontos)."}</div>`;
  }
  const dir =
    trend.direction === "crescente" ? "subindo" :
    trend.direction === "decrescente" ? "caindo" : "estável";
  const ci =
    trend.slope_ci && trend.slope_ci[0] !== null && trend.slope_ci[1] !== null
      ? ` (IC 95%: ${num(trend.slope_ci[0], 6)} a ${num(trend.slope_ci[1], 6)})`
      : "";
  const jb =
    trend.jarque_bera_p !== null && trend.jarque_bera_p !== undefined
      ? ` — resíduos normais? p(Jarque-Bera) ${num(trend.jarque_bera_p, 4)}`
      : "";
  return `<div class="trend-panel">
    <strong>Tendência:</strong> ${dir} (${trend.slope > 0 ? "+" : ""}${num(trend.slope, 6)} un/hora${ci}).
    Confiança: p-valor ${num(trend.p_value, 6)} — ${trend.significant ? "há indício forte de tendência" : "pouco indício"}.
    Qualidade do ajuste: R² ${num(trend.r_squared, 4)}.${jb}
  </div>`;
}

el("btn-generate-stats").addEventListener("click", async () => {
  setBusy(el("btn-generate-stats"));
  busy(el("btn-generate-stats"), true);
  const container = el("stat-results");
  container.innerHTML = "";
  try {
    const region = el("stat-region").value;
    const variable = el("stat-variable").value;
    const level = levelValueFor("stat", variable);
    const common = {
      region,
      variable,
      level,
      date: el("stat-date").value || null,
      analysis: el("stat-analysis").value || null,
    };

    const dash = await apiPost("/analysis/dashboard", common);
    const charts = await apiPost("/analysis/charts", { ...common, dpi: 130 });

    const trendHtml = trendPanel(dash.trend);
    const cardsHtml = `<div class="stat-cards">${summaryCards(dash.summary)}</div>`;
    const tableHtml = summaryTable(dash.summary);

    const chartFigs = (charts.charts || [])
      .map((p) => tmpUrl(p))
      .filter(Boolean)
      .map((url) => `<figure><img src="${url}" alt="Gráfico de análise meteorológica"></figure>`)
      .join("");

    const csvUrl = dash.csv ? analiseUrl(dash.csv) : null;
    const toolsHtml = `
      <div class="dash-tools">
        ${csvUrl ? `<a class="btn" href="${csvUrl}" download>⬇ Baixar estatísticas (CSV)</a>` : ""}
        <a class="btn" href="/analysis/statistics?region=${region}&variable=${variable}&date=${dash.date || ""}&analysis=${dash.analysis || ""}" target="_blank">Ver no banco (API)</a>
        <span class="hint-inline">Fonte: GFS (NOAA) · data ${dash.date || "hoje"} · análise ${dash.analysis || "auto"} · nível ${level ?? "superfície"}</span>
      </div>`;

    container.innerHTML = `
      ${trendHtml}
      <div style="margin-top:16px">${cardsHtml}</div>
      ${chartFigs ? `<div class="charts-grid">${chartFigs}</div>` : ""}
      ${tableHtml}
      ${toolsHtml}
      <div class="msg info" style="margin-top:14px">Dados gravados no banco (tabela <code>statistics</code>) e em arquivo CSV servido pela API REST.</div>`;
  } catch (err) {
    showMsg(container, "Não foi possível gerar o dashboard: " + err.message, "err");
  } finally {
    busy(el("btn-generate-stats"), false);
  }
});

/* ------------------------------------------------------------- METAR */
async function refreshMetar() {
  setBusy(el("btn-refresh-metar"));
  busy(el("btn-refresh-metar"), true);
  const container = el("metar-results");
  container.innerHTML = "";
  try {
    const data = await apiGet("/metar/all");
    const rows = (data.metars || [])
      .map((m) => {
        const p = m.parsed || {};
        const t = p.temperatures || {};
        const wind = p.wind || {};
        const vis = p.visibility || {};
        const obs =
          (m.metadata && (m.metadata.obsTime || m.metadata.reportTime)) ||
          m.timestamp ||
          "";
        return `<tr>
          <td><strong>${m.region || "—"}</strong></td>
          <td>${m.station}</td>
          <td>${obs}</td>
          <td>${wind.direction ?? "—"}° ${wind.speed ?? "—"} kt</td>
          <td>${vis.miles ?? vis.value ?? "—"}</td>
          <td>${t.air ?? "—"}°C / ${t.dew_point ?? "—"}°C</td>
        </tr>`;
      })
      .join("");
    container.innerHTML = `
      <div class="msg ok">${data.count} estações consultadas.</div>
      <table class="data-table">
        <thead><tr><th>Região</th><th>ICAO</th><th>Observação</th><th>Vento</th><th>Visibilidade</th><th>Temp/Rocío</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>`;
  } catch (err) {
    showMsg(container, "Não foi possível obter os METARs: " + err.message, "err");
  } finally {
    busy(el("btn-refresh-metar"), false);
  }
}
el("btn-refresh-metar").addEventListener("click", refreshMetar);
refreshMetar();

/* ------------------------------------------------------- bootstrap (catálogo) */
async function loadCatalog() {
  try {
    const vars = await apiGet("/variables");
    leveledMap = {};
    (vars.variables || []).forEach((v) => {
      leveledMap[v.key] = v.leveled === true;
    });
  } catch (e) {
    /* offline: usa o conjunto estático LEVELED_VARS */
  }
  try {
    const levels = await apiGet("/levels");
    if (levels.levels && levels.levels.length) STANDARD_LEVELS = levels.levels;
  } catch (e) { /* mantém STANDARD_LEVELS padrão */ }
  try {
    const cat = await apiGet("/catalog/cycles");
    cycles = cat.cycles || [];
  } catch (e) {
    cycles = [];
  }
  ["map", "anim", "stat"].forEach((prefix) => {
    populateDateSelect(prefix);
    populateAnalysisSelect(prefix);
    populateForecastSelect(prefix);
    fillLevelSelect(prefix, el(prefix + "-variable").value);
  });
}
loadCatalog();

/* ------------------------------------------------------------ health */
(async () => {
  try {
    const h = await apiGet("/health");
    const ok = h.status === "ok" || h.status === "healthy";
    el("health-status").textContent = ok
      ? `OK (v${h.version})`
      : h.status || "indisponível";
    el("health-status").style.color = ok ? "#2f9e44" : "#e8590c";
  } catch {
    el("health-status").textContent = "indisponível";
  }
})();
