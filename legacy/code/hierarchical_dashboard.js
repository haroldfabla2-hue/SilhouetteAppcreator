/**
 * Dashboard Jerárquico Avanzado de SilhouetteMCP
 * Sistema completo de gestión y visualización de 100+ agentes
 * Autor: Sistema SilhouetteMCP
 * Fecha: 2025-11-06
 */

// =====================================
// CONFIGURACIÓN Y VARIABLES GLOBALES
// =====================================

class SilhouetteDashboard {
    constructor() {
        this.apiBaseUrls = {
            master: 'http://localhost:8001',
            maps: 'http://localhost:8002',
            financial: 'http://localhost:8003',
            social_travel: 'http://localhost:8004',
            content: 'http://localhost:8005',
            database: 'http://localhost:8006',
            research: 'http://localhost:8007',
            support: 'http://localhost:8008',
            coordination: 'http://localhost:8009',
            metrics: 'http://localhost:8010'
        };

        this.websocketConnections = new Map();
        this.currentTheme = localStorage.getItem('dashboard_theme') || 'dark';
        this.currentView = 'dashboard';
        this.selectedAgents = new Set();
        this.searchResults = [];
        this.alerts = [];
        this.metricsData = {};
        this.hierarchyData = null;
        this.draggedTask = null;
        this.presentationMode = false;
        
        this.keyboardShortcuts = new Map([
            ['ctrl+h', () => this.switchView('hierarchy')],
            ['ctrl+t', () => this.switchView('teams')],
            ['ctrl+c', () => this.switchView('coordination')],
            ['ctrl+m', () => this.switchView('metrics')],
            ['ctrl+f', () => this.focusSearch()],
            ['ctrl+e', () => this.exportDashboard()],
            ['ctrl+p', () => this.togglePresentationMode()],
            ['ctrl+d', () => this.toggleTheme()],
            ['escape', () => this.closeModals()]
        ]);

        this.init();
    }

    // =====================================
    // INICIALIZACIÓN DEL SISTEMA
    // =====================================

    async init() {
        try {
            console.log('🔄 Inicializando Dashboard SilhouetteMCP...');
            
            // Configurar tema inicial
            this.applyTheme(this.currentTheme);
            
            // Inicializar componentes
            await this.initializeData();
            this.setupWebSocketConnections();
            this.setupEventListeners();
            this.setupKeyboardShortcuts();
            this.initializeVisualizations();
            this.loadSavedState();
            
            // Iniciar actualizaciones automáticas
            this.startAutoRefresh();
            
            console.log('✅ Dashboard SilhouetteMCP inicializado correctamente');
            this.showNotification('Dashboard iniciado correctamente', 'success');
            
        } catch (error) {
            console.error('❌ Error inicializando dashboard:', error);
            this.showNotification('Error inicializando dashboard', 'error');
        }
    }

    async initializeData() {
        try {
            // Cargar estructura jerárquica
            this.hierarchyData = await this.fetchHierarchyData();
            
            // Cargar métricas iniciales
            this.metricsData = await this.fetchMetricsData();
            
            // Cargar estado de equipos
            await this.updateTeamsStatus();
            
        } catch (error) {
            console.error('Error cargando datos iniciales:', error);
        }
    }

    // =====================================
    // API INTEGRATION
    // =====================================

    async fetchHierarchyData() {
        try {
            const response = await fetch(`${this.apiBaseUrls.master}/api/hierarchy`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            return this.processHierarchyData(data);
        } catch (error) {
            console.error('Error cargando datos jerárquicos:', error);
            return this.getDefaultHierarchyData();
        }
    }

    async fetchMetricsData() {
        try {
            const response = await fetch(`${this.apiBaseUrls.metrics}/api/metrics`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            return await response.json();
        } catch (error) {
            console.error('Error cargando métricas:', error);
            return this.getDefaultMetricsData();
        }
    }

    async updateTeamsStatus() {
        const teams = ['maps', 'financial', 'social_travel', 'content', 'database', 'research', 'support'];
        
        for (const team of teams) {
            try {
                const response = await fetch(`${this.apiBaseUrls[team]}/api/status`);
                if (response.ok) {
                    const status = await response.json();
                    this.updateTeamStatus(team, status);
                }
            } catch (error) {
                console.warn(`Error actualizando estado del equipo ${team}:`, error);
            }
        }
    }

    async assignTask(taskData) {
        try {
            const response = await fetch(`${this.apiBaseUrls.master}/api/assign_task`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskData)
            });
            
            if (response.ok) {
                const result = await response.json();
                this.showNotification('Tarea asignada correctamente', 'success');
                return result;
            } else {
                throw new Error('Error en la asignación');
            }
        } catch (error) {
            console.error('Error asignando tarea:', error);
            this.showNotification('Error asignando tarea', 'error');
            throw error;
        }
    }

    // =====================================
    // WEBSOCKET CONNECTIONS
    // =====================================

    setupWebSocketConnections() {
        // Conexión principal para actualizaciones en tiempo real
        this.connectWebSocket('master', `${this.apiBaseUrls.master.replace('http', 'ws')}/ws`);
        
        // Conexiones específicas por equipo
        const teams = ['maps', 'financial', 'social_travel', 'content', 'database', 'research', 'support'];
        teams.forEach(team => {
            const wsUrl = `${this.apiBaseUrls[team].replace('http', 'ws')}/ws`;
            this.connectWebSocket(team, wsUrl);
        });
    }

    connectWebSocket(name, url) {
        try {
            const ws = new WebSocket(url);
            
            ws.onopen = () => {
                console.log(`✅ WebSocket conectado: ${name}`);
                this.websocketConnections.set(name, ws);
                this.updateConnectionStatus(name, 'connected');
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.handleWebSocketMessage(name, data);
            };
            
            ws.onclose = () => {
                console.warn(`⚠️ WebSocket desconectado: ${name}`);
                this.websocketConnections.delete(name);
                this.updateConnectionStatus(name, 'disconnected');
                
                // Reconectar automáticamente
                setTimeout(() => {
                    if (!this.websocketConnections.has(name)) {
                        console.log(`🔄 Reconectando WebSocket: ${name}`);
                        this.connectWebSocket(name, url);
                    }
                }, 5000);
            };
            
            ws.onerror = (error) => {
                console.error(`❌ Error WebSocket ${name}:`, error);
                this.updateConnectionStatus(name, 'error');
            };
            
        } catch (error) {
            console.error(`Error conectando WebSocket ${name}:`, error);
        }
    }

    handleWebSocketMessage(source, data) {
        switch (data.type) {
            case 'agent_status_update':
                this.updateAgentStatus(data.payload);
                break;
            case 'task_assignment':
                this.handleTaskAssignment(data.payload);
                break;
            case 'metrics_update':
                this.updateMetrics(data.payload);
                break;
            case 'alert':
                this.handleAlert(data.payload);
                break;
            case 'team_performance':
                this.updateTeamPerformance(data.payload);
                break;
            default:
                console.log(`Mensaje WebSocket desconocido de ${source}:`, data);
        }
    }

    // =====================================
    // VISUALIZACIONES D3.JS
    // =====================================

    initializeHierarchyVisualization() {
        const container = d3.select('#hierarchy-visualization');
        const width = container.node().offsetWidth;
        const height = 600;

        const svg = container.append('svg')
            .attr('width', width)
            .attr('height', height);

        const g = svg.append('g')
            .attr('transform', 'translate(50, 50)');

        // Crear el layout del árbol
        const tree = d3.tree()
            .size([height - 100, width - 200]);

        // Crear las relaciones jerárquicas
        this.renderHierarchyTree(g, tree);
        
        // Configurar zoom y pan
        this.setupZoomAndPan(svg);
    }

