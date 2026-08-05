# Dashboard Jerárquico SilhouetteMCP - Documentación de Integración API

## Descripción General

Este documento describe la integración completa entre el Dashboard Jerárquico de SilhouetteMCP y el sistema de 100+ agentes. El dashboard proporciona una interfaz web avanzada para monitoreo, gestión y coordinación de toda la arquitectura multi-agente.

## Arquitectura del Sistema

### Puertos y Endpoints

El dashboard se conecta con múltiples servidores especializados:

| Puerto | Servicio | Propósito | Endpoints Principales |
|--------|----------|-----------|----------------------|
| **8001** | Master Server | Coordinación principal | `/api/hierarchy`, `/api/assign_task` |
| **8002** | Maps Team | Equipo de Mapas (15 agentes) | `/api/status`, `/ws` |
| **8003** | Financial Team | Equipo Financiero (20 agentes) | `/api/status`, `/ws` |
| **8004** | Social/Travel Team | Social + Travel (18 agentes) | `/api/status`, `/ws` |
| **8005** | Content Team | Creación de Contenido (12 agentes) | `/api/status`, `/ws` |
| **8006** | Database Team | Operaciones BD (15 agentes) | `/api/status`, `/ws` |
| **8007** | Research Team | Inteligencia (8 agentes) | `/api/status`, `/ws` |
| **8008** | Support Team | Sistemas de Soporte (10 agentes) | `/api/status`, `/ws` |
| **8009** | Coordination Server | Coordinación inter-equipos | `/api/coordination` |
| **8010** | Metrics Server | Métricas y Analytics | `/api/metrics` |

## Estructura de Datos Jerárquicos

### Formato de Datos del Sistema

