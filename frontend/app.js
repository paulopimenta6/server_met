// Server MET v2.0 - Frontend Application (Lightweight)
const API_BASE = '/api/v1';

let timeSeriesChart = null;
let currentData = null;
let variablesCache = [];

// Surface variables (don't need level selection)
const SURFACE_VARIABLES = ['ps', 'prnm', 'temps', 'chuvaNaoConvec', 'chuvaConvec', 'pm25', 'pm10', 'aod'];

document.addEventListener('DOMContentLoaded', async () => {
    initChart();
    await loadConfig();
    setupEventListeners();
});

function initChart() {
    const ctx = document.getElementById('timeSeriesChart').getContext('2d');
    timeSeriesChart = new Chart(ctx, {
        type: 'line',
        data: { labels: [], datasets: [] },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: false, title: { display: true, text: 'Valor' } },
                x: { title: { display: true, text: 'Tempo' } }
            },
            plugins: {
                legend: { display: true, position: 'top' },
                title: { display: true, text: 'Série Temporal' }
            }
        }
    });
}

async function loadConfig() {
    try {
        const [varsRes, regionsRes, availRes] = await Promise.all([
            fetch(`${API_BASE}/data/variables`),
            fetch(`${API_BASE}/data/regions`),
            fetch(`${API_BASE}/data/available`)
        ]);
        
        const variables = (await varsRes.json()).variables;
        const regions = (await regionsRes.json()).regions;
        const available = await availRes.json();
        
        variablesCache = variables;
        
        populateSelect('variableSelect', variables.map(v => ({value: v.code, text: `${v.name} (${v.unit})`})));
        populateSelect('regionSelect', regions.map(r => ({value: r.code, text: r.code})));
        populateSelect('dateSelect', available.dates.map(d => ({value: d, text: formatDate(d)})));
        
        document.getElementById('variableSelect').addEventListener('change', onVariableChange);
        document.getElementById('regionSelect').addEventListener('change', onRegionChange);
        
        // Load METAR stations
        await loadMETARStations();
        
    } catch (error) {
        console.error('Error loading config:', error);
        showError('Erro ao carregar configurações');
    }
}

function populateSelect(selectId, options) {
    const select = document.getElementById(selectId);
    select.innerHTML = '<option value="">Selecione...</option>';
    options.forEach(opt => {
        const option = document.createElement('option');
        option.value = opt.value;
        option.textContent = opt.text;
        select.appendChild(option);
    });
}

async function onVariableChange() {
    const variable = document.getElementById('variableSelect').value;
    const region = document.getElementById('regionSelect').value;
    const levelGroup = document.getElementById('levelGroup');
    
    // Hide level selector for surface variables
    if (variable && SURFACE_VARIABLES.includes(variable)) {
        levelGroup.style.display = 'none';
        document.getElementById('levelSelect').value = '';
    } else {
        levelGroup.style.display = 'block';
        if (variable && region) {
            await loadLevels(variable);
        }
    }
    
    // Update image when variable changes
    if (variable && region) {
        await loadImage();
    }
}

async function onRegionChange() {
    const variable = document.getElementById('variableSelect').value;
    if (variable) {
        await onVariableChange();
        await loadImage();
    }
}

async function loadLevels(variable) {
    try {
        const res = await fetch(`${API_BASE}/data/levels/${variable}`);
        const data = await res.json();
        populateSelect('levelSelect', data.levels.map(l => ({value: l, text: `${l}`})));
    } catch (error) {
        console.error('Error loading levels:', error);
    }
}

function setupEventListeners() {
    document.getElementById('loadBtn').addEventListener('click', loadData);
    document.getElementById('exportBtn').addEventListener('click', exportCSV);
}

async function loadData() {
    const variable = document.getElementById('variableSelect').value;
    const level = document.getElementById('levelSelect').value;
    const region = document.getElementById('regionSelect').value;
    const date = document.getElementById('dateSelect').value;
    const analysis = document.getElementById('analysisSelect').value;
    
    // Check required fields (level only required for non-surface vars)
    const needsLevel = !SURFACE_VARIABLES.includes(variable);
    
    if (!variable || !region || (needsLevel && !level)) {
        showError(needsLevel ? 'Selecione variável, nível e região' : 'Selecione variável e região');
        return;
    }
    
    showLoading(true);
    hideError();
    
    try {
        const params = new URLSearchParams({
            variable, region,
            ...(level && { level }),
            ...(date && { date }),
            ...(analysis && { analysis })
        });
        
        const res = await fetch(`${API_BASE}/data/?${params}`);
        const data = await res.json();
        
        if (data.total === 0) {
            showError('Nenhum dado encontrado para os filtros selecionados');
            return;
        }
        
        currentData = data.data[0];
        displayData(currentData);
        loadTimeSeries(variable, level || 'sfc', region);
        document.getElementById('exportBtn').disabled = false;
        
        // Also load the pre-generated image
        await loadImage();
        
    } catch (error) {
        console.error('Error loading data:', error);
        showError('Erro ao carregar dados');
    } finally {
        showLoading(false);
    }
}

function displayData(data) {
    document.getElementById('statMin').textContent = data.min_value?.toFixed(2) || '-';
    document.getElementById('statMax').textContent = data.max_value?.toFixed(2) || '-';
    document.getElementById('statMean').textContent = data.mean_value?.toFixed(2) || '-';
    document.getElementById('statsPanel').classList.remove('hidden');
}

