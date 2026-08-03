// MET Server - Frontend Application

class METServerApp {
    constructor() {
        this.baseURL = '';
        this.variables = [];
        this.regions = [];
        this.catalog = {};
        this.currentMapPath = null;
        this.currentAnimPath = null;
        this.init();
    }

    async init() {
        await this.loadConfig();
        this.setupEventListeners();
        this.setupTabs();
        this.startStatusCheck();
    }

    async loadConfig() {
        try {
            const [varsRes, regionsRes, cyclesRes] = await Promise.all([
                fetch('/variables'),
                fetch('/regions'),
                fetch('/catalog/cycles')
            ]);

            const varsData = await varsRes.json();
            const regionsData = await regionsRes.json();
            const cyclesData = await cyclesRes.json();

            this.variables = varsData.variables || [];
            this.regions = regionsData.regions || [];
            this.cycles = cyclesData.cycles || [];
            this.latestCycle = cyclesData.latest || null;

            this.populateVariables();
            this.populateRegions();
            this.populateCycles();
            this.updateDateInputs();
            this.updateLastUpdate();
        } catch (error) {
            console.error('Erro ao carregar configuração:', error);
            this.showToast('Erro ao carregar configuração do servidor', 'error');
        }
    }

    populateVariables() {
        const selects = [
            'mapVariable', 'animVariable', 'dashVariable', 'anaVariable'
        ];

        selects.forEach(id => {
            const select = document.getElementById(id);
            if (!select) return;

            this.variables.forEach(v => {
                const opt = document.createElement('option');
                opt.value = v.key;
                opt.textContent = `${v.label} (${v.unit})`;
                opt.dataset.hasLevel = v.has_level;
                opt.dataset.levelType = v.level_type;
                select.appendChild(opt);
            });
        });

        // Adiciona event listeners para mudança de variável
        ['mapVariable', 'animVariable', 'dashVariable', 'anaVariable'].forEach(id => {
            const select = document.getElementById(id);
            if (select) {
                select.addEventListener('change', () => this.updateLevels(id));
            }
        });

        // Popula níveis iniciais
        ['mapVariable', 'animVariable', 'dashVariable', 'anaVariable'].forEach(id => {
            const select = document.getElementById(id);
            if (select) this.updateLevels(id);
        });
    }

    updateLevels(triggerId) {
        const select = document.getElementById(triggerId);
        const option = select.options[select.selectedIndex];
        const hasLevel = option?.dataset?.hasLevel === 'true';
        const levelType = option?.dataset?.levelType;

        const levelSelects = {
            'mapVariable': 'mapLevel',
            'animVariable': 'animLevel',
            'dashVariable': 'dashLevel',
            'anaVariable': 'anaLevel'
        };

        const levelSelectId = levelSelects[triggerId];
        if (!levelSelectId) return;

        const levelSelect = document.getElementById(levelSelectId);
        levelSelect.innerHTML = '<option value="">Selecione...</option>';

        if (hasLevel) {
            // Níveis isobáricos principais
            const levels = [1000, 925, 850, 700, 500, 300, 250, 200, 150, 100, 50, 30, 20, 10, 5, 2, 1];
            levels.forEach(l => {
                const opt = document.createElement('option');
                opt.value = l;
                opt.textContent = `${l} hPa`;
                if (l === 500) opt.selected = true; // Default 500 hPa
                levelSelect.appendChild(opt);
            });
            levelSelect.disabled = false;
        } else {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = 'Superfície (sem nível)';
            opt.selected = true;
            levelSelect.appendChild(opt);
            levelSelect.disabled = true;
        }
    }

    populateRegions() {
        const selects = ['mapRegion', 'animRegion', 'dashRegion', 'anaRegion'];

        selects.forEach(id => {
            const select = document.getElementById(id);
            if (!select) return;

            this.regions.forEach(r => {
                const opt = document.createElement('option');
                opt.value = r.name;
                opt.textContent = `${r.full_name || r.name} (${r.kind})`;
                select.appendChild(opt);
            });

            // Default para SP
            if (select.options.length > 0) {
                select.value = 'SP';
            }
        });

        // METAR usa regiões com aeródromo ICAO cadastrado
        const metarSelect = document.getElementById('metarRegion');
        if (metarSelect) {
            this.regions.forEach(r => {
                if (!r.icao) return;
                const opt = document.createElement('option');
                opt.value = r.icao;
                opt.textContent = `${r.full_name || r.name} (${r.icao})`;
                metarSelect.appendChild(opt);
            });
        }
    }