```json
{
  "id": "master_coordinator",
  "name": "Master Coordinator",
  "type": "master",
  "level": 5,
  "status": "active",
  "team": "master",
  "efficiency": 95,
  "workload": 45,
  "skills": ["coordination", "strategy", "leadership"],
  "children": [
    {
      "id": "task_assigner",
      "name": "Intelligent Task Assigner",
      "type": "assigner",
      "level": 4,
      "status": "active",
      "team": "coordination",
      "efficiency": 92,
      "children": [
        {
          "id": "maps_leader",
          "name": "Maps Team Leader",
          "type": "leader",
          "level": 3,
          "status": "active",
          "team": "maps",
          "efficiency": 88,
          "children": [
            {
              "id": "maps_supervisor_1",
              "name": "Maps Supervisor North",
              "type": "supervisor",
              "level": 2,
              "status": "active",
              "team": "maps",
              "children": [
                {
                  "id": "maps_agent_001",
                  "name": "Geospatial Analysis Agent",
                  "type": "specialist",
                  "level": 1,
                  "status": "active",
                  "team": "maps",
                  "skills": ["gis", "geospatial", "mapping"]
                }
                // ... más agentes especializados
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## Endpoints API Detallados

### 1. Master Server (Puerto 8001)

#### `GET /api/hierarchy`
**Propósito:** Obtener estructura jerárquica completa del sistema

**Respuesta:**
```json
{
  "totalAgents": 100,
  "structure": {
    // Datos jerárquicos como se muestra arriba
  },
  "lastUpdate": "2025-11-06T03:20:32Z"
}
```

#### `POST /api/assign_task`
**Propósito:** Asignar tarea entre agentes

**Body:**
```json
{
  "taskId": "task_123",
  "fromAgent": "maps_agent_001",
  "toAgent": "financial_agent_015",
  "priority": "high",
  "estimatedDuration": 3600,
  "dependencies": ["task_122"],
  "timestamp": "2025-11-06T03:20:32Z"
}
```

**Respuesta:**
```json
{
  "success": true,
  "assignmentId": "assign_456",
  "newAgent": "financial_agent_015",
  "estimatedCompletion": "2025-11-06T04:20:32Z"
}
```

#### `WebSocket /ws`
**Propósito:** Actualizaciones en tiempo real del coordinador principal

**Mensajes:**
- `agent_status_update`: Cambios en estado de agentes
- `task_assignment`: Nuevas asignaciones de tareas
- `system_alert`: Alertas críticas del sistema
- `coordination_message`: Mensajes de coordinación FIPA-ACL

### 2. Teams Servers (Puertos 8002-8008)

#### `GET /api/status`
**Propósito:** Estado detallado del equipo

**Respuesta (ejemplo para Maps Team):**
```json
{
  "teamName": "maps",
  "totalAgents": 15,
  "activeAgents": 13,
  "idleAgents": 2,
  "efficiency": 88.5,
  "averageWorkload": 65.2,
  "performance": {
    "tasksCompleted": 247,
    "averageResponseTime": 1200,
    "successRate": 0.94
  },
  "agentDetails": [
    {
      "id": "maps_agent_001",
      "name": "Geospatial Analysis Agent",
      "status": "active",
      "currentTask": "analyze_geographic_data",
      "workload": 75,
      "efficiency": 92
    }
    // ... más agentes
  ]
}
```

#### `WebSocket /ws`
**Propósito:** Updates en tiempo real del equipo

### 3. Metrics Server (Puerto 8010)

#### `GET /api/metrics`
**Propósito:** Métricas del sistema en tiempo real

**Respuesta:**
```json
{
  "timestamp": "2025-11-06T03:20:32Z",
  "systemMetrics": {
    "cpuUsage": 45.2,
    "memoryUsage": 62.8,
    "networkTraffic": 125.6,
    "activeConnections": 98,
    "queueLength": 12
  },
  "agentMetrics": {
    "totalAgents": 100,
    "activeAgents": 95,
    "idleAgents": 5,
    "averageEfficiency": 87.3
  },
  "taskMetrics": {
    "totalTasks": 156,
    "completedTasks": 142,
    "pendingTasks": 14,
    "failedTasks": 0
  },
  "teamPerformance": {
    "maps": { "efficiency": 88, "agentCount": 15 },
    "financial": { "efficiency": 92, "agentCount": 20 },
    "social_travel": { "efficiency": 82, "agentCount": 18 },
    "content": { "efficiency": 90, "agentCount": 12 },
    "database": { "efficiency": 95, "agentCount": 15 },
    "research": { "efficiency": 85, "agentCount": 8 },
    "support": { "efficiency": 91, "agentCount": 10 }
  }
}
```

#### `GET /api/metrics/history`
**Propósito:** Métricas históricas para gráficos

**Query Parameters:**
- `timeRange`: 1h, 6h, 24h, 7d, 30d
- `granularity`: 1m, 5m, 15m, 1h
- `metrics`: cpu,memory,tasks,efficiency

#### `GET /api/workload/heatmap`
**Propósito:** Datos para heatmap de carga de trabajo

**Respuesta:**
```json
{
  "agents": ["maps_agent_001", "maps_agent_002", ...],
  "timeSlots": ["00:00", "01:00", ..., "23:00"],
  "workloadMatrix": [
    [45, 52, 38, ...],  // Agent 1 workload por hora
    [67, 71, 58, ...],  // Agent 2 workload por hora
    ...
  ]
}
```

#### `GET /api/projects/gantt`
**Propósito:** Datos para Gantt chart de proyectos

**Respuesta:**
```json
{
  "projects": [
    {
      "id": "proj_001",
      "name": "Sistema Maps V2",
      "team": "maps",
      "startDate": "2025-11-01",
      "duration": 15,
      "progress": 60,
      "status": "active",
      "assignedAgents": ["maps_agent_001", "maps_agent_003"]
    }
    // ... más proyectos
  ]
}
```

### 4. Coordination Server (Puerto 8009)

#### `GET /api/coordination/flows`
**Propósito:** Flujos de comunicación entre equipos

**Respuesta:**
```json
{
  "coordinationFlows": [
    {
      "from": "maps_team",
      "to": "financial_team",
      "project": "location_based_financial_analysis",
      "communicationFrequency": "high",
      "dataExchange": "geographic_financial_data",
      "bottlenecks": []
    }
    // ... más flujos
  ]
}
```

#### `GET /api/coordination/algorithms`
**Propósito:** Estado de algoritmos de coordinación

**Respuesta:**
```json
{
  "algorithms": {
    "raft": {
      "status": "active",
      "leader": "master_coordinator",
      "consensusNodes": 5,
      "lastConsensus": "2025-11-06T03:19:32Z"
    },
    "cbba": {
      "status": "active",
      "bundleCount": 12,
      "consensusRounds": 3,
      "successRate": 0.89
    },
    "hungarian": {
      "status": "active",
      "assignmentEfficiency": 0.94,
      "lastOptimization": "2025-11-06T03:18:45Z"
    }
  }
}
```

## Protocolos de Comunicación

### WebSocket Message Format

Todos los mensajes WebSocket siguen el formato:

```json
{
  "type": "message_type",
  "timestamp": "2025-11-06T03:20:32Z",
  "source": "agent_id_or_team",
  "payload": {
    // Datos específicos del mensaje
  }
}
```

### Tipos de Mensajes WebSocket

#### `agent_status_update`
```json
{
  "type": "agent_status_update",
  "timestamp": "2025-11-06T03:20:32Z",
  "source": "maps_agent_001",
  "payload": {
    "agentId": "maps_agent_001",
    "previousStatus": "active",
    "newStatus": "busy",
    "currentTask": "geospatial_analysis",
    "workload": 85,
    "location": {"lat": 40.7128, "lng": -74.0060}
  }
}
```

#### `task_assignment`
```json
{
  "type": "task_assignment",
  "timestamp": "2025-11-06T03:20:32Z",
  "source": "task_assigner",
  "payload": {
    "taskId": "task_456",
    "taskName": "Analyze traffic patterns",
    "assignedAgent": "maps_agent_005",
    "priority": "medium",
    "estimatedDuration": 1800,
    "dependencies": []
  }
}
```

#### `metrics_update`
```json
{
  "type": "metrics_update",
  "timestamp": "2025-11-06T03:20:32Z",
  "source": "metrics_server",
  "payload": {
    "cpuUsage": 45.2,
    "memoryUsage": 62.8,
    "activeTasks": 156,
    "queueLength": 12
  }
}
```

#### `alert`
```json
{
  "type": "alert",
  "timestamp": "2025-11-06T03:20:32Z",
  "source": "financial_agent_012",
  "payload": {
    "alertId": "alert_789",
    "type": "warning",
    "priority": "high",
    "title": "High processing load",
    "message": "Financial analysis agent experiencing high CPU usage",
    "agent": "financial_agent_012",
    "team": "financial",
    "details": {
      "cpuUsage": 95.2,
      "currentTasks": 8,
      "queueLength": 15
    }
  }
}
```

## Configuración del Dashboard

### Variables de Configuración

```javascript
const dashboardConfig = {
    apiBaseUrls: {
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
    },
    websocketEndpoints: {
        master: 'ws://localhost:8001/ws',
        maps: 'ws://localhost:8002/ws',
        financial: 'ws://localhost:8003/ws',
        // ... más endpoints WebSocket
    },
    refreshIntervals: {
        metrics: 30000,      // 30 segundos
        teamStatus: 60000,   // 1 minuto
        realtime: 5000       // 5 segundos
    },
    features: {
        dragAndDrop: true,
        exportPDF: true,
        exportExcel: true,
        scenarioSimulator: true,
        presentationMode: true,
        advancedSearch: true,
        alertSystem: true
    }
};
```

### Autenticación y Seguridad

#### JWT Token Authentication

```javascript
const authConfig = {
    tokenEndpoint: 'http://localhost:8001/auth/token',
    refreshEndpoint: 'http://localhost:8001/auth/refresh',
    tokenKey: 'silhouette_jwt_token',
    refreshBefore: 300000, // 5 minutos antes de expirar
    headers: {
        'Authorization': 'Bearer {jwt_token}',
        'Content-Type': 'application/json'
    }
};
```

#### Request Interceptor

```javascript
class APIInterceptor {
    constructor() {
        this.setupInterceptors();
    }