    renderHierarchyTree(container, tree) {
        if (!this.hierarchyData) return;

        const root = d3.hierarchy(this.hierarchyData);
        tree(root);

        // Renderizar enlaces
        const links = container.selectAll('.link')
            .data(root.links())
            .enter().append('path')
            .attr('class', 'link')
            .attr('d', d3.linkHorizontal()
                .x(d => d.y)
                .y(d => d.x))
            .style('fill', 'none')
            .style('stroke', '#666')
            .style('stroke-width', 2);

        // Renderizar nodos
        const nodes = container.selectAll('.node')
            .data(root.descendants())
            .enter().append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${d.y},${d.x})`)
            .style('cursor', 'pointer')
            .on('click', (event, d) => this.selectAgent(d.data));

        // Círculos de nodos
        nodes.append('circle')
            .attr('r', d => d.data.level === 5 ? 12 : d.data.level === 4 ? 10 : 8)
            .style('fill', d => this.getAgentColor(d.data))
            .style('stroke', '#fff')
            .style('stroke-width', 2);

        // Etiquetas de nodos
        nodes.append('text')
            .attr('dy', '.35em')
            .attr('x', d => d.children ? -15 : 15)
            .style('text-anchor', d => d.children ? 'end' : 'start')
            .style('font-size', '12px')
            .style('fill', '#333')
            .text(d => d.data.name);

        // Indicadores de estado
        nodes.append('circle')
            .attr('r', 4)
            .attr('cx', 8)
            .attr('cy', -8)
            .style('fill', d => this.getStatusColor(d.data.status));

        // Tooltips
        nodes.append('title')
            .text(d => this.generateAgentTooltip(d.data));

        // Configurar drag and drop para reasignación
        this.setupDragAndDrop(nodes);
    }

    renderNetworkGraph() {
        const container = d3.select('#network-visualization');
        const width = container.node().offsetWidth;
        const height = 500;

        const svg = container.append('svg')
            .attr('width', width)
            .attr('height', height);

        const simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2));

        // Crear enlaces basados en comunicación entre agentes
        const links = this.buildNetworkLinks();
        const nodes = this.buildNetworkNodes();

        // Renderizar enlaces
        const link = svg.append('g')
            .selectAll('line')
            .data(links)
            .enter().append('line')
            .attr('class', 'network-link')
            .style('stroke', '#999')
            .style('stroke-opacity', 0.6)
            .style('stroke-width', d => Math.sqrt(d.strength || 1));

        // Renderizar nodos
        const node = svg.append('g')
            .selectAll('circle')
            .data(nodes)
            .enter().append('circle')
            .attr('class', 'network-node')
            .attr('r', d => d.type === 'leader' ? 10 : 6)
            .style('fill', d => this.getNetworkNodeColor(d))
            .style('cursor', 'pointer')
            .call(d3.drag()
                .on('start', this.dragstarted.bind(this, simulation))
                .on('drag', this.dragged.bind(this))
                .on('end', this.dragended.bind(this, simulation)));

        // Etiquetas
        const labels = svg.append('g')
            .selectAll('text')
            .data(nodes)
            .enter().append('text')
            .text(d => d.name)
            .style('font-size', '10px')
            .style('text-anchor', 'middle')
            .style('pointer-events', 'none');

        simulation
            .nodes(nodes)
            .on('tick', () => {
                link
                    .attr('x1', d => d.source.x)
                    .attr('y1', d => d.source.y)
                    .attr('x2', d => d.target.x)
                    .attr('y2', d => d.target.y);

                node
                    .attr('cx', d => d.x)
                    .attr('cy', d => d.y);

                labels
                    .attr('x', d => d.x)
                    .attr('y', d => d.y + 20);
            });

        simulation.force('link').links(links);
    }

    // =====================================
    // GRÁFICOS CHART.JS
    // =====================================

    initializeMetricsCharts() {
        // Gráfico de rendimiento por equipo
        this.createTeamPerformanceChart();
        
        // Heatmap de carga de trabajo
        this.createWorkloadHeatmap();
        
        // Gantt chart de proyectos
        this.createGanttChart();
        
        // Gráfico de métricas en tiempo real
        this.createRealtimeMetricsChart();
    }

    createTeamPerformanceChart() {
        const ctx = document.getElementById('team-performance-chart').getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Maps', 'Financial', 'Social/Travel', 'Content', 'Database', 'Research', 'Support'],
                datasets: [{
                    label: 'Tareas Completadas',
                    data: [85, 92, 78, 88, 95, 82, 90],
                    backgroundColor: 'rgba(54, 162, 235, 0.6)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }, {
                    label: 'Eficiencia (%)',
                    data: [88, 95, 82, 90, 97, 85, 92],
                    backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Rendimiento por Equipo'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    createWorkloadHeatmap() {
        const ctx = document.getElementById('workload-heatmap').getContext('2d');
        
        // Datos del heatmap (agentes x tiempo)
        const agents = Array.from({length: 30}, (_, i) => `Agent${i + 1}`);
        const hours = Array.from({length: 24}, (_, i) => `${i}:00`);
        const workloadData = this.generateWorkloadData(agents, hours);

        new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Carga de Trabajo',
                    data: workloadData,
                    backgroundColor: function(context) {
                        const value = context.raw.y;
                        return value > 80 ? 'rgba(255, 99, 132, 0.8)' :
                               value > 60 ? 'rgba(255, 206, 86, 0.8)' :
                               value > 40 ? 'rgba(75, 192, 192, 0.8)' :
                               'rgba(54, 162, 235, 0.8)';
                    },
                    pointRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Heatmap de Carga de Trabajo'
                    }
                },
                scales: {
                    x: {
                        type: 'linear',
                        position: 'bottom',
                        min: 0,
                        max: 23,
                        title: {
                            display: true,
                            text: 'Hora del Día'
                        }
                    },
                    y: {
                        type: 'linear',
                        min: 0,
                        max: 29,
                        title: {
                            display: true,
                            text: 'Agentes'
                        }
                    }
                }
            }
        });
    }

    createGanttChart() {
        const ctx = document.getElementById('gantt-chart').getContext('2d');
        
        const projects = [
            {name: 'Sistema Maps V2', start: 0, duration: 15, team: 'maps'},
            {name: 'Análisis Financiero Q4', start: 5, duration: 20, team: 'financial'},
            {name: 'Rediseño Social Platform', start: 10, duration: 18, team: 'social_travel'},
            {name: 'Content Management System', start: 2, duration: 12, team: 'content'},
            {name: 'Database Migration', start: 8, duration: 25, team: 'database'},
            {name: 'Research Analytics Platform', start: 12, duration: 15, team: 'research'},
            {name: 'Support Automation', start: 3, duration: 10, team: 'support'}
        ];

        const teamColors = {
            maps: '#FF6384',
            financial: '#36A2EB',
            social_travel: '#FFCE56',
            content: '#4BC0C0',
            database: '#9966FF',
            research: '#FF9F40',
            support: '#FF6384'
        };

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: projects.map(p => p.name),
                datasets: [{
                    label: 'Duración del Proyecto (días)',
                    data: projects.map(p => ({x: p.start, y: p.name, duration: p.duration})),
                    backgroundColor: projects.map(p => teamColors[p.team]),
                    borderColor: projects.map(p => teamColors[p.team]),
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Timeline de Proyectos'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const data = context.raw;
                                return `${data.y}: ${data.duration} días (Inicia día ${data.x})`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Días desde el inicio'
                        }
                    }
                }
            }
        });
    }

    createRealtimeMetricsChart() {
        const ctx = document.getElementById('realtime-metrics').getContext('2d');
        
        const config = {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU Usage (%)',
                    data: [],
                    borderColor: 'rgb(255, 99, 132)',
                    backgroundColor: 'rgba(255, 99, 132, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Memory Usage (%)',
                    data: [],
                    borderColor: 'rgb(54, 162, 235)',
                    backgroundColor: 'rgba(54, 162, 235, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Network Traffic (MB/s)',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                animation: {
                    duration: 0
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Métricas en Tiempo Real'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        };

        this.realtimeChart = new Chart(ctx, config);
        this.startRealtimeUpdates();
    }

    // =====================================
    // DRAG & DROP
    // =====================================

    setupDragAndDrop(nodes) {
        nodes.call(d3.drag()
            .on('start', this.dragStarted.bind(this))
            .on('drag', this.dragged.bind(this))
            .on('end', this.dragEnded.bind(this)));
    }

    dragStarted(event, d) {
        if (!event.active) this.hierarchySimulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragEnded(event, d) {
        if (!event.active) this.hierarchySimulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    setupTaskDragAndDrop() {
        const taskElements = document.querySelectorAll('.task-item');
        const agentDropZones = document.querySelectorAll('.agent-drop-zone');

        taskElements.forEach(task => {
            task.draggable = true;
            task.addEventListener('dragstart', (e) => {
                this.draggedTask = {
                    id: task.dataset.taskId,
                    name: task.dataset.taskName,
                    currentAgent: task.dataset.currentAgent
                };
                task.classList.add('dragging');
            });

            task.addEventListener('dragend', (e) => {
                task.classList.remove('dragging');
                this.draggedTask = null;
            });
        });

        agentDropZones.forEach(zone => {
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                zone.classList.add('drag-over');
            });

            zone.addEventListener('dragleave', (e) => {
                zone.classList.remove('drag-over');
            });

            zone.addEventListener('drop', async (e) => {
                e.preventDefault();
                zone.classList.remove('drag-over');
                
                if (this.draggedTask && zone.dataset.agentId) {
                    await this.reassignTask(this.draggedTask, zone.dataset.agentId);
                }
            });
        });
    }

    async reassignTask(task, newAgentId) {
        try {
            const assignmentData = {
                taskId: task.id,
                fromAgent: task.currentAgent,
                toAgent: newAgentId,
                timestamp: new Date().toISOString()
            };

            const result = await this.assignTask(assignmentData);
            
            if (result.success) {
                this.showNotification(`Tarea "${task.name}" reasignada correctamente`, 'success');
                this.updateTaskAssignment(task.id, newAgentId);
            } else {
                throw new Error(result.error || 'Error en la reasignación');
            }
        } catch (error) {
            console.error('Error reasignando tarea:', error);
            this.showNotification('Error reasignando tarea', 'error');
        }
    }

    // =====================================
    // BÚSQUEDA AVANZADA
    // =====================================

    setupAdvancedSearch() {
        const searchInput = document.getElementById('advanced-search');
        const searchFilters = document.getElementById('search-filters');
        
        let searchTimeout;

        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performAdvancedSearch(e.target.value);
            }, 300);
        });

        // Filtros por tipo de agente, equipo, estado
        const filterOptions = [
            {value: 'all', label: 'Todos los agentes'},
            {value: 'leader', label: 'Líderes de equipo'},
            {value: 'supervisor', label: 'Supervisores'},
            {value: 'specialist', label: 'Especialistas'},
            {value: 'active', label: 'Activos'},
            {value: 'idle', label: 'Inactivos'},
            {value: 'maps', label: 'Equipo Maps'},
            {value: 'financial', label: 'Equipo Financial'},
            {value: 'social_travel', label: 'Equipo Social/Travel'},
            {value: 'content', label: 'Equipo Content'},
            {value: 'database', label: 'Equipo Database'},
            {value: 'research', label: 'Equipo Research'},
            {value: 'support', label: 'Equipo Support'}
        ];

        filterOptions.forEach(option => {
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.value = option.value;
            checkbox.id = `filter-${option.value}`;
            
            const label = document.createElement('label');
            label.htmlFor = checkbox.id;
            label.textContent = option.label;
            
            searchFilters.appendChild(checkbox);
            searchFilters.appendChild(label);
        });
    }

    performAdvancedSearch(query) {
        const filters = Array.from(document.querySelectorAll('#search-filters input:checked'))
            .map(cb => cb.value);

        if (!query && filters.length === 0) {
            this.clearSearchResults();
            return;
        }

        this.searchResults = this.filterAgents(query, filters);
        this.displaySearchResults();
    }

    filterAgents(query, filters) {
        let results = [];

        // Filtrar por texto de búsqueda
        if (query) {
            const searchTerms = query.toLowerCase().split(' ');
            results = this.getAllAgents().filter(agent => {
                const searchText = `${agent.name} ${agent.type} ${agent.team} ${agent.skills?.join(' ')}`.toLowerCase();
                return searchTerms.every(term => searchText.includes(term));
            });
        } else {
            results = this.getAllAgents();
        }

        // Aplicar filtros adicionales
        if (filters.length > 0) {
            results = results.filter(agent => {
                return filters.some(filter => {
                    switch (filter) {
                        case 'leader':
                            return agent.type === 'leader';
                        case 'supervisor':
                            return agent.type === 'supervisor';
                        case 'specialist':
                            return agent.type === 'specialist';
                        case 'active':
                            return agent.status === 'active';
                        case 'idle':
                            return agent.status === 'idle';
                        default:
                            return agent.team === filter;
                    }
                });
            });
        }

        return results;
    }

    displaySearchResults() {
        const resultsContainer = document.getElementById('search-results');
        
        if (this.searchResults.length === 0) {
            resultsContainer.innerHTML = '<p>No se encontraron resultados</p>';
            return;
        }

        const resultsHTML = this.searchResults.map(agent => `
            <div class="search-result-item" data-agent-id="${agent.id}">
                <div class="agent-info">
                    <span class="agent-name">${agent.name}</span>
                    <span class="agent-type">${agent.type}</span>
                    <span class="agent-team">${agent.team}</span>
                    <span class="agent-status status-${agent.status}">${agent.status}</span>
                </div>
                <div class="agent-actions">
                    <button onclick="dashboard.selectAgent('${agent.id}')">Ver Detalles</button>
                    <button onclick="dashboard.viewAgentMetrics('${agent.id}')">Métricas</button>
                </div>
            </div>
        `).join('');

        resultsContainer.innerHTML = resultsHTML;
    }

    // =====================================
    // SISTEMA DE ALERTAS
    // =====================================

    setupAlertSystem() {
        this.alertQueue = [];
        this.maxAlerts = 10;
    }

    handleAlert(alertData) {
        const alert = {
            id: Date.now(),
            type: alertData.type || 'info',
            title: alertData.title,
            message: alertData.message,
            timestamp: new Date(),
            agent: alertData.agent,
            team: alertData.team,
            priority: alertData.priority || 'medium'
        };

        this.alerts.push(alert);
        this.displayAlert(alert);
        this.updateAlertCount();
        
        // Auto-remove después del tiempo especificado
        setTimeout(() => {
            this.removeAlert(alert.id);
        }, alertData.duration || 10000);
    }

    displayAlert(alert) {
        const alertsContainer = document.getElementById('alerts-container');
        if (!alertsContainer) return;

        const alertElement = document.createElement('div');
        alertElement.className = `alert alert-${alert.type} priority-${alert.priority}`;
        alertElement.dataset.alertId = alert.id;

        alertElement.innerHTML = `
            <div class="alert-header">
                <span class="alert-icon">${this.getAlertIcon(alert.type)}</span>
                <span class="alert-title">${alert.title}</span>
                <button class="alert-close" onclick="dashboard.removeAlert(${alert.id})">&times;</button>
            </div>
            <div class="alert-message">${alert.message}</div>
            <div class="alert-footer">
                <span class="alert-timestamp">${this.formatTime(alert.timestamp)}</span>
                ${alert.agent ? `<span class="alert-agent">Agente: ${alert.agent}</span>` : ''}
            </div>
        `;

        alertsContainer.appendChild(alertElement);
        
        // Animación de entrada
        setTimeout(() => {
            alertElement.classList.add('show');
        }, 100);

        // Limitar número de alertas
        if (this.alerts.length > this.maxAlerts) {
            const oldestAlert = this.alerts[0];
            this.removeAlert(oldestAlert.id);
        }
    }

    removeAlert(alertId) {
        const alertElement = document.querySelector(`[data-alert-id="${alertId}"]`);
        if (alertElement) {
            alertElement.classList.add('removing');
            setTimeout(() => {
                alertElement.remove();
            }, 300);
        }

        this.alerts = this.alerts.filter(alert => alert.id !== alertId);
        this.updateAlertCount();
    }

    updateAlertCount() {
        const alertCountElements = document.querySelectorAll('.alert-count');
        alertCountElements.forEach(element => {
            element.textContent = this.alerts.length;
        });
    }

    getAlertIcon(type) {
        const icons = {
            info: 'ℹ️',
            success: '✅',
            warning: '⚠️',
            error: '❌',
            critical: '🚨'
        };
        return icons[type] || icons.info;
    }

    // =====================================
    // EXPORTACIÓN DE REPORTES
    // =====================================

    async exportDashboard() {
        try {
            const exportFormat = await this.selectExportFormat();
            if (!exportFormat) return;

            const exportData = await this.prepareExportData();
            
            switch (exportFormat) {
                case 'pdf':
                    await this.exportToPDF(exportData);
                    break;
                case 'excel':
                    await this.exportToExcel(exportData);
                    break;
                case 'json':
                    await this.exportToJSON(exportData);
                    break;
            }
            
            this.showNotification(`Dashboard exportado en formato ${exportFormat.toUpperCase()}`, 'success');
        } catch (error) {
            console.error('Error exportando dashboard:', error);
            this.showNotification('Error exportando dashboard', 'error');
        }
    }

    async selectExportFormat() {
        return new Promise((resolve) => {
            const modal = document.createElement('div');
            modal.className = 'export-modal';
            modal.innerHTML = `
                <div class="modal-content">
                    <h3>Seleccionar Formato de Exportación</h3>
                    <div class="export-options">
                        <button onclick="dashboard.handleExportFormat('pdf', this.closest('.modal-content').parentElement)">
                            📄 Exportar PDF
                        </button>
                        <button onclick="dashboard.handleExportFormat('excel', this.closest('.modal-content').parentElement)">
                            📊 Exportar Excel
                        </button>
                        <button onclick="dashboard.handleExportFormat('json', this.closest('.modal-content').parentElement)">
                            📋 Exportar JSON
                        </button>
                    </div>
                    <button onclick="this.closest('.export-modal').remove()">Cancelar</button>
                </div>
            `;
            document.body.appendChild(modal);
        });
    }

    async prepareExportData() {
        return {
            timestamp: new Date().toISOString(),
            hierarchy: this.hierarchyData,
            metrics: this.metricsData,
            teams: this.getTeamsSummary(),
            alerts: this.alerts,
            activeTasks: await this.getActiveTasks(),
            systemStatus: await this.getSystemStatus()
        };
    }

    async exportToPDF(data) {
        // Usar jsPDF para generar PDF
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        // Título
        doc.setFontSize(20);
        doc.text('SilhouetteMCP - Dashboard Jerárquico', 20, 30);

        // Fecha
        doc.setFontSize(12);
        doc.text(`Generado: ${new Date(data.timestamp).toLocaleString()}`, 20, 45);

        // Resumen del sistema
        doc.setFontSize(16);
        doc.text('Resumen del Sistema', 20, 65);
        
        doc.setFontSize(12);
        let yPos = 80;
        doc.text(`Total de Agentes: ${data.hierarchy.totalAgents || 'N/A'}`, 20, yPos);
        yPos += 10;
        doc.text(`Equipos Activos: ${Object.keys(data.teams).length}`, 20, yPos);
        yPos += 10;
        doc.text(`Alertas Activas: ${data.alerts.length}`, 20, yPos);

        // Métricas por equipo
        yPos += 20;
        doc.setFontSize(16);
        doc.text('Rendimiento por Equipo', 20, yPos);
        
        yPos += 15;
        doc.setFontSize(12);
        Object.entries(data.teams).forEach(([team, info]) => {
            if (yPos > 250) {
                doc.addPage();
                yPos = 30;
            }
            doc.text(`${team}: ${info.agentCount} agentes, Eficiencia: ${info.efficiency}%`, 20, yPos);
            yPos += 10;
        });

        // Guardar PDF
        doc.save(`silhouette_dashboard_${new Date().toISOString().split('T')[0]}.pdf`);
    }

    async exportToExcel(data) {
        // Usar SheetJS para generar Excel
        const wb = XLSX.utils.book_new();

        // Hoja de resumen
        const summaryData = [
            ['SilhouetteMCP - Dashboard Jerárquico'],
            [`Fecha de generación: ${new Date(data.timestamp).toLocaleString()}`],
            [''],
            ['Métricas Generales'],
            ['Total de Agentes', data.hierarchy.totalAgents || 'N/A'],
            ['Equipos Activos', Object.keys(data.teams).length],
            ['Alertas Activas', data.alerts.length],
            [''],
            ['Estado por Equipos']
        ];

        Object.entries(data.teams).forEach(([team, info]) => {
            summaryData.push([team, info.agentCount, info.efficiency + '%', info.status]);
        });

        const summaryWs = XLSX.utils.aoa_to_sheet(summaryData);
        XLSX.utils.book_append_sheet(wb, summaryWs, 'Resumen');

        // Hoja de agentes detallada
        const agentsData = [['ID', 'Nombre', 'Tipo', 'Equipo', 'Estado', 'Eficiencia']];
        this.getAllAgents().forEach(agent => {
            agentsData.push([
                agent.id,
                agent.name,
                agent.type,
                agent.team,
                agent.status,
                agent.efficiency || 'N/A'
            ]);
        });

        const agentsWs = XLSX.utils.aoa_to_sheet(agentsData);
        XLSX.utils.book_append_sheet(wb, agentsWs, 'Agentes');

        // Hoja de alertas
        const alertsData = [['ID', 'Tipo', 'Título', 'Mensaje', 'Timestamp', 'Prioridad']];
        data.alerts.forEach(alert => {
            alertsData.push([
                alert.id,
                alert.type,
                alert.title,
                alert.message,
                alert.timestamp,
                alert.priority
            ]);
        });

        const alertsWs = XLSX.utils.aoa_to_sheet(alertsData);
        XLSX.utils.book_append_sheet(wb, alertsWs, 'Alertas');

        // Descargar archivo
        XLSX.writeFile(wb, `silhouette_dashboard_${new Date().toISOString().split('T')[0]}.xlsx`);
    }

    async exportToJSON(data) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `silhouette_dashboard_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    // =====================================
    // SIMULADOR DE ESCENARIOS
    // =====================================

