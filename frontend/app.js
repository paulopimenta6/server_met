// Server MET v2.0 - Frontend Application
const API_BASE = '/api/v1';

let map = null;
let dataLayer = null;
let timeSeriesChart = null;
let currentData = null;

document.addEventListener('DOMContentLoaded', async () => {
    initMap();
    initChart();
    await loadConfig();
    setupEventListeners();
});

function initMap() {
    map = L.map('map').setView([-15, -50], 4);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
    
    dataLayer = L.layerGroup().addTo(map);
}

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
        
        populateSelect('variableSelect', variables.map(v => ({value: v.code, text: `${v.name} (${v.unit})`})));
        populateSelect('regionSelect', regions.map(r => ({value: r.code, text: r.code})));
        populateSelect('dateSelect', available.dates.map(d => ({value: d, text: formatDate(d)})));
        
        document.getElementById('variableSelect').addEventListener('change', onVariableChange);
        document.getElementById('regionSelect').addEventListener('change', onRegionChange);
        
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
    
    if (!variable || !region) return;
    
    try {
        const res = await fetch(`${API_BASE}/data/levels/${variable}`);
        const data = await res.json();
        populateSelect('levelSelect', data.levels.map(l => ({value: l, text: `${l}`})));
    } catch (error) {
        console.error('Error loading levels:', error);
    }
}

async function onRegionChange() {
    const variable = document.getElementById('variableSelect').value;
    if (variable) await onVariableChange();
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
    
    if (!variable || !level || !region) {
        showError('Selecione variável, nível e região');
        return;
    }
    
    showLoading(true);
    hideError();
    
    try {
        const params = new URLSearchParams({
            variable, level, region,
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
        loadTimeSeries(variable, level, region);
        document.getElementById('exportBtn').disabled = false;
        
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
    
    if (data.csv_path) {
        loadMapLayer(data);
    }
}

async function loadMapLayer(data) {
    dataLayer.clearLayers();
    
    try {
        const res = await fetch(`${API_BASE}/maps/geojson/${data.variable_code}/${data.region_code}?level=${data.level_value}&date=${data.data_date}&analysis=${data.analysis_time}`);
        const geojson = await res.json();
        
        const variableInfo = await (await fetch(`${API_BASE}/data/variables`)).json();
        const varInfo = variableInfo.variables.find(v => v.code === data.variable_code);
        const unit = varInfo?.unit || '';
        
        L.geoJSON(geojson, {
            pointToLayer: (feature, latlng) => {
                const value = feature.properties.value;
                const intensity = normalizeValue(value, data.min_value, data.max_value);
                const color = getColor(intensity);
                
                return L.circleMarker(latlng, {
                    radius: 4,
                    fillColor: color,
                    color: '#fff',
                    weight: 0.5,
                    opacity: 1,
                    fillOpacity: 0.8
                });
            },
            onEachFeature: (feature, layer) => {
                layer.bindPopup(`
                    <strong>${feature.properties.variable}</strong><br>
                    Valor: ${feature.properties.value.toFixed(2)} ${unit}<br>
                    Nível: ${feature.properties.level} hPa<br>
                    Região: ${feature.properties.region}
                `);
            }
        }).addTo(dataLayer);
        
        if (geojson.bbox) {
            map.fitBounds([
                [geojson.bbox[1], geojson.bbox[0]],
                [geojson.bbox[3], geojson.bbox[2]]
            ]);
        }
        
        addLegend(data.min_value, data.max_value, unit);
        
    } catch (error) {
        console.error('Error loading map layer:', error);
    }
}

function addLegend(min, max, unit) {
    const legend = L.control({position: 'bottomright'});
    legend.onAdd = () => {
        const div = L.DomUtil.create('div', 'legend');
        div.innerHTML = `
            <div style="background: white; padding: 10px; border-radius: 4px; box-shadow: 0 1px 5px rgba(0,0,0,0.3);">
                <strong>${unit}</strong>
                <div style="display: flex; align-items: center; margin-top: 5px;">
                    <div style="width: 100px; height: 10px; background: linear-gradient(to right, #440154, #31688e, #35b779, #fde725);"></div>
                </div>
                <div style="display: flex; justify-content: space-between; width: 100px; margin-top: 2px; font-size: 11px;">
                    <span>${min?.toFixed(1) || 'Min'}</span>
                    <span>${max?.toFixed(1) || 'Max'}</span>
                </div>
            </div>
        `;
        return div;
    };
    legend.addTo(map);
}

async function loadTimeSeries(variable, level, region) {
    try {
        const res = await fetch(`${API_BASE}/data/?variable=${variable}&level=${level}&region=${region}&limit=50`);
        const data = await res.json();
        
        const labels = data.data.map(d => `${d.data_date} ${d.analysis_time}Z`).reverse();
        const values = data.data.map(d => d.mean_value).reverse();
        
        timeSeriesChart.data.labels = labels;
        timeSeriesChart.data.datasets = [{
            label: `${variable} (${level} hPa) - ${region}`,
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
        level: currentData.level_value,
        ...(currentData.data_date && { date: currentData.data_date }),
        ...(currentData.analysis_time && { analysis: currentData.analysis_time })
    });
    
    window.open(`${API_BASE}/data/export/csv?${params}`, '_blank');
}

function normalizeValue(value, min, max) {
    if (min === max) return 0.5;
    return Math.max(0, Math.min(1, (value - min) / (max - min)));
}

function getColor(intensity) {
    const colors = ['#440154', '#482878', '#3e4a89', '#31688e', '#26828e', '#1f9e89', '#35b779', '#6ece58', '#b5de2b', '#fde725'];
    const index = Math.floor(intensity * (colors.length - 1));
    return colors[Math.max(0, Math.min(index, colors.length - 1))];
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