    setupInterceptors() {
        // Request interceptor para añadir tokens
        fetch = fetchWithAuth;
    }

    async fetchWithAuth(url, options = {}) {
        const token = this.getValidToken();
        
        if (token) {
            options.headers = {
                ...options.headers,
                'Authorization': `Bearer ${token}`
            };
        }

        try {
            const response = await fetch(url, options);
            
            if (response.status === 401) {
                // Token expirado, intentar refresh
                const newToken = await this.refreshToken();
                if (newToken) {
                    options.headers.Authorization = `Bearer ${newToken}`;
                    return fetch(url, options);
                }
            }
            
            return response;
        } catch (error) {
            console.error('Error en request:', error);
            throw error;
        }
    }
}
```

## Manejo de Errores

### Estrategia de Retry

```javascript
class APIRetryHandler {
    constructor() {
        this.maxRetries = 3;
        this.retryDelays = [1000, 3000, 5000]; // 1s, 3s, 5s
    }

    async requestWithRetry(requestFn, ...args) {
        for (let attempt = 0; attempt < this.maxRetries; attempt++) {
            try {
                return await requestFn(...args);
            } catch (error) {
                if (attempt === this.maxRetries - 1) {
                    throw error;
                }
                
                console.warn(`Request fallido, intento ${attempt + 1}/${this.maxRetries}:`, error);
                await this.delay(this.retryDelays[attempt]);
            }
        }
    }

    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

### Fallback Data

```javascript
class FallbackDataProvider {
    getDefaultHierarchy() {
        return {
            name: "Master Coordinator",
            level: 5,
            status: "active",
            children: [
                {
                    name: "Task Assigner",
                    level: 4,
                    status: "active",
                    children: []
                }
            ]
        };
    }

    getDefaultMetrics() {
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

    generateMockTeamData() {
        const teams = ['maps', 'financial', 'social_travel', 'content', 'database', 'research', 'support'];
        return teams.map(team => ({
            name: team,
            agentCount: Math.floor(Math.random() * 20) + 5,
            efficiency: Math.floor(Math.random() * 30) + 70,
            status: Math.random() > 0.1 ? 'active' : 'warning'
        }));
    }
}
```

## Optimización de Performance

### Data Caching

```javascript
class DataCache {
    constructor() {
        this.cache = new Map();
        this.cacheExpiry = new Map();
        this.defaultTTL = 5 * 60 * 1000; // 5 minutos
    }

    set(key, data, ttl = this.defaultTTL) {
        this.cache.set(key, data);
        this.cacheExpiry.set(key, Date.now() + ttl);
    }

    get(key) {
        if (this.cache.has(key)) {
            if (Date.now() < this.cacheExpiry.get(key)) {
                return this.cache.get(key);
            } else {
                this.cache.delete(key);
                this.cacheExpiry.delete(key);
            }
        }
        return null;
    }

    invalidate(key) {
        this.cache.delete(key);
        this.cacheExpiry.delete(key);
    }

    clear() {
        this.cache.clear();
        this.cacheExpiry.clear();
    }
}
```

### Virtual Scrolling para Listas Grandes

```javascript
class VirtualList {
    constructor(container, itemHeight, totalItems) {
        this.container = container;
        this.itemHeight = itemHeight;
        this.totalItems = totalItems;
        this.visibleItems = Math.ceil(container.clientHeight / itemHeight);
        this.startIndex = 0;
        this.endIndex = this.visibleItems;
        
        this.setupContainer();
        this.renderItems();
    }

    setupContainer() {
        this.container.style.height = `${this.totalItems * this.itemHeight}px`;
        this.container.style.position = 'relative';
        this.container.addEventListener('scroll', this.handleScroll.bind(this));
    }

    handleScroll() {
        const scrollTop = this.container.scrollTop;
        const newStartIndex = Math.floor(scrollTop / this.itemHeight);
        const newEndIndex = Math.min(
            newStartIndex + this.visibleItems + 1,
            this.totalItems
        );

        if (newStartIndex !== this.startIndex || newEndIndex !== this.endIndex) {
            this.startIndex = newStartIndex;
            this.endIndex = newEndIndex;
            this.renderItems();
        }
    }

    renderItems() {
        // Implementar renderizado virtual
    }
}
```

## Testing y Debugging

### Mock API Server

```javascript
class MockAPIServer {
    constructor() {
        this.setupRoutes();
    }

    setupRoutes() {
        // Mock hierarchy endpoint
        app.get('/api/hierarchy', (req, res) => {
            res.json(this.getMockHierarchyData());
        });

        // Mock metrics endpoint
        app.get('/api/metrics', (req, res) => {
            res.json(this.getMockMetricsData());
        });

        // Mock WebSocket
        this.setupMockWebSocket();
    }

    getMockHierarchyData() {
        return {
            totalAgents: 100,
            structure: this.generateMockHierarchy(),
            lastUpdate: new Date().toISOString()
        };
    }

    generateMockHierarchy() {
        // Generar estructura jerárquica de prueba
        return {
            name: "Master Coordinator",
            level: 5,
            status: "active",
            children: [
                {
                    name: "Task Assigner",
                    level: 4,
                    status: "active",
                    children: this.generateMockTeams()
                }
            ]
        };
    }

    generateMockTeams() {
        const teams = ['maps', 'financial', 'social_travel', 'content', 'database', 'research', 'support'];
        return teams.map(team => ({
            name: `${team.charAt(0).toUpperCase() + team.slice(1)} Team Leader`,
            level: 3,
            status: "active",
            team: team,
            children: this.generateMockAgents(team)
        }));
    }

    generateMockAgents(team) {
        const agentCount = {
            maps: 15, financial: 20, social_travel: 18, 
            content: 12, database: 15, research: 8, support: 10
        }[team] || 10;

        return Array.from({length: agentCount}, (_, i) => ({
            name: `${team.charAt(0).toUpperCase() + team.slice(1)} Agent ${i + 1}`,
            level: Math.random() > 0.3 ? 1 : 2,
            status: Math.random() > 0.1 ? 'active' : 'idle',
            team: team,
            efficiency: Math.floor(Math.random() * 40) + 60
        }));
    }
}
```

### Debug Panel

```javascript
class DebugPanel {
    constructor() {
        this.isEnabled = localStorage.getItem('debug_enabled') === 'true';
        this.setupPanel();
    }

    setupPanel() {
        if (!this.isEnabled) return;

        const debugPanel = document.createElement('div');
        debugPanel.id = 'debug-panel';
        debugPanel.innerHTML = `
            <div class="debug-header">
                <h4>Debug Panel</h4>
                <button onclick="debugPanel.toggle()">Toggle</button>
            </div>
            <div class="debug-content">
                <div class="debug-section">
                    <h5>API Status</h5>
                    <div id="api-status"></div>
                </div>
                <div class="debug-section">
                    <h5>WebSocket Connections</h5>
                    <div id="ws-status"></div>
                </div>
                <div class="debug-section">
                    <h5>Performance</h5>
                    <div id="perf-metrics"></div>
                </div>
            </div>
        `;
        document.body.appendChild(debugPanel);

        this.startMonitoring();
    }

    startMonitoring() {
        setInterval(() => {
            this.updateAPIsStatus();
            this.updateWebSocketStatus();
            this.updatePerformanceMetrics();
        }, 2000);
    }

    updateAPIsStatus() {
        const status = document.getElementById('api-status');
        const apis = ['master', 'maps', 'financial', 'social_travel', 'content', 'database', 'research', 'support'];
        
        status.innerHTML = apis.map(api => {
            const isConnected = dashboard.websocketConnections.has(api);
            return `<div class="api-status ${api} ${isConnected ? 'connected' : 'disconnected'}">${api}: ${isConnected ? '✅' : '❌'}</div>`;
        }).join('');
    }

    updateWebSocketStatus() {
        const status = document.getElementById('ws-status');
        status.innerHTML = Array.from(dashboard.websocketConnections.entries())
            .map(([name, ws]) => `<div class="ws-status">${name}: ${ws.readyState === 1 ? '🟢' : '🔴'}</div>`)
            .join('');
    }

    updatePerformanceMetrics() {
        const metrics = document.getElementById('perf-metrics');
        metrics.innerHTML = `
            <div>Memory: ${performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1024 / 1024) : 'N/A'} MB</div>
            <div>Load Time: ${performance.now().toFixed(2)} ms</div>
            <div>Active Agents: ${dashboard.getAllAgents().filter(a => a.status === 'active').length}</div>
        `;
    }

    toggle() {
        const panel = document.getElementById('debug-panel');
        panel.classList.toggle('collapsed');
    }
}
```