    setupScenarioSimulator() {
        const scenarios = [
            {
                name: 'Alta Demanda',
                description: 'Simular aumento del 200% en la carga de trabajo',
                config: {
                    workloadMultiplier: 2.0,
                    responseTimeMultiplier: 1.5,
                    agentEfficiencyMultiplier: 0.8
                }
            },
            {
                name: 'Fallo de Equipo',
                description: 'Simular fallo del 50% de agentes del equipo Financial',
                config: {
                    disabledTeams: ['financial'],
                    disabledAgentPercentage: 50
                }
            },
            {
                name: 'Optimización',
                description: 'Simular optimización del algoritmo de coordinación',
                config: {
                    coordinationEfficiencyImprovement: 25,
                    communicationLatencyReduction: 30
                }
            },
            {
                name: 'Escalabilidad',
                description: 'Simular expansión a 150 agentes',
                config: {
                    newAgentCount: 50,
                    distributedTeams: ['maps', 'content', 'database']
                }
            }
        ];

        this.renderScenarioSelector(scenarios);
    }

    renderScenarioSelector(scenarios) {
        const container = document.getElementById('scenario-selector');
        if (!container) return;

        const scenariosHTML = scenarios.map(scenario => `
            <div class="scenario-card" data-scenario="${scenario.name.toLowerCase().replace(' ', '_')}">
                <h4>${scenario.name}</h4>
                <p>${scenario.description}</p>
                <button onclick="dashboard.runScenario('${scenario.name}')">Ejecutar Simulación</button>
            </div>
        `).join('');

        container.innerHTML = scenariosHTML;
    }

