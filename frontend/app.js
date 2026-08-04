// Server MET v2.0 - Frontend Application
const API = '/api/v1';
const SURFACE_TYPES = ['surface', 'meanSea', 'atmosphere'];

const CATEGORY_LABELS = {
    pressure: 'Pressão',
    temperature: 'Temperatura',
    cloud: 'Nuvens',
    precipitation: 'Precipitação',
    humidity: 'Umidade',
    wind: 'Vento',
    pollution: 'Poluição',
};

let variables = [];
let regions = [];
let dates = [];

const $ = id => document.getElementById(id);

async function init() {
    await Promise.all([loadDashboard(), loadConfig(), loadMetarStations()]);
    wireEvents();
    autoSelect();
}

// ---------- Dashboard ----------
async function loadDashboard() {
    try {
        const res = await fetch(`${API}/data/dashboard`);
        const d = await res.json();
        $('dTotal').textContent = d.total_records;
        $('dVars').textContent = d.variables;
        $('dRegs').textContent = d.regions;
        $('dStations').textContent = (d.metar && d.metar.stations) || 0;
        $('dReports').textContent = (d.metar && d.metar.reports) || 0;

        $('dByVar').innerHTML = (d.by_variable || []).map(v =>
            `<tr><td>${v.variable}</td><td>${v.records}</td><td>${v.avg}</td></tr>`).join('');
        $('dByRegion').innerHTML = (d.by_region || []).map(r =>
            `<tr><td>${r.region}</td><td>${r.records}</td></tr>`).join('');
    } catch (e) {
        console.error('Dashboard load failed', e);
    }
}

// ---------- Configuration ----------
async function loadConfig() {
    const [varsRes, regsRes, availRes] = await Promise.all([
        fetch(`${API}/data/variables`),
        fetch(`${API}/data/regions`),
        fetch(`${API}/data/available`),
    ]);
    variables = (await varsRes.json()).variables;
    regions = (await regsRes.json()).regions;
    const avail = await availRes.json();
    dates = avail.dates || [];

    $('regSel').innerHTML = '<option value="">Selecione...</option>' +
        regions.map(r => `<option value="${r.code}">${r.code}</option>`).join('');
    $('dateSel').innerHTML = '<option value="">Mais recente</option>' +
        dates.map(d => `<option value="${d}">${formatDate(d)}</option>`).join('');

    renderVariables('');

    if (regions.length) $('regSel').value = regions[0].code;
    if (dates.length) $('dateSel').value = dates[0];
    $('anaSel').value = '00';
}

function renderVariables(category) {
    const filtered = variables.filter(v =>
        !category ||
        (category === 'pollution' ? v.category === 'pollution' : v.category !== 'pollution'));
    const opts = filtered.map(v => `<option value="${v.code}">${varLabel(v)}</option>`).join('');
    $('varSel').innerHTML = '<option value="">Selecione...</option>' + opts;
    $('varSel')._data = filtered;
    if (filtered.length) {
        $('varSel').value = filtered[0].code;
        onVarChange();
    }
}

function varLabel(v) {
    const cat = CATEGORY_LABELS[v.category] || v.category;
    return `${v.code} (${v.unit}) — ${cat}`;
}

function isSurface(v) {
    return v && SURFACE_TYPES.includes(v.level_type);
}

// ---------- Events ----------
function wireEvents() {
    $('categorySel').onchange = e => renderVariables(e.target.value);
    $('varSel').onchange = onVarChange;
    $('regSel').onchange = () => {};
    $('loadBtn').onclick = loadData;
    $('csvBtn').onclick = exportCSV;
    $('metarSel').onchange = loadMETAR;
}

function currentVar() {
    return variables.find(v => v.code === $('varSel').value);
}

async function onVarChange() {
    const v = currentVar();
    const levelGroup = $('levelGroup');
    const hint = $('varHint');
    hint.textContent = v ? (v.description || '') : '';
    if (v && isSurface(v)) {
        levelGroup.classList.add('hidden');
        $('levelSel').value = '';
    } else if (v) {
        levelGroup.classList.remove('hidden');
        await loadLevels(v.code);
    } else {
        levelGroup.classList.add('hidden');
    }
    if (v) await loadData();
}

async function loadLevels(varCode) {
    try {
        const res = await fetch(`${API}/data/levels/${varCode}`);
        const d = await res.json();
        const levels = (d.levels || []).sort((a, b) => b - a);
        $('levelSel').innerHTML = '<option value="">Selecione...</option>' +
            levels.map(l => `<option value="${l}">${l} hPa</option>`).join('');
        if (levels.length) $('levelSel').value = levels[0];
    } catch (e) {
        console.error(e);
    }
}