## Despliegue y Configuración

### Variables de Entorno

```bash
# .env file
SILHOUETTE_API_BASE=http://localhost
SILHOUETTE_WS_BASE=ws://localhost
SILHOUETTE_REFRESH_INTERVAL=30000
SILHOUETTE_MAX_ALERTS=10
SILHOUETTE_DEFAULT_THEME=dark
SILHOUETTE_ENABLE_DEBUG=false
SILHOUETTE_EXPORT_TIMEOUT=30000
```

### Docker Configuration

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name silhouette-dashboard.local;
    
    root /var/www/silhouette-dashboard;
    index index.html;
    
    # Proxy API requests to SilhouetteMCP servers
    location /api/master {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/metrics {
        proxy_pass http://localhost:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket proxy
    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Static files with caching
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## Monitoreo y Logs

### Logger del Dashboard

```javascript
class DashboardLogger {
    constructor() {
        this.logs = [];
        this.maxLogs = 1000;
        this.setupConsoleLogging();
    }

    log(level, message, data = {}) {
        const logEntry = {
            timestamp: new Date().toISOString(),
            level: level,
            message: message,
            data: data,
            url: window.location.href,
            userAgent: navigator.userAgent
        };

        this.logs.push(logEntry);
        
        if (this.logs.length > this.maxLogs) {
            this.logs.shift();
        }

        // Enviar logs al servidor si está configurado
        this.sendToServer(logEntry);
    }

    info(message, data) {
        this.log('info', message, data);
        console.info(message, data);
    }

    warn(message, data) {
        this.log('warn', message, data);
        console.warn(message, data);
    }

    error(message, data) {
        this.log('error', message, data);
        console.error(message, data);
    }

    sendToServer(logEntry) {
        // Enviar a endpoint de logging si está disponible
        fetch('/api/logs', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(logEntry)
        }).catch(() => {
            // Silently fail if logging server is not available
        });
    }

    setupConsoleLogging() {
        const originalError = console.error;
        const originalWarn = console.warn;
        
        console.error = (...args) => {
            this.error(args.join(' '), {args});
            originalError.apply(console, args);
        };
        
        console.warn = (...args) => {
            this.warn(args.join(' '), {args});
            originalWarn.apply(console, args);
        };
    }

    getLogs(level = null, limit = 100) {
        let filteredLogs = this.logs;
        
        if (level) {
            filteredLogs = this.logs.filter(log => log.level === level);
        }
        
        return filteredLogs.slice(-limit);
    }

    exportLogs() {
        const blob = new Blob([JSON.stringify(this.logs, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `silhouette_dashboard_logs_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
    }
}