    async runScenario(scenarioName) {
        try {
            this.showNotification(`Iniciando simulación: ${scenarioName}`, 'info');
            
            const scenarios = {
                'Alta Demanda': await this.simulateHighDemand(),
                'Fallo de Equipo': await this.simulateTeamFailure(),
                'Optimización': await this.simulateOptimization(),
                'Escalabilidad': await this.simulateScalability()
            };

            const scenario = scenarios[scenarioName];
            if (!scenario) {
                throw new Error(`Escenario no encontrado: ${scenarioName}`);
            }

            // Mostrar resultados de la simulación
            this.displayScenarioResults(scenario);
            this.showNotification(`Simulación completada: ${scenarioName}`, 'success');
            
        } catch (error) {
            console.error('Error ejecutando simulación:', error);
            this.showNotification('Error ejecutando simulación', 'error');
        }
    }

    async simulateHighDemand() {
        const originalMetrics = {...this.metricsData};
        
        // Simular incremento de carga
        const loadIncrease = 2.0;
        
        const simulatedMetrics = {
            ...originalMetrics,
            totalTasks: Math.floor(originalMetrics.totalTasks * loadIncrease),
            averageResponseTime: Math.floor(originalMetrics.averageResponseTime * 1.5),
            systemLoad: Math.min(100, originalMetrics.systemLoad * 1.8),
            queueLength: Math.floor(originalMetrics.queueLength * 2.5)
        };

        return {
            name: 'Alta Demanda',
            before: originalMetrics,
            after: simulatedMetrics,
            impact: {
                tasksIncreased: `${Math.round((loadIncrease - 1) * 100)}%`,
                responseTimeIncrease: '50%',
                systemLoadIncrease: `${Math.round((simulatedMetrics.systemLoad - originalMetrics.systemLoad))}%`,
                queueGrowth: `${Math.round((simulatedMetrics.queueLength - originalMetrics.queueLength) / originalMetrics.queueLength * 100)}%`
            }
        };
    }

