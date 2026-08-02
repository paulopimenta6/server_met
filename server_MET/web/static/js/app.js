/* MET Server — frontend do site meteorológico (v4). */
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

function dateToYmd(input) {
  if (!input || !input.value) return undefined;
  return input.value.replace(/-/g, "");
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
const REGIONS = [
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
  { value: "SA", label: "América do Sul" },
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
];

const VARIABLES = [
  { value: "temp", label: "Temperatura (nível)" },
  { value: "temps", label: "Temperatura (superfície)" },
  { value: "umidadeRel", label: "Umidade relativa" },
  { value: "nuvem", label: "Nebulosidade" },
  { value: "chuvaNaoConvec", label: "Chuva acumulada" },
  { value: "chuvaConvec", label: "Chuva convectiva" },
  { value: "ps", label: "Pressão na superfície" },
  { value: "prnm", label: "Pressão ao nível do mar" },
  { value: "wind", label: "Vento (nível)" },
  { value: "winds", label: "Vento (superfície)" },
];

function fillSelect(select, options) {
  select.innerHTML = "";
  options.forEach((o) => {
    const opt = document.createElement("option");
    opt.value = o.value;
    opt.textContent = o.label;
    select.appendChild(opt);
  });
}

["anim-region", "stat-region"].forEach((id) => fillSelect(el(id), REGIONS));
fillSelect(el("anim-variable"), VARIABLES);
fillSelect(el("stat-variable"), VARIABLES);

/* ------------------------------------------------- mapa interativo */
const map = L.map("interactive-map").setView([-15, -52], 4);
L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 18,
  attribution: "© OpenStreetMap",
}).addTo(map);

let pickMarker = null;
let picked = null;
map.on("click", (e) => {
  picked = { lon: e.latlng.lng, lat: e.latlng.lat };
  el("pick-lat").textContent = picked.lat.toFixed(4);
  el("pick-lon").textContent = picked.lon.toFixed(4);
  if (pickMarker) pickMarker.setLatLng(e.latlng);
  else pickMarker = L.marker(e.latlng).addTo(map);
});

/* ------------------------------------------------------------ mapas */
el("btn-generate-map").addEventListener("click", async () => {
  setBusy(el("btn-generate-map"));
  busy(el("btn-generate-map"), true);
  const container = el("map-results");
  container.innerHTML = "";
  try {
    const body = {
      variable: el("map-variable").value,
      level: parseInt(el("map-level").value, 10) || 500,
      region: el("map-region").value,
      date: dateToYmd(el("map-date")),
      analysis: el("map-analysis").value || null,
      forecast: el("map-forecast").value || null,
    };
    const data = await apiPost("/maps/generate", body);
    const figs = data.maps
      .map((p) => tmpUrl(p))
      .filter(Boolean)
      .map((url) => `<figure class="map-item"><img src="${url}" alt="Mapa GFS"></figure>`)
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
    const body = {
      variable: el("map-variable").value,
      level: parseInt(el("map-level").value, 10) || 500,
      lon: picked.lon,
      lat: picked.lat,
      date: dateToYmd(el("map-date")),
      analysis: el("map-analysis").value || null,
    };
    const data = await apiPost("/maps/generate", body);
    const figs = data.maps
      .map((p) => tmpUrl(p))
      .filter(Boolean)
      .map((url) => `<figure class="map-item"><img src="${url}" alt="Mapa GFS"></figure>`)
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
    const body = {
      variable: el("anim-variable").value,
      level: parseInt(el("anim-level").value, 10) || 500,
      region: el("anim-region").value,
      date: dateToYmd(el("anim-date")),
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
        <img src="${url}" alt="Animação GFS">
        <figcaption>GIF da previsão — atualize a página para reiniciar a animação.</figcaption>
      </figure>`;
  } catch (err) {
    showMsg(container, "Não foi possível gerar a animação: " + err.message, "err");
  } finally {
    busy(el("btn-generate-anim"), false);
  }
});

/* ----------------------------------------------------- estatísticas */
el("btn-generate-stats").addEventListener("click", async () => {
  setBusy(el("btn-generate-stats"));
  busy(el("btn-generate-stats"), true);
  const container = el("stat-results");
  container.innerHTML = "";
  try {
    const region = el("stat-region").value;
    const variable = el("stat-variable").value;
    const level = parseInt(el("stat-level").value, 10) || 500;
    const date = dateToYmd(el("stat-date"));
    const common = { region, variable, level, date };

    const summary = await apiPost("/analysis/summary", common);
    const series = await apiPost("/analysis/timeseries", common);
    const charts = await apiPost("/analysis/charts", {
      ...common,
      dpi: 130,
    });

    const cards = (summary.results || [])
      .map(
        (r) => `
        <div class="stat-card">
          <div class="k">Previsão +${String(r.forecast).padStart(2, "0")}h</div>
          <div class="v">${r.mean} ${r.units}</div>
          <div>média (min ${r.min} / máx ${r.max})</div>
        </div>`
      )
      .join("");

    const trend = series.trend || {};
    const trendText = trend.slope !== undefined
      ? `<div class="msg info">
           <strong>Tendência:</strong> ${trend.direction === "crescente" ? "subindo" :
             trend.direction === "decrescente" ? "caindo" : "estável"}
           (${trend.slope > 0 ? "+" : ""}${Number(trend.slope).toFixed(4)} un/hora).
           Confiança estatística: p-valor ${Number(trend.p_value).toFixed(4)} —
           ${trend.p_value < 0.05 ? "há indício forte de tendência" : "pouco indício"}.
           Qualidade do ajuste: R² ${Number(trend.r_squared).toFixed(3)}.
         </div>`
      : "";

    const chartFigs = (charts.charts || [])
      .map((p) => tmpUrl(p))
      .filter(Boolean)
      .map((url) => `<figure><img src="${url}" alt="Gráfico de análise"></figure>`)
      .join("");

    container.innerHTML = `
      ${trendText}
      <div class="stat-cards">${cards}</div>
      ${chartFigs ? `<div class="charts-grid">${chartFigs}</div>` : ""}
      <div class="msg info" style="margin-top:14px">Fonte: GFS (NOAA) · data ${summary.date || date || "hoje"} · análise ${summary.analysis || "auto"}</div>`;
  } catch (err) {
    showMsg(container, "Não foi possível calcular as estatísticas: " + err.message, "err");
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