// Global logger instance
window.dashboardLogger = new DashboardLogger();
```

### Analytics y Métricas de Uso

```javascript
class DashboardAnalytics {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.pageViews = [];
        this.userInteractions = [];
        this.performanceMetrics = [];
        this.setupEventTracking();
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    setupEventTracking() {
        // Track page views
        this.trackPageView();
        
        // Track user interactions
        document.addEventListener('click', (e) => {
            this.trackInteraction('click', {
                element: e.target.tagName,
                id: e.target.id,
                className: e.target.className,
                text: e.target.textContent?.substring(0, 50)
            });
        });

        // Track view changes
        window.addEventListener('hashchange', () => {
            this.trackPageView();
        });

        // Track performance metrics
        this.trackPerformanceMetrics();
    }

    trackPageView() {
        const pageView = {
            sessionId: this.sessionId,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            title: document.title,
            referrer: document.referrer
        };

        this.pageViews.push(pageView);
        this.sendAnalytics('page_view', pageView);
    }

    trackInteraction(type, data) {
        const interaction = {
            sessionId: this.sessionId,
            timestamp: new Date().toISOString(),
            type: type,
            data: data
        };

        this.userInteractions.push(interaction);
        this.sendAnalytics('interaction', interaction);
    }

    trackPerformanceMetrics() {
        const perfData = {
            sessionId: this.sessionId,
            timestamp: new Date().toISOString(),
            url: window.location.href,
            loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
            domContentLoaded: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
            memoryUsage: performance.memory ? performance.memory.usedJSHeapSize : 0,
            connectionType: navigator.connection?.effectiveType || 'unknown'
        };

        this.performanceMetrics.push(perfData);
        this.sendAnalytics('performance', perfData);

        // Continue tracking every 30 seconds
        setTimeout(() => this.trackPerformanceMetrics(), 30000);
    }