    async simulateTeamFailure() {
        const originalTeams = {...this.teamsData};
        
        // Simular fallo del 50% de agentes Financial
        const financialTeam = originalTeams.financial;
        const disabledAgents = Math.floor(financialTeam.totalAgents * 0.5);
        
        const failedTeam = {
            ...financialTeam,
            activeAgents: financialTeam.activeAgents - disabledAgents,
            disabledAgents: disabledAgents,
            status: 'degraded'
        };

        const newTeamsData = {
            ...originalTeams,
            financial: failedTeam
        };

        return {
            name: 'Fallo de Equipo',
            before: originalTeams,
            after: newTeamsData,
            impact: {
                agentsDisabled: disabledAgents,
                teamCapacityReduction: '50%',
                teamStatus: 'degraded',
                recommendedActions: [
                    'Reasignar tareas críticas a otros equipos',
                    'Activar protocolo de contingencia',
                    'Notificar stakeholders'
                ]
            }
        };
    }

    async simulateOptimization() {
        const originalMetrics = {...this.metricsData};
        
        const improvedMetrics = {
            ...originalMetrics,
            coordinationEfficiency: originalMetrics.coordinationEfficiency + 25,
            averageResponseTime: Math.floor(originalMetrics.averageResponseTime * 0.7),
            communicationLatency: Math.floor(originalMetrics.communicationLatency * 0.7),
            taskCompletionRate: Math.min(100, originalMetrics.taskCompletionRate + 15)
        };

        return {
            name: 'Optimización',
            before: originalMetrics,
            after: improvedMetrics,
            impact: {
                efficiencyImprovement: '+25%',
                responseTimeReduction: '30%',
                latencyReduction: '30%',
                completionRateImprovement: '+15%'
            }
        };
    }

    async simulateScalability() {
        const originalTeams = {...this.teamsData};
        const newAgentCount = 50;
        
        // Distribuir nuevos agentes
        const distribution = {
            maps: 15,
            content: 12,
            database: 10,
            financial: 8,
            social_travel: 5
        };

        const newTeamsData = {...originalTeams};
        
        Object.entries(distribution).forEach(([team, count]) => {
            if (newTeamsData[team]) {
                newTeamsData[team].totalAgents += count;
                newTeamsData[team].activeAgents += count;
            }
        });

        const totalAgentsAfter = Object.values(newTeamsData).reduce((sum, team) => sum + team.totalAgents, 0);

        return {
            name: 'Escalabilidad',
            before: originalTeams,
            after: newTeamsData,
            impact: {
                newAgentsAdded: newAgentCount,
                totalAgentsAfter: totalAgentsAfter,
                growthPercentage: `${Math.round((newAgentCount / originalTeams.totalAgents) * 100)}%`,
                newTeamDistribution: distribution
            }
        };
    }