// ---------- Data + Map ----------
function params() {
    const v = currentVar();
    const p = new URLSearchParams();
    if (v && !isSurface(v) && $('levelSel').value) p.set('level', $('levelSel').value);
    if ($('regSel').value) p.set('region', $('regSel').value);
    if ($('dateSel').value) p.set('date', $('dateSel').value);
    if ($('anaSel').value) p.set('analysis', $('anaSel').value);
    return p;
}

async function loadData() {
    const v = currentVar();
    const region = $('regSel').value;
    if (!v || !region) return;

    $('loading').classList.remove('hidden');
    $('imgWrap').classList.add('hidden');
    $('imgErr').classList.add('hidden');
    $('loadBtn').disabled = true;

    const p = params();
    try {
        const url = `${API}/maps/${v.code}/${region}${p.toString() ? '?' + p : ''}`;
        const head = await fetch(url, { method: 'HEAD' });
        if (head.ok) {
            const img = $('mapImg');
            img.onload = () => { $('loading').classList.add('hidden'); $('imgWrap').classList.remove('hidden'); };
            img.onerror = () => { $('loading').classList.add('hidden'); $('imgErr').classList.remove('hidden'); };
            img.src = url;
            const lvl = $('levelSel').value;
            $('mapTitle').textContent = `${v.name} (${v.unit}) — ${region}`;
            $('mapMeta').textContent = `Nível: ${lvl ? lvl + ' hPa' : 'Superfície'} | Data: ${$('dateSel').value || 'última'} | Análise: ${$('anaSel').value}Z`;
        } else {
            $('loading').classList.add('hidden');
            $('imgErr').classList.remove('hidden');
        }

        // Statistics from SQLite
        const dp = new URLSearchParams({ variable: v.code, region });
        if (!isSurface(v) && $('levelSel').value) dp.set('level', $('levelSel').value);
        if ($('dateSel').value) dp.set('date', $('dateSel').value);
        if ($('anaSel').value) dp.set('analysis', $('anaSel').value);
        const res = await fetch(`${API}/data/?${dp}`);
        const data = await res.json();
        if (data.total) {
            const d0 = data.data[0];
            $('sMin').textContent = d0.min_value != null ? (+d0.min_value).toFixed(2) : '-';
            $('sMax').textContent = d0.max_value != null ? (+d0.max_value).toFixed(2) : '-';
            $('sMean').textContent = d0.mean_value != null ? (+d0.mean_value).toFixed(2) : '-';
            $('sDate').textContent = `${d0.data_date || ''} ${d0.analysis_time || ''}Z f${d0.forecast_hour || 0}`;
            $('statsPanel').classList.remove('hidden');
            $('csvBtn').disabled = false;
        }
    } catch (e) {
        console.error(e);
        $('loading').classList.add('hidden');
        $('imgErr').classList.remove('hidden');
    } finally {
        $('loadBtn').disabled = false;
    }
}

function exportCSV() {
    const v = currentVar();
    if (!v) return;
    const p = new URLSearchParams({ variable: v.code, region: $('regSel').value });
    if (!isSurface(v) && $('levelSel').value) p.set('level', $('levelSel').value);
    if ($('dateSel').value) p.set('date', $('dateSel').value);
    if ($('anaSel').value) p.set('analysis', $('anaSel').value);
    window.open(`${API}/data/export/csv?${p}`, '_blank');
}

// ---------- METAR ----------
async function loadMetarStations() {
    try {
        const res = await fetch(`${API}/metar/stations`);
        const d = await res.json();
        const opts = (d.stations || []).map(s =>
            `<option value="${s.code}">${s.code} — ${s.name || ''}</option>`).join('');
        $('metarSel').innerHTML = '<option value="">Selecione...</option>' + opts;
        if (d.stations && d.stations.length) {
            $('metarSel').value = d.stations[0].code;
            loadMETAR();
        }
    } catch (e) {
        console.error(e);
    }
}

async function loadMETAR() {
    const code = $('metarSel').value;
    $('metarRaw').textContent = '';
    $('metarDecoded').textContent = '';
    if (!code) return;
    $('metarRaw').textContent = 'Carregando...';
    try {
        const res = await fetch(`${API}/metar/${code}`);
        const d = await res.json();
        $('metarRaw').textContent = d.metar || 'SEM METAR';
        $('metarDecoded').textContent = d.decoded || 'Sem decodificação disponível';
    } catch (e) {
        $('metarRaw').textContent = 'Erro ao carregar METAR';
    }
}

// ---------- helpers ----------
function formatDate(s) {
    if (!s || s.length !== 8) return s;
    return `${s.slice(6, 8)}/${s.slice(4, 6)}/${s.slice(0, 4)}`;
}

function autoSelect() {
    const first = variables.find(v => v.category !== 'pollution');
    if (first) {
        $('varSel').value = first.code;
        onVarChange();
    }
}

document.addEventListener('DOMContentLoaded', init);