    sendAnalytics(eventType, data) {
        // Enviar a servicio de analytics (ej. Google Analytics, Mixpanel, etc.)
        if (typeof gtag !== 'undefined') {
            gtag('event', eventType, {
                custom_parameter_1: JSON.stringify(data)
            });
        }

        // O enviar a endpoint propio
        fetch('/api/analytics', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                eventType: eventType,
                data: data,
                userAgent: navigator.userAgent,
                timestamp: new Date().toISOString()
            })
        }).catch(() => {
            // Silently fail if analytics server is not available
        });
    }
}
```

## Conclusión

Esta documentación cubre la integración completa entre el Dashboard Jerárquico de SilhouetteMCP y el sistema de 100+ agentes. El dashboard proporciona:

### Características Implementadas

✅ **Visualización Jerárquica Completa** con D3.js  
✅ **Gráficos en Tiempo Real** con Chart.js  
✅ **WebSocket Connections** para updates instantáneos  
✅ **Drag & Drop** para reasignación de tareas  
✅ **Sistema de Alertas Inteligentes**  
✅ **Búsqueda Avanzada** con múltiples filtros  
✅ **Exportación Multi-formato** (PDF, Excel, JSON)  
✅ **Simulador de Escenarios** para análisis predictivo  
✅ **Modo Presentación** para demos  
✅ **Keyboard Shortcuts** para usuarios avanzados  
✅ **Temas Personalizables** con persistencia  
✅ **Integración Completa** con 7 equipos especializados  

### Arquitectura Escalable

El sistema está diseñado para manejar:
- **100+ agentes** distribuidos en 7 equipos
- **Múltiples niveles jerárquicos** (5 niveles)
- **Comunicación en tiempo real** vía WebSocket
- **Múltiples formatos de datos** (JSON, métricas, alertas)
- **Interfaz responsive** para todos los dispositivos
- **Sistema de caching** para optimización
- **Manejo robusto de errores** con fallback data

### Próximos Pasos

1. **Deploy del Backend**: Asegurar que los servidores SilhouetteMCP estén ejecutándose en puertos 8001-8010
2. **Configuración de Autenticación**: Implementar JWT tokens si es requerido
3. **Customización de Temas**: Adaptar colores y estilos según branding
4. **Testing Completo**: Ejecutar pruebas de integración con todos los endpoints
5. **Optimización**: Ajustar intervalos de refresh según carga del sistema

El Dashboard Jerárquico de SilhouetteMCP representa la solución más avanzada para gestión y visualización de sistemas multi-agente, proporcionando una interfaz intuitiva y potente para administrar eficientemente toda la arquitectura de 100+ agentes especializados.