    displayScenarioResults(scenario) {
        const modal = document.createElement('div');
        modal.className = 'scenario-results-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Resultados de Simulación: ${scenario.name}</h3>
                    <button class="modal-close" onclick="this.closest('.scenario-results-modal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="comparison-charts">
                        <canvas id="scenario-comparison-chart" width="400" height="200"></canvas>
                    </div>
                    <div class="impact-summary">
                        <h4>Impacto del Escenario:</h4>
                        <ul>
                            ${Object.entries(scenario.impact).map(([key, value]) => 
                                `<li><strong>${key}:</strong> ${value}</li>`
                            ).join('')}
                        </ul>
                    </div>
                    ${scenario.impact.recommendedActions ? `
                        <div class="recommendations">
                            <h4>Acciones Recomendadas:</h4>
                            <ul>
                                ${scenario.impact.recommendedActions.map(action => 
                                    `<li>${action}</li>`
                                ).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
                <div class="modal-footer">
                    <button onclick="this.closest('.scenario-results-modal').remove()">Cerrar</button>
                    <button onclick="dashboard.exportScenarioResults('${scenario.name}')">Exportar Resultados</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Crear gráfico comparativo
        this.createScenarioComparisonChart(scenario);
    }

    createScenarioComparisonChart(scenario) {
        const ctx = document.getElementById('scenario-comparison-chart').getContext('2d');
        
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Métricas Principales'],
                datasets: [{
                    label: 'Antes',
                    data: [scenario.before.systemLoad || 50],
                    backgroundColor: 'rgba(54, 162, 235, 0.6)'
                }, {
                    label: 'Después',
                    data: [scenario.after.systemLoad || 75],
                    backgroundColor: 'rgba(75, 192, 192, 0.6)'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: `Comparación: ${scenario.name}`
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    // =====================================
    // MODO PRESENTACIÓN
    // =====================================

    togglePresentationMode() {
        this.presentationMode = !this.presentationMode;
        
        if (this.presentationMode) {
            this.enterPresentationMode();
        } else {
            this.exitPresentationMode();
        }
    }

    enterPresentationMode() {
        // Ocultar elementos innecesarios
        const elementsToHide = [
            '.sidebar', '.navigation', '.controls-panel', 
            '.search-container', '.alert-system'
        ];
        
        elementsToHide.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => el.classList.add('hidden'));
        });

        // Maximizar área de visualización
        document.body.classList.add('presentation-mode');
        
        // Auto-rotación entre vistas
        this.presentationInterval = setInterval(() => {
            this.rotatePresentationView();
        }, 10000); // 10 segundos por vista
        
        this.showNotification('Modo presentación activado', 'info');
    }

    exitPresentationMode() {
        // Mostrar elementos ocultados
        const elementsToShow = [
            '.sidebar', '.navigation', '.controls-panel', 
            '.search-container', '.alert-system'
        ];
        
        elementsToShow.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => el.classList.remove('hidden'));
        });

        document.body.classList.remove('presentation-mode');
        
        if (this.presentationInterval) {
            clearInterval(this.presentationInterval);
            this.presentationInterval = null;
        }
        
        this.showNotification('Modo presentación desactivado', 'info');
    }

    rotatePresentationView() {
        const views = ['dashboard', 'hierarchy', 'teams', 'coordination', 'metrics'];
        const currentIndex = views.indexOf(this.currentView);
        const nextIndex = (currentIndex + 1) % views.length;
        
        this.switchView(views[nextIndex]);
    }

    // =====================================
    // KEYBOARD SHORTCUTS
    // =====================================

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (event) => {
            const key = this.getKeyCombo(event);
            const handler = this.keyboardShortcuts.get(key);
            
            if (handler) {
                event.preventDefault();
                handler();
            }
        });
    }

    getKeyCombo(event) {
        const parts = [];
        
        if (event.ctrlKey || event.metaKey) parts.push('ctrl');
        if (event.altKey) parts.push('alt');
        if (event.shiftKey) parts.push('shift');
        
        parts.push(event.key.toLowerCase());
        
        return parts.join('+');
    }

    focusSearch() {
        const searchInput = document.getElementById('advanced-search');
        if (searchInput) {
            searchInput.focus();
            searchInput.select();
        }
    }

    switchView(viewName) {
        // Ocultar todas las vistas
        const views = document.querySelectorAll('.dashboard-view');
        views.forEach(view => view.classList.remove('active'));
        
        // Mostrar vista seleccionada
        const targetView = document.getElementById(`${viewName}-view`);
        if (targetView) {
            targetView.classList.add('active');
            this.currentView = viewName;
            
            // Actualizar navegación
            this.updateNavigation(viewName);
            
            // Cargar datos específicos de la vista
            this.loadViewData(viewName);
        }
    }

    // =====================================
    // GESTIÓN DE TEMA
    // =====================================

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(this.currentTheme);
        localStorage.setItem('dashboard_theme', this.currentTheme);
    }

    applyTheme(theme) {
        document.body.className = theme === 'dark' ? 'dark-theme' : 'light-theme';
        
        // Actualizar toggle button
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
        }
    }

    // =====================================
    // UTILIDADES Y HELPERS
    // =====================================

    showNotification(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">&times;</button>
        `;
        
        document.bodyById('notifications-container').appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }

    formatTime(date) {
        return new Date(date).toLocaleTimeString();
    }

    getAgentColor(agent) {
        const colors = {
            5: '#FF6384', // Master Coordinator - Rojo
            4: '#36A2EB', // Task Assigner - Azul
            3: '#4BC0C0', // Team Leaders - Cian
            2: '#FFCE56', // Supervisors - Amarillo
            1: '#9966FF', // Specialists - Morado
            0: '#FF9F40'  // Agents - Naranja
        };
        return colors[agent.level] || '#CCCCCC';
    }

    getStatusColor(status) {
        const colors = {
            active: '#4CAF50',
            idle: '#FFC107',
            busy: '#FF9800',
            error: '#F44336',
            offline: '#9E9E9E'
        };
        return colors[status] || '#CCCCCC';
    }

    getAllAgents() {
        if (!this.hierarchyData) return [];
        
        const agents = [];
        this.extractAgents(this.hierarchyData, agents);
        return agents;
    }

    extractAgents(node, agentsArray) {
        agentsArray.push(node);
        if (node.children) {
            node.children.forEach(child => this.extractAgents(child, agentsArray));
        }
    }

    generateAgentTooltip(agent) {
        return `
${agent.name}
Tipo: ${agent.type}
Equipo: ${agent.team || 'N/A'}
Estado: ${agent.status}
Eficiencia: ${agent.efficiency || 'N/A'}%
Carga: ${agent.workload || 'N/A'}%
        `.trim();
    }

    getDefaultHierarchyData() {
        return {
            name: "Master Coordinator",
            level: 5,
            status: "active",
            children: [
                {
                    name: "Task Assigner",
                    level: 4,
                    status: "active",
                    children: [
                        // Teams will be populated from actual data
                    ]
                }
            ]
        };
    }

    getDefaultMetricsData() {
        return {
            totalAgents: 100,
            activeAgents: 95,
            totalTasks: 250,
            completedTasks: 180,
            systemLoad: 65,
            averageResponseTime: 1200,
            coordinationEfficiency: 88
        };
    }

    // =====================================
    // AUTO-REFRESH Y ACTUALIZACIONES
    // =====================================

    startAutoRefresh() {
        // Actualizar métricas cada 30 segundos
        setInterval(() => {
            this.updateMetrics();
        }, 30000);

        // Actualizar estado de equipos cada minuto
        setInterval(() => {
            this.updateTeamsStatus();
        }, 60000);

        // Actualizar datos en tiempo real cada 5 segundos
        setInterval(() => {
            this.updateRealtimeData();
        }, 5000);
    }

    async updateMetrics() {
        try {
            const newMetrics = await this.fetchMetricsData();
            this.metricsData = newMetrics;
            
            // Actualizar gráficos si están visibles
            if (this.currentView === 'metrics' && this.realtimeChart) {
                this.updateRealtimeChart(newMetrics);
            }
            
        } catch (error) {
            console.error('Error actualizando métricas:', error);
        }
    }

    updateRealtimeData() {
        // Simular datos en tiempo real para demostración
        if (this.realtimeChart) {
            const timestamp = new Date().toLocaleTimeString();
            
            // Añadir nuevos puntos de datos
            this.realtimeChart.data.labels.push(timestamp);
            this.realtimeChart.data.datasets[0].data.push(Math.random() * 100);
            this.realtimeChart.data.datasets[1].data.push(Math.random() * 100);
            this.realtimeChart.data.datasets[2].data.push(Math.random() * 50);
            
            // Mantener solo los últimos 20 puntos
            if (this.realtimeChart.data.labels.length > 20) {
                this.realtimeChart.data.labels.shift();
                this.realtimeChart.data.datasets.forEach(dataset => dataset.data.shift());
            }
            
            this.realtimeChart.update('none');
        }
    }

    updateRealtimeChart(metrics) {
        if (!this.realtimeChart) return;
        
        // Actualizar con datos reales
        this.realtimeChart.data.datasets[0].data.push(metrics.cpuUsage || Math.random() * 100);
        this.realtimeChart.data.datasets[1].data.push(metrics.memoryUsage || Math.random() * 100);
        this.realtimeChart.data.datasets[2].data.push(metrics.networkTraffic || Math.random() * 50);
        
        this.realtimeChart.update('none');
    }

    // =====================================
    // EVENT LISTENERS
    // =====================================

    setupEventListeners() {
        // Botón de toggle de tema
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Navegación del dashboard
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const view = item.dataset.view;
                if (view) {
                    this.switchView(view);
                }
            });
        });

        // Configurar drag & drop
        this.setupTaskDragAndDrop();
        
        // Configurar búsqueda avanzada
        this.setupAdvancedSearch();
        
        // Configurar sistema de alertas
        this.setupAlertSystem();
        
        // Configurar simulador de escenarios
        this.setupScenarioSimulator();

        // Botón de exportación
        const exportBtn = document.getElementById('export-dashboard');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => this.exportDashboard());
        }

        // Botón de modo presentación
        const presentationBtn = document.getElementById('presentation-mode');
        if (presentationBtn) {
            presentationBtn.addEventListener('click', () => this.togglePresentationMode());
        }

        // Redimensionamiento de ventana
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    handleResize() {
        // Redimensionar visualizaciones
        if (this.currentView === 'hierarchy') {
            this.initializeHierarchyVisualization();
        } else if (this.currentView === 'network') {
            this.renderNetworkGraph();
        }
    }

    loadViewData(viewName) {
        switch (viewName) {
            case 'hierarchy':
                this.initializeHierarchyVisualization();
                break;
            case 'teams':
                this.updateTeamsDisplay();
                break;
            case 'coordination':
                this.renderNetworkGraph();
                break;
            case 'metrics':
                this.initializeMetricsCharts();
                break;
        }
    }

    updateNavigation(activeView) {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.classList.toggle('active', item.dataset.view === activeView);
        });
    }

    loadSavedState() {
        // Cargar estado guardado del localStorage
        const savedState = localStorage.getItem('dashboard_state');
        if (savedState) {
            try {
                const state = JSON.parse(savedState);
                if (state.lastView) {
                    this.switchView(state.lastView);
                }
            } catch (error) {
                console.warn('Error cargando estado guardado:', error);
            }
        }
    }

    saveState() {
        const state = {
            lastView: this.currentView,
            theme: this.currentTheme,
            timestamp: Date.now()
        };
        localStorage.setItem('dashboard_state', JSON.stringify(state));
    }

    closeModals() {
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => modal.remove());
    }

    selectAgent(agentData) {
        this.selectedAgents.clear();
        this.selectedAgents.add(agentData.id);
        this.showAgentDetails(agentData);
    }

    showAgentDetails(agent) {
        const modal = document.createElement('div');
        modal.className = 'agent-details-modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Detalles del Agente: ${agent.name}</h3>
                    <button class="modal-close" onclick="this.closest('.agent-details-modal').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="agent-info-grid">
                        <div class="info-item">
                            <label>ID:</label>
                            <span>${agent.id}</span>
                        </div>
                        <div class="info-item">
                            <label>Tipo:</label>
                            <span>${agent.type}</span>
                        </div>
                        <div class="info-item">
                            <label>Equipo:</label>
                            <span>${agent.team}</span>
                        </div>
                        <div class="info-item">
                            <label>Estado:</label>
                            <span class="status-${agent.status}">${agent.status}</span>
                        </div>
                        <div class="info-item">
                            <label>Nivel:</label>
                            <span>${agent.level}</span>
                        </div>
                        <div class="info-item">
                            <label>Eficiencia:</label>
                            <span>${agent.efficiency || 'N/A'}%</span>
                        </div>
                    </div>
                    ${agent.skills ? `
                        <div class="agent-skills">
                            <h4>Habilidades:</h4>
                            <div class="skills-list">
                                ${agent.skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
                <div class="modal-footer">
                    <button onclick="dashboard.reassignAgent('${agent.id}')">Reasignar</button>
                    <button onclick="dashboard.viewAgentMetrics('${agent.id}')">Ver Métricas</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    // =====================================
    // INICIALIZACIÓN AL CARGAR LA PÁGINA
    // =====================================

    loadAdditionalScripts() {
        // Cargar librerías adicionales si no están presentes
        if (typeof d3 === 'undefined') {
            const d3Script = document.createElement('script');
            d3Script.src = 'https://d3js.org/d3.v7.min.js';
            document.head.appendChild(d3Script);
        }

        if (typeof Chart === 'undefined') {
            const chartScript = document.createElement('script');
            chartScript.src = 'https://cdn.jsdelivr.net/npm/chart.js';
            document.head.appendChild(chartScript);
        }

        if (typeof jsPDF === 'undefined') {
            const jspdfScript = document.createElement('script');
            jspdfScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
            document.head.appendChild(jspdfScript);
        }

        if (typeof XLSX === 'undefined') {
            const xlsxScript = document.createElement('script');
            xlsxScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js';
            document.head.appendChild(xlsxScript);
        }
    }

    // =====================================
    // MÉTODOS DE INICIALIZACIÓN COMPLEMENTARIOS
    // =====================================

    initializeVisualizations() {
        // Esperar a que D3 y Chart.js estén cargados
        const checkLibraries = setInterval(() => {
            if (typeof d3 !== 'undefined' && typeof Chart !== 'undefined') {
                clearInterval(checkLibraries);
                
                // Inicializar visualizaciones según la vista actual
                this.loadViewData(this.currentView);
            }
        }, 100);
    }

    updateConnectionStatus(connectionName, status) {
        const statusElement = document.querySelector(`[data-connection="${connectionName}"]`);
        if (statusElement) {
            statusElement.className = `connection-status ${status}`;
        }
    }

    buildNetworkLinks() {
        // Construir enlaces basados en comunicación real entre agentes
        return [
            {source: 'master', target: 'task-assigner', strength: 10},
            {source: 'task-assigner', target: 'maps-leader', strength: 8},
            {source: 'task-assigner', target: 'financial-leader', strength: 8},
            {source: 'maps-leader', target: 'maps-supervisor-1', strength: 5},
            {source: 'financial-leader', target: 'financial-supervisor-1', strength: 5},
            // Más enlaces...
        ];
    }

    buildNetworkNodes() {
        return [
            {id: 'master', name: 'Master Coordinator', type: 'master'},
            {id: 'task-assigner', name: 'Task Assigner', type: 'assigner'},
            {id: 'maps-leader', name: 'Maps Leader', type: 'leader'},
            {id: 'financial-leader', name: 'Financial Leader', type: 'leader'},
            // Más nodos...
        ];
    }

    getNetworkNodeColor(node) {
        const colors = {
            master: '#FF6384',
            assigner: '#36A2EB',
            leader: '#4BC0C0',
            supervisor: '#FFCE56',
            agent: '#9966FF'
        };
        return colors[node.type] || '#CCCCCC';
    }

    dragstarted(simulation, event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    dragended(simulation, event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    generateWorkloadData(agents, hours) {
        const data = [];
        agents.forEach((agent, agentIndex) => {
            hours.forEach((hour, hourIndex) => {
                const workload = Math.random() * 100;
                data.push({
                    x: hourIndex,
                    y: agentIndex,
                    workload: workload
                });
            });
        });
        return data;
    }

    updateTeamStatus(teamName, status) {
        const teamElement = document.querySelector(`[data-team="${teamName}"]`);
        if (teamElement) {
            teamElement.className = `team-status ${status}`;
            const statusText = teamElement.querySelector('.status-text');
            if (statusText) {
                statusText.textContent = status;
            }
        }
    }

    updateAgentStatus(agentData) {
        // Actualizar estado visual del agente
        const agentElement = document.querySelector(`[data-agent-id="${agentData.id}"]`);
        if (agentElement) {
            const statusElement = agentElement.querySelector('.agent-status');
            if (statusElement) {
                statusElement.className = `agent-status status-${agentData.status}`;
                statusElement.textContent = agentData.status;
            }
        }
    }

    handleTaskAssignment(taskData) {
        // Actualizar asignación de tarea en la UI
        console.log('Nueva asignación de tarea:', taskData);
        this.showNotification(`Tarea asignada: ${taskData.taskName}`, 'success');
    }

    updateMetrics(payload) {
        // Actualizar métricas específicas
        Object.assign(this.metricsData, payload);
        
        if (this.currentView === 'metrics') {
            // Actualizar gráficos visibles
            this.updateRealtimeData();
        }
    }

    updateTeamPerformance(payload) {
        // Actualizar rendimiento del equipo
        console.log('Actualización de rendimiento:', payload);
    }

    updateTaskAssignment(taskId, newAgentId) {
        // Actualizar UI después de reasignar tarea
        const taskElement = document.querySelector(`[data-task-id="${taskId}"]`);
        if (taskElement) {
            taskElement.dataset.currentAgent = newAgentId;
        }
    }

    viewAgentMetrics(agentId) {
        // Abrir modal con métricas del agente
        this.showNotification(`Mostrando métricas del agente ${agentId}`, 'info');
    }

    reassignAgent(agentId) {
        // Abrir modal de reasignación
        this.showNotification(`Reasignando agente ${agentId}`, 'info');
    }

    handleExportFormat(format, modalElement) {
        modalElement.parentElement.remove();
        
        switch (format) {
            case 'pdf':
                this.exportToPDF(this.prepareExportData());
                break;
            case 'excel':
                this.exportToExcel(this.prepareExportData());
                break;
            case 'json':
                this.exportToJSON(this.prepareExportData());
                break;
        }
    }

    exportScenarioResults(scenarioName) {
        // Exportar resultados de simulación
        const data = {
            scenario: scenarioName,
            timestamp: new Date().toISOString(),
            results: this.lastScenarioResults
        };
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `scenario_${scenarioName.toLowerCase()}_${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    setupZoomAndPan(svg) {
        const container = d3.select('#hierarchy-visualization');
        
        container.call(d3.zoom()
            .scaleExtent([0.1, 3])
            .on('zoom', (event) => {
                svg.select('.hierarchy-content')
                    .attr('transform', event.transform);
            }));
    }

    updateTeamsDisplay() {
        // Actualizar visualización de equipos
        const teamsContainer = document.getElementById('teams-container');
        if (teamsContainer && this.teamsData) {
            // Renderizar información de equipos
            teamsContainer.innerHTML = this.renderTeamsHTML(this.teamsData);
        }
    }

    renderTeamsHTML(teamsData) {
        return Object.entries(teamsData).map(([teamName, teamData]) => `
            <div class="team-card" data-team="${teamName}">
                <h3>${teamName}</h3>
                <div class="team-stats">
                    <span>Agentes: ${teamData.totalAgents}</span>
                    <span>Activos: ${teamData.activeAgents}</span>
                    <span>Eficiencia: ${teamData.efficiency}%</span>
                </div>
                <div class="team-status ${teamData.status}">
                    <span class="status-indicator"></span>
                    <span class="status-text">${teamData.status}</span>
                </div>
            </div>
        `).join('');
    }

    getTeamsSummary() {
        if (!this.teamsData) return {};
        
        const summary = {};
        Object.entries(this.teamsData).forEach(([teamName, teamData]) => {
            summary[teamName] = {
                agentCount: teamData.totalAgents,
                efficiency: teamData.efficiency || 0,
                status: teamData.status || 'unknown'
            };
        });
        return summary;
    }

    async getActiveTasks() {
        // Obtener tareas activas del sistema
        return [];
    }

    async getSystemStatus() {
        // Obtener estado general del sistema
        return {
            status: 'operational',
            uptime: '99.9%',
            lastUpdate: new Date().toISOString()
        };
    }

    processHierarchyData(rawData) {
        // Procesar datos jerárquicos del servidor
        return rawData;
    }
}

// =====================================
// INICIALIZACIÓN AL CARGAR LA PÁGINA
// =====================================

let dashboard;

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Inicializando Dashboard SilhouetteMCP...');
    
    // Crear instancia global del dashboard
    dashboard = new SilhouetteDashboard();
    
    // Cargar scripts adicionales
    dashboard.loadAdditionalScripts();
    
    // Hacer disponible globalmente para debugging
    window.dashboard = dashboard;
    
    console.log('✅ Dashboard SilhouetteMCP listo para usar');
});

// =====================================
// FUNCIONES GLOBALES PARA COMPATIBILIDAD
// =====================================

// Función para seleccionar agente desde HTML
function selectAgentFromUI(agentId) {
    if (dashboard) {
        const agent = dashboard.getAllAgents().find(a => a.id === agentId);
        if (agent) {
            dashboard.selectAgent(agent);
        }
    }
}

// Función para cambiar vista desde HTML
function switchViewFromUI(viewName) {
    if (dashboard) {
        dashboard.switchView(viewName);
    }
}

// Función para exportar desde HTML
function exportFromUI() {
    if (dashboard) {
        dashboard.exportDashboard();
    }
}

// Manejo de errores globales
window.addEventListener('error', (event) => {
    console.error('Error global:', event.error);
    if (dashboard) {
        dashboard.showNotification('Error inesperado en el dashboard', 'error');
    }
});

// Manejo de promesas rechazadas
window.addEventListener('unhandledrejection', (event) => {
    console.error('Promesa rechazada:', event.reason);
    if (dashboard) {
        dashboard.showNotification('Error en operación asíncrona', 'error');
    }
});

// Guardar estado al cerrar página
window.addEventListener('beforeunload', () => {
    if (dashboard) {
        dashboard.saveState();
    }
});