    populateCycles() {
        // Ordena ciclos do mais recente para o mais antigo
        const sorted = [...this.cycles].sort((a, b) =>
            `${b.date}_${b.analysis}`.localeCompare(`${a.date}_${a.analysis}`)
        );

        const dateInputs = ['mapDate', 'animDate', 'dashDate', 'anaDate'];
        const analysisSelects = ['mapAnalysis', 'animAnalysis', 'dashAnalysis', 'anaAnalysis'];

        // Conjunto de datas disponíveis
        const dates = [...new Set(sorted.map(c => c.date))];
        if (dates.length > 0) {
            dateInputs.forEach(id => {
                const input = document.getElementById(id);
                if (input) {
                    input.max = dates[0];
                    if (!input.value) input.value = dates[0];
                    input.min = dates[dates.length - 1];
                }
            });
        }

        // Popula análises por data (recalcula quando a data muda)
        analysisSelects.forEach(id => {
            const select = document.getElementById(id);
            if (select) {
                select.addEventListener('change', () => this.updateForecast(id));
            }
        });

        dateInputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('change', () => this.updateForecast(id));
            }
        });

        this.updateForecast('mapAnalysis');
    }

    updateForecast(triggerId) {
        // Resolve data e análise dos seletores correspondentes
        const idMap = {
            'mapAnalysis': ['mapDate', 'mapAnalysis', 'mapForecast'],
            'mapDate': ['mapDate', 'mapAnalysis', 'mapForecast'],
            'animAnalysis': ['animDate', 'animAnalysis', null],
            'animDate': ['animDate', 'animAnalysis', null],
            'dashAnalysis': ['dashDate', 'dashAnalysis', null],
            'dashDate': ['dashDate', 'dashAnalysis', null],
            'anaAnalysis': ['anaDate', 'anaAnalysis', null],
            'anaDate': ['anaDate', 'anaAnalysis', null],
        };

        const mapping = idMap[triggerId];
        if (!mapping) return;

        const [dateId, anaId, forecastId] = mapping;
        const dateInput = document.getElementById(dateId);
        const anaSelect = document.getElementById(anaId);
        if (!dateInput || !anaSelect) return;

        const dateVal = dateInput.value.replace(/-/g, '');
        const cyclesForDate = this.cycles.filter(c => c.date === dateVal);
        const analyses = [...new Set(cyclesForDate.map(c => c.analysis))].sort();

        anaSelect.innerHTML = '';
        analyses.forEach(ana => {
            const opt = document.createElement('option');
            opt.value = ana;
            opt.textContent = `${ana}Z`;
            anaSelect.appendChild(opt);
        });

        if (analyses.length > 0) {
            anaSelect.value = analyses[analyses.length - 1];
        }

        // Popula horas de previsão do ciclo selecionado (seletor de mapa)
        if (forecastId) {
            const forecastSelect = document.getElementById(forecastId);
            if (!forecastSelect) return;
            forecastSelect.innerHTML = '';
            const cycle = cyclesForDate.find(c => c.analysis === anaSelect.value);
            const fhs = (cycle && cycle.forecast_hours) || [];
            fhs.forEach(fh => {
                const opt = document.createElement('option');
                opt.value = fh;
                opt.textContent = `+${parseInt(fh)}h`;
                forecastSelect.appendChild(opt);
            });
            if (fhs.length > 0) {
                forecastSelect.value = fhs[0];
            }
        }
    }

    setupTabs() {
        const tabBtns = document.querySelectorAll('.tab-btn');
        const tabPanels = document.querySelectorAll('.tab-panel');

        tabBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const tab = btn.dataset.tab;

                tabBtns.forEach(b => {
                    b.classList.remove('active');
                    b.setAttribute('aria-selected', 'false');
                });
                tabPanels.forEach(p => p.classList.remove('active'));

                btn.classList.add('active');
                btn.setAttribute('aria-selected', 'true');
                document.getElementById(`${tab}-panel`).classList.add('active');
            });
        });
    }

    setupEventListeners() {
        // Mapas
        document.getElementById('generateMap')?.addEventListener('click', () => this.generateMap());
        document.getElementById('openMap')?.addEventListener('click', () => this.openMap());

        // Animação
        document.getElementById('generateAnim')?.addEventListener('click', () => this.generateAnimation());
        document.getElementById('openAnim')?.addEventListener('click', () => this.openAnimation());

        // Dashboard
        document.getElementById('generateDashboard')?.addEventListener('click', () => this.generateDashboard());

        // METAR
        document.getElementById('fetchMetar')?.addEventListener('click', () => this.fetchMetar());

        // Análises
        document.getElementById('genSummary')?.addEventListener('click', () => this.generateAnalysis('summary'));
        document.getElementById('genProfile')?.addEventListener('click', () => this.generateAnalysis('profile'));
        document.getElementById('genTimeseries')?.addEventListener('click', () => this.generateAnalysis('timeseries'));
        document.getElementById('genCharts')?.addEventListener('click', () => this.generateAnalysis('charts'));

        // Refresh
        document.getElementById('refreshData')?.addEventListener('click', () => this.loadConfig());
    }

    async startStatusCheck() {
        await this.checkConnection();
        setInterval(() => this.checkConnection(), 60000); // A cada minuto
    }

    async checkConnection() {
        try {
            const res = await fetch('/health');
            const data = await res.json();
            const indicator = document.getElementById('connectionStatus');
            if (data.status === 'ok') {
                indicator.classList.remove('offline');
                indicator.classList.add('online');
                indicator.title = `Servidor online - v${data.version}`;
            } else {
                indicator.classList.remove('online');
                indicator.classList.add('offline');
                indicator.title = 'Servidor com problemas';
            }
        } catch (e) {
            const indicator = document.getElementById('connectionStatus');
            indicator.classList.remove('online');
            indicator.classList.add('offline');
            indicator.title = 'Sem conexão com o servidor';
        }
    }

    showLoading(text = 'Processando...') {
        const overlay = document.getElementById('loadingOverlay');
        document.getElementById('loadingText').textContent = text;
        overlay.classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }

    showToast(message, type = 'info') {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        toast.innerHTML = `
            <span class="toast-icon">${icons[type]}</span>
            <span class="toast-message">${message}</span>
            <button class="toast-close" onclick="this.parentElement.remove()">×</button>
        `;
        container.appendChild(toast);

        setTimeout(() => toast.remove(), 5000);
    }

    // === MAPAS ===
    async generateMap() {
        const variable = document.getElementById('mapVariable').value;
        const level = document.getElementById('mapLevel').value || null;
        const region = document.getElementById('mapRegion').value;
        const date = document.getElementById('mapDate').value.replace(/-/g, '');
        const analysis = document.getElementById('mapAnalysis').value;
        const forecast = document.getElementById('mapForecast').value || null;

        if (!variable || !region) {
            this.showToast('Selecione variável e região', 'warning');
            return;
        }

        this.showLoading('Gerando mapa...');

        try {
            const body = { variable, region, date, analysis };
            if (level) body.level = parseInt(level);
            if (forecast) body.forecast = forecast;

            const res = await fetch('/maps/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            const data = await res.json();

            if (res.ok && data.maps && data.maps.length > 0) {
                this.currentMapPath = data.maps[0];
                this.showMapPreview(data.maps[0]);
                this.showToast('Mapa gerado com sucesso!', 'success');
            } else {
                this.showToast(data.detail || 'Erro ao gerar mapa', 'error');
            }
        } catch (error) {
            console.error('Erro ao gerar mapa:', error);
            this.showToast('Erro de conexão ao gerar mapa', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showMapPreview(path) {
        const preview = document.getElementById('mapPreview');
        const img = document.getElementById('mapImage');
        const info = document.getElementById('mapInfo');

        // Converter caminho absoluto para URL servida
        const match = path.match(/data\/tmp\/(.+)$/);
        const url = match ? `/files/tmp/${match[1]}` : path;

        img.src = url;
        info.innerHTML = `
            <strong>Caminho:</strong> ${path}<br>
            <a href="${url}" target="_blank" class="btn btn-secondary" style="padding: 0.375rem 0.75rem; font-size: 0.8125rem; margin-top: 0.5rem; display: inline-block;">Abrir em nova aba</a>
        `;
        preview.classList.remove('hidden');
        document.getElementById('openMap').disabled = false;
    }

    openMap() {
        if (this.currentMapPath) {
            const match = this.currentMapPath.match(/data\/tmp\/(.+)$/);
            const url = match ? `/files/tmp/${match[1]}` : this.currentMapPath;
            window.open(url, '_blank');
        }
    }

    // === ANIMAÇÃO ===
    async generateAnimation() {
        const variable = document.getElementById('animVariable').value;
        const level = document.getElementById('animLevel').value || null;
        const region = document.getElementById('animRegion').value;
        const date = document.getElementById('animDate').value.replace(/-/g, '');
        const analysis = document.getElementById('animAnalysis').value;
        const duration = parseInt(document.getElementById('animDuration').value) || 700;

        if (!variable || !region) {
            this.showToast('Selecione variável e região', 'warning');
            return;
        }

        this.showLoading('Gerando animação GIF...');

        try {
            const body = { variable, region, date, analysis, duration_ms: duration };
            if (level) body.level = parseInt(level);

            const res = await fetch('/maps/animate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            const data = await res.json();

            if (res.ok && data.gif) {
                this.currentAnimPath = data.gif;
                this.showAnimPreview(data.gif);
                this.showToast('Animação gerada com sucesso!', 'success');
            } else {
                this.showToast(data.detail || 'Erro ao gerar animação', 'error');
            }
        } catch (error) {
            console.error('Erro ao gerar animação:', error);
            this.showToast('Erro de conexão ao gerar animação', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showAnimPreview(path) {
        const preview = document.getElementById('animPreview');
        const img = document.getElementById('animImage');
        const info = document.getElementById('animInfo');

        const match = path.match(/data\/tmp\/(.+)$/);
        const url = match ? `/files/tmp/${match[1]}` : path;

        img.src = url;
        info.innerHTML = `
            <strong>Caminho:</strong> ${path}<br>
            <a href="${url}" target="_blank" class="btn btn-secondary" style="padding: 0.375rem 0.75rem; font-size: 0.8125rem; margin-top: 0.5rem; display: inline-block;">Abrir em nova aba</a>
        `;
        preview.classList.remove('hidden');
        document.getElementById('openAnim').disabled = false;
    }

    openAnimation() {
        if (this.currentAnimPath) {
            const match = this.currentAnimPath.match(/data\/tmp\/(.+)$/);
            const url = match ? `/files/tmp/${match[1]}` : this.currentAnimPath;
            window.open(url, '_blank');
        }
    }

    // === DASHBOARD ===
    async generateDashboard() {
        const variable = document.getElementById('dashVariable').value;
        const level = document.getElementById('dashLevel').value || null;
        const region = document.getElementById('dashRegion').value;
        const date = document.getElementById('dashDate').value.replace(/-/g, '');
        const analysis = document.getElementById('dashAnalysis').value;

        if (!variable || !region) {
            this.showToast('Selecione variável e região', 'warning');
            return;
        }

        this.showLoading('Gerando dashboard estatístico...');

        try {
            const body = { variable, region, date, analysis };
            if (level) body.level = parseInt(level);

            const res = await fetch('/analysis/dashboard', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            const data = await res.json();

            if (res.ok) {
                this.showDashboardResults(data);
                this.showToast('Dashboard gerado com sucesso!', 'success');
            } else {
                this.showToast(data.detail || 'Erro ao gerar dashboard', 'error');
            }
        } catch (error) {
            console.error('Erro ao gerar dashboard:', error);
            this.showToast('Erro de conexão ao gerar dashboard', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showDashboardResults(data) {
        const container = document.getElementById('dashboardResults');
        const cardsContainer = document.getElementById('dashboardCards');
        const chartsContainer = document.getElementById('dashboardCharts');
        const profileContainer = document.getElementById('dashboardProfile');

        cardsContainer.innerHTML = '';
        chartsContainer.innerHTML = '';
        profileContainer.innerHTML = '';

        // Cards de resumo por hora de previsão
        if (data.cards && data.cards.length > 0) {
            data.cards.forEach(card => {
                const cardEl = document.createElement('div');
                cardEl.className = 'dashboard-card';
                cardEl.innerHTML = `
                    <h3>Previsão +${card.forecast}h</h3>
                    <div class="value">${card.mean?.toFixed(1) || '--'} <span class="unit">${data.units || ''}</span></div>
                    <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 0.25rem;">
                        Min: ${card.min?.toFixed(1) || '--'} | Max: ${card.max?.toFixed(1) || '--'} | DP: ${card.std?.toFixed(1) || '--'}
                    </div>
                    ${card.trend ? `
                        <div class="trend ${card.trend.slope > 0 ? 'positive' : card.trend.slope < 0 ? 'negative' : 'neutral'}">
                            ${card.trend.slope > 0 ? '↑' : card.trend.slope < 0 ? '↓' : '→'}
                            Tendência: ${card.trend.slope.toFixed(4)} (p=${card.trend.p_value?.toFixed(3) || '--'}, R²=${card.trend.r2?.toFixed(3) || '--'})
                        </div>
                    ` : ''}
                `;
                cardsContainer.appendChild(cardEl);
            });
        }

        // Gráficos
        if (data.charts && data.charts.length > 0) {
            data.charts.forEach(chartPath => {
                const match = chartPath.match(/data\/tmp\/(.+)$/);
                const url = match ? `/files/tmp/${match[1]}` : chartPath;
                const chartEl = document.createElement('div');
                chartEl.className = 'dashboard-chart';
                chartEl.innerHTML = `<img src="${url}" alt="Gráfico dashboard">`;
                chartsContainer.appendChild(chartEl);
            });
        }

        // Perfil vertical
        if (data.profile && data.profile.profile) {
            profileContainer.innerHTML = `
                <h3>Perfil Vertical - ${data.variable} (${data.region})</h3>
                <div class="analysis-grid" style="max-height: 400px; overflow-y: auto;">
                    ${data.profile.profile.slice(0, 20).map(p => `
                        <div class="analysis-item">
                            <span class="analysis-label">${p.level} hPa</span>
                            <span class="analysis-value">${p.value?.toFixed(2) || '--'} ${data.units || ''}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        container.classList.remove('hidden');
    }

    // === METAR ===
    async fetchMetar() {
        const icao = document.getElementById('metarRegion').value;
        if (!icao) {
            this.showToast('Selecione um aeródromo', 'warning');
            return;
        }

        this.showLoading('Buscando METAR...');

        try {
            const res = await fetch('/metar/fetch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ icao_code: icao })
            });

            const data = await res.json();

            if (res.ok) {
                this.showMetarResults(data);
                this.showToast('METAR obtido com sucesso!', 'success');
            } else {
                this.showToast(data.detail || 'Erro ao buscar METAR', 'error');
            }
        } catch (error) {
            console.error('Erro ao buscar METAR:', error);
            this.showToast('Erro de conexão ao buscar METAR', 'error');
        } finally {
            this.hideLoading();
        }
    }

    showMetarResults(data) {
        const container = document.getElementById('metarResults');
        const card = document.getElementById('metarCard');

        const parsed = data.parsed || {};
        const metadata = data.metadata || {};
        const raw = data.raw_metar || '';

        let fieldsHtml = '';
        if (parsed.wind) {
            fieldsHtml += this.createMetarField('Vento', `${parsed.wind.dir || 'VRB'}${parsed.wind.speed ? ` ${parsed.wind.speed} kt` : ''}${parsed.wind.gust ? ` (rajada ${parsed.wind.gust} kt)` : ''} ${parsed.wind.dir_cardinal ? `(${parsed.wind.dir_cardinal})` : ''}`);
        }
        if (parsed.visibility_km !== undefined) {
            fieldsHtml += this.createMetarField('Visibilidade', `${parsed.visibility_km} km`);
        }
        if (parsed.temperatures) {
            const t = parsed.temperatures;
            fieldsHtml += this.createMetarField('Temperatura', `${t.temp || '--'}°C`);
            fieldsHtml += this.createMetarField('Ponto de Orvalho', `${t.dewpoint || '--'}°C`);
            if (t.humidity !== undefined) {
                fieldsHtml += this.createMetarField('Umidade Relativa', `${t.humidity}%`);
            }
        }
        if (parsed.qnh_hpa !== undefined) {
            fieldsHtml += this.createMetarField('QNH', `${parsed.qnh_hpa} hPa (${parsed.qnh_inhg || '--'} inHg)`);
        }
        if (parsed.cloud && parsed.cloud.length > 0) {
            const clouds = parsed.cloud.map(c => `${c.amount || ''} ${c.base ? `${c.base}ft` : ''} ${c.type || ''}`).join('; ');
            fieldsHtml += this.createMetarField('Nuvens', clouds);
        }
        if (parsed.weather && parsed.weather.length > 0) {
            fieldsHtml += this.createMetarField('Tempo Presente', parsed.weather.join(', '));
        }
        if (parsed.vmc) {
            fieldsHtml += this.createMetarField('VMC', parsed.vmc);
        }
        if (parsed.runway && parsed.runway.length > 0) {
            fieldsHtml += this.createMetarField('Pistas', parsed.runway.join(', '));
        }

        card.innerHTML = `
            <div class="metar-header">
                <h3>${metadata.name || data.station} (${data.station})</h3>
                <span class="metar-time">${metadata.obsTime ? new Date(metadata.obsTime).toLocaleString('pt-BR') : new Date().toLocaleString('pt-BR')}</span>
            </div>
            <div class="metar-body">
                <div class="metar-raw">${raw}</div>
                <div class="metar-fields">${fieldsHtml}</div>
            </div>
        `;

        container.classList.remove('hidden');
    }

    createMetarField(label, value) {
        return `
            <div class="metar-field">
                <span class="metar-field-label">${label}</span>
                <span class="metar-field-value">${value}</span>
            </div>
        `;
    }

    // === ANÁLISES ===
    async generateAnalysis(type) {
        const variable = document.getElementById('anaVariable').value;
        const level = document.getElementById('anaLevel').value || null;
        const region = document.getElementById('anaRegion').value;
        const date = document.getElementById('anaDate').value.replace(/-/g, '');
        const analysis = document.getElementById('anaAnalysis').value;

        if (!variable || !region) {
            this.showToast('Selecione variável e região', 'warning');
            return;
        }

        const endpoints = {
            'summary': '/analysis/summary',
            'profile': '/analysis/profile',
            'timeseries': '/analysis/timeseries',
            'charts': '/analysis/charts'
        };

        this.showLoading(`Gerando ${type}...`);

        try {
            const body = { variable, region, date, analysis };
            if (level && type !== 'profile') body.level = parseInt(level);

            const res = await fetch(endpoints[type], {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            const data = await res.json();

            if (res.ok) {
                this.showAnalysisResults(type, data, variable, region);
                this.showToast(`${type.charAt(0).toUpperCase() + type.slice(1)} gerado com sucesso!`, 'success');
            } else {
                this.showToast(data.detail || `Erro ao gerar ${type}`, 'error');
            }
        } catch (error) {
            console.error(`Erro ao gerar ${type}:`, error);
            this.showToast(`Erro de conexão ao gerar ${type}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    showAnalysisResults(type, data, variable, region) {
        const container = document.getElementById('analysisResults');
        let html = '';

        switch (type) {
            case 'summary':
                if (data.results && data.results.length > 0) {
                    const r = data.results[0];
                    html = `
                        <div class="analysis-section">
                            <h3>Resumo Estatístico - ${variable} (${region})</h3>
                            <div class="analysis-grid">
                                <div class="analysis-item"><span class="analysis-label">Mínimo</span><span class="analysis-value">${r.min?.toFixed(2) || '--'}</span></div>
                                <div class="analysis-item"><span class="analysis-label">Máximo</span><span class="analysis-value">${r.max?.toFixed(2) || '--'}</span></div>
                                <div class="analysis-item"><span class="analysis-label">Média</span><span class="analysis-value">${r.mean?.toFixed(2) || '--'}</span></div>
                                <div class="analysis-item"><span class="analysis-label">Mediana</span><span class="analysis-value">${r.median?.toFixed(2) || '--'}</span></div>
                                <div class="analysis-item"><span class="analysis-label">Desvio Padrão</span><span class="analysis-value">${r.std?.toFixed(2) || '--'}</span></div>
                                <div class="analysis-item"><span class="analysis-label">IQR</span><span class="analysis-value">${r.iqr?.toFixed(2) || '--'}</span></div>
                                <div class="analysis-item"><span class="analysis-label">Assimetria</span><span class="analysis-value">${r.skewness?.toFixed(3) || '--'}</span></div>
                                <div class="analysis-item"><span class="analysis-label">Curtose</span><span class="analysis-value">${r.kurtosis?.toFixed(3) || '--'}</span></div>
                                <div class="analysis-item"><span class="analysis-label">Pontos válidos</span><span class="analysis-value">${r.n_points || '--'}</span></div>
                                <div class="analysis-item"><span class="analysis-label">Pontos faltantes</span><span class="analysis-value">${r.n_missing || '--'}</span></div>
                            </div>
                            <details style="margin-top: 1rem;">
                                <summary style="cursor: pointer; color: var(--primary);">Ver percentis</summary>
                                <div class="analysis-grid" style="margin-top: 0.5rem;">
                                    ${[1,5,10,25,50,75,90,95,99].map(p => `
                                        <div class="analysis-item"><span class="analysis-label">P${p}</span><span class="analysis-value">${r[`p${p}`]?.toFixed(2) || '--'}</span></div>
                                    `).join('')}
                                </div>
                            </details>
                        </div>
                    `;
                }
                break;

            case 'profile':
                if (data.profile && data.profile.length > 0) {
                    html = `
                        <div class="analysis-section">
                            <h3>Perfil Vertical - ${variable} (${region})</h3>
                            <div class="analysis-grid" style="max-height: 500px; overflow-y: auto;">
                                ${data.profile.map(p => `
                                    <div class="analysis-item">
                                        <span class="analysis-label">${p.level} hPa</span>
                                        <span class="analysis-value">${p.value?.toFixed(2) || '--'}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }
                break;

            case 'timeseries':
                if (data.series && data.series.length > 0) {
                    html = `
                        <div class="analysis-section">
                            <h3>Série Temporal - ${variable} (${region})</h3>
                            ${data.trend ? `
                                <div class="dashboard-card" style="margin-bottom: 1rem;">
                                    <h3>Tendência (OLS)</h3>
                                    <div class="analysis-grid">
                                        <div class="analysis-item"><span class="analysis-label">Inclinação</span><span class="analysis-value">${data.trend.slope?.toFixed(6) || '--'}</span></div>
                                        <div class="analysis-item"><span class="analysis-label">Intercepto</span><span class="analysis-value">${data.trend.intercept?.toFixed(2) || '--'}</span></div>
                                        <div class="analysis-item"><span class="analysis-label">R²</span><span class="analysis-value">${data.trend.r2?.toFixed(4) || '--'}</span></div>
                                        <div class="analysis-item"><span class="analysis-label">P-valor</span><span class="analysis-value">${data.trend.p_value?.toFixed(4) || '--'}</span></div>
                                        <div class="analysis-item"><span class="analysis-label">IC 95%</span><span class="analysis-value">[${data.trend.ci95?.[0]?.toFixed(6) || '--'}, ${data.trend.ci95?.[1]?.toFixed(6) || '--'}]</span></div>
                                    </div>
                                </div>
                            ` : ''}
                            <div class="analysis-grid" style="max-height: 400px; overflow-y: auto;">
                                ${data.series.map(s => `
                                    <div class="analysis-item">
                                        <span class="analysis-label">+${s.forecast}h</span>
                                        <span class="analysis-value">${s.value?.toFixed(2) || '--'}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                }
                break;

            case 'charts':
                if (data.charts && data.charts.length > 0) {
                    html = `
                        <div class="analysis-section">
                            <h3>Gráficos - ${variable} (${region})</h3>
                            <div class="dashboard-charts">
                                ${data.charts.map(chartPath => {
                                    const match = chartPath.match(/data\/tmp\/(.+)$/);
                                    const url = match ? `/files/tmp/${match[1]}` : chartPath;
                                    return `<div class="dashboard-chart"><img src="${url}" alt="Gráfico ${chartPath}"></div>`;
                                }).join('')}
                            </div>
                        </div>
                    `;
                }
                break;
        }

        container.innerHTML = html;
        container.classList.remove('hidden');
    }

    updateLastUpdate() {
        const el = document.getElementById('lastUpdate');
        if (el) {
            el.textContent = `Última atualização: ${new Date().toLocaleString('pt-BR')}`;
        }
    }
}

// Inicializar quando DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    window.app = new METServerApp();
});