async function loadImage() {
    const variable = document.getElementById('variableSelect').value;
    const region = document.getElementById('regionSelect').value;
    const level = document.getElementById('levelSelect').value;
    const date = document.getElementById('dateSelect').value;
    const analysis = document.getElementById('analysisSelect').value;
    
    if (!variable || !region) return;
    
    const wrapper = document.getElementById('imageWrapper');
    const loading = document.getElementById('loading');
    const img = document.getElementById('mapImage');
    const error = document.getElementById('imageError');
    const title = document.getElementById('imageTitle');
    const meta = document.getElementById('imageMeta');
    
    loading.classList.remove('hidden');
    wrapper.classList.add('hidden');
    error.classList.add('hidden');
    
    try {
        const params = new URLSearchParams({
            ...(level && { level }),
            ...(date && { date }),
            ...(analysis && { analysis })
        });
        
        const res = await fetch(`${API_BASE}/maps/${variable}/${region}?${params}`, { method: 'HEAD' });
        
        if (res.ok) {
            // Build the full URL for the image
            const imgUrl = `${API_BASE}/maps/${variable}/${region}?${params}`;
            img.src = imgUrl;
            img.onload = () => {
                loading.classList.add('hidden');
                wrapper.classList.remove('hidden');
            };
            img.onerror = () => {
                loading.classList.add('hidden');
                error.classList.remove('hidden');
            };
            
            // Update title and meta
            const varInfo = variablesCache.find(v => v.code === variable);
            const levelText = level ? `${level} hPa` : 'Superfície';
            title.textContent = `${varInfo?.name || variable} - ${levelText} - ${region}`;
            meta.textContent = `Análise: ${analysis || '00'}Z | Data: ${formatDate(date || 'latest')} | Previsão: ${params.get('forecast') || '00'}h`;
        } else {
            loading.classList.add('hidden');
            error.classList.remove('hidden');
        }
    } catch (err) {
        console.error('Error loading image:', err);
        loading.classList.add('hidden');
        error.classList.remove('hidden');
    }
}

async function loadTimeSeries(variable, level, region) {
    try {
        const params = new URLSearchParams({ variable, region, limit: '50' });
        if (level) params.append('level', level);
        
        const res = await fetch(`${API_BASE}/data/?${params}`);
        const data = await res.json();
        
        const labels = data.data.map(d => `${d.data_date} ${d.analysis_time}Z`).reverse();
        const values = data.data.map(d => d.mean_value).reverse();
        
        const levelText = level ? `${level} hPa` : 'Superfície';
        
        timeSeriesChart.data.labels = labels;
        timeSeriesChart.data.datasets = [{
            label: `${variable} (${levelText}) - ${region}`,
            data: values,
            borderColor: '#31688e',
            backgroundColor: 'rgba(49, 104, 142, 0.1)',
            fill: true,
            tension: 0.2
        }];
        timeSeriesChart.update();
        
    } catch (error) {
        console.error('Error loading time series:', error);
    }
}

async function exportCSV() {
    if (!currentData) return;
    
    const params = new URLSearchParams({
        variable: currentData.variable_code,
        region: currentData.region_code,
        ...(currentData.level_value && { level: currentData.level_value }),
        ...(currentData.data_date && { date: currentData.data_date }),
        ...(currentData.analysis_time && { analysis: currentData.analysis_time })
    });
    
    window.open(`${API_BASE}/data/export/csv?${params}`, '_blank');
}

// METAR functionality
async function loadMETARStations() {
    try {
        const res = await fetch(`${API_BASE}/metar/stations`);
        const data = await res.json();
        
        if (data.stations) {
            const select = document.getElementById('metarStationSelect');
            select.innerHTML = '<option value="">Selecione estação...</option>';
            
            data.stations.forEach(station => {
                const option = document.createElement('option');
                option.value = station.code;
                option.textContent = `${station.code} - ${station.name}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading METAR stations:', error);
    }
}

async function loadMETAR() {
    const station = document.getElementById('metarStationSelect').value;
    const output = document.getElementById('metarData');
    
    if (!station) {
        output.textContent = '';
        return;
    }
    
    output.textContent = 'Carregando...';
    
    try {
        const res = await fetch(`${API_BASE}/metar/${station}`);
        const data = await res.json();
        
        if (data.metar) {
            output.textContent = `${data.station}\n${data.time}\n${data.metar}`;
        } else {
            output.textContent = 'METAR não disponível';
        }
    } catch (error) {
        output.textContent = 'Erro ao carregar METAR';
    }
}

function formatDate(dateStr) {
    if (!dateStr || dateStr.length !== 8) return dateStr;
    return `${dateStr.slice(6,8)}/${dateStr.slice(4,6)}/${dateStr.slice(0,4)}`;
}

function showLoading(show) {
    document.getElementById('loading').classList.toggle('hidden', !show);
    document.getElementById('loadBtn').disabled = show;
}

function showError(msg) {
    const el = document.getElementById('loading');
    el.textContent = msg;
    el.classList.remove('hidden');
    el.style.color = '#e74c3c';
}

function hideError() {
    const el = document.getElementById('loading');
    el.classList.add('hidden');
    el.style.color = 'inherit';
}