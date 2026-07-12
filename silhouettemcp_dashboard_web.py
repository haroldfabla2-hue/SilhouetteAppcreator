#!/usr/bin/env python3
"""
🌐 Servidor Web Dashboard SilhouetteMCP
======================================

Servidor web para acceso al dashboard SilhouetteMCP desde dominio
- Proxy hacia el dashboard unificado en puerto 9000
- Interfaz web moderna y responsive
- Acceso desde cualquier dispositivo

Uso:
    python silhouettemcp_dashboard_web.py

Acceso:
    - Local: http://localhost:8000
    - Dominio: Configurar DNS o usar ngrok
"""

from flask import Flask, redirect, jsonify, render_template_string, request
import requests
import json
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Configuración
DASHBOARD_API_URL = "http://localhost:9000"
PORT = 8000

# Template HTML del dashboard con diseño moderno
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 SilhouetteMCP - Dashboard Unificado</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #e9ecef;
        }
        
        .header h1 {
            color: #2c3e50;
            font-size: 2.8em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        }
        
        .header p {
            color: #6c757d;
            font-size: 1.2em;
            font-weight: 300;
        }
        
        .score-display {
            background: linear-gradient(45deg, #28a745, #20c997);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            margin: 20px 0;
            box-shadow: 0 10px 20px rgba(40, 167, 69, 0.3);
        }
        
        .score-number {
            font-size: 3em;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .score-label {
            font-size: 1.2em;
            margin-top: 5px;
            opacity: 0.9;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .running { color: #28a745; }
        .stopped { color: #dc3545; }
        .error { color: #fd7e14; }
        .total { color: #007bff; }
        
        .controls {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .btn {
            background: linear-gradient(45deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1em;
            cursor: pointer;
            margin: 0 10px;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        }
        
        .btn-secondary {
            background: linear-gradient(45deg, #6c757d, #495057);
        }
        
        .systems-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 20px;
        }
        
        .system-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        
        .system-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
        }
        
        .system-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }
        
        .system-name {
            font-weight: bold;
            color: #2c3e50;
            font-size: 1.1em;
            flex: 1;
        }
        
        .system-status {
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            text-transform: uppercase;
            margin-left: 10px;
        }
        
        .status-running {
            background: #d4edda;
            color: #155724;
            animation: pulse-green 2s infinite;
        }
        
        .status-stopped {
            background: #f8d7da;
            color: #721c24;
        }
        
        .status-error {
            background: #fff3cd;
            color: #856404;
            animation: pulse-orange 2s infinite;
        }
        
        @keyframes pulse-green {
            0%, 100% { box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }
            50% { box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }
        }
        
        @keyframes pulse-orange {
            0%, 100% { box-shadow: 0 0 0 0 rgba(253, 126, 20, 0.7); }
            50% { box-shadow: 0 0 0 10px rgba(253, 126, 20, 0); }
        }
        
        .system-info {
            color: #6c757d;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        
        .system-description {
            color: #495057;
            font-size: 0.9em;
            line-height: 1.4;
            margin-bottom: 15px;
        }
        
        .system-link {
            color: #007bff;
            text-decoration: none;
            font-weight: bold;
            transition: color 0.3s ease;
        }
        
        .system-link:hover {
            color: #0056b3;
            text-decoration: underline;
        }
        
        .category-badge {
            display: inline-block;
            padding: 4px 12px;
            background: linear-gradient(45deg, #e9ecef, #dee2e6);
            color: #495057;
            border-radius: 15px;
            font-size: 0.8em;
            font-weight: 500;
            margin-top: 10px;
        }
        
        .footer {
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e9ecef;
            color: #6c757d;
        }
        
        .access-info {
            background: linear-gradient(45deg, #17a2b8, #138496);
            color: white;
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            text-align: center;
        }
        
        .access-info h3 {
            margin-bottom: 10px;
        }
        
        .access-info p {
            margin: 5px 0;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 SilhouetteMCP Dashboard</h1>
            <p>Sistema de Monitoreo Unificado - Ecosistema Empresarial IA</p>
        </div>
        
        <div class="score-display">
            <div class="score-number" id="system-score">--/--</div>
            <div class="score-label">Puntuación del Sistema</div>
        </div>
        
        <div class="access-info">
            <h3>🌐 Opciones de Acceso al Dashboard</h3>
            <p><strong>Local:</strong> http://localhost:{{ port }}</p>
            <p><strong>Ngrok:</strong> npx ngrok http {{ port }}</p>
            <p><strong>DNS:</strong> Configurar dominio personalizado para IP local</p>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="loadData()">🔄 Actualizar Datos</button>
            <a href="http://localhost:9000" class="btn btn-secondary" target="_blank">🔗 Dashboard Original</a>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Cargando estado de sistemas...</p>
        </div>
        
        <div class="stats-grid" id="stats-grid" style="display: none;">
            <!-- Las estadísticas se cargarán aquí -->
        </div>
        
        <div class="systems-grid" id="systems-grid" style="display: none;">
            <!-- Los sistemas se cargarán aquí -->
        </div>
        
        <div class="footer">
            <p>🌐 SilhouetteMCP Dashboard Web - Versión Unificada</p>
            <p>📊 Acceso directo a sistemas en puertos 8001-8026, 9000</p>
            <p>🕐 Última actualización: <span id="timestamp"></span></p>
        </div>
    </div>

    <script>
        let systemsData = null;
        
        async function loadData() {
            try {
                // Mostrar loading
                document.getElementById('loading').style.display = 'block';
                document.getElementById('stats-grid').style.display = 'none';
                document.getElementById('systems-grid').style.display = 'none';
                
                const response = await fetch('{{ api_url }}/api/systems');
                const data = await response.json();
                systemsData = data;
                
                // Simular puntuación del sistema basada en estado
                const runningCount = data.running_systems;
                const totalCount = data.total_systems;
                const score = Math.round((runningCount / totalCount) * 100);
                document.getElementById('system-score').textContent = `${score}/100`;
                
                updateStats(data);
                updateSystems(data.systems);
                document.getElementById('timestamp').textContent = new Date(data.timestamp).toLocaleString('es-ES');
                
                // Ocultar loading
                document.getElementById('loading').style.display = 'none';
                document.getElementById('stats-grid').style.display = 'grid';
                document.getElementById('systems-grid').style.display = 'grid';
                
            } catch (error) {
                console.error('Error cargando datos:', error);
                document.getElementById('loading').innerHTML = `
                    <div style="color: #dc3545;">
                        <h3>❌ Error al cargar datos</h3>
                        <p>No se pudo conectar al dashboard SilhouetteMCP</p>
                        <p>Verifica que el servicio esté corriendo en puerto 9000</p>
                    </div>
                `;
            }
        }
        
        function updateStats(data) {
            const statsGrid = document.getElementById('stats-grid');
            statsGrid.innerHTML = `
                <div class="stat-card">
                    <div class="stat-number total">${data.total_systems}</div>
                    <div class="stat-label">Total Sistemas</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number running">${data.running_systems}</div>
                    <div class="stat-label">Sistemas Activos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number stopped">${data.systems.filter(s => s.status === 'stopped').length}</div>
                    <div class="stat-label">Sistemas Detenidos</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number error">${data.systems.filter(s => s.status === 'error').length}</div>
                    <div class="stat-label">Con Errores</div>
                </div>
            `;
        }
        
        function updateSystems(systems) {
            const systemsGrid = document.getElementById('systems-grid');
            
            const statusIcons = {
                'running': '🟢',
                'stopped': '🔴', 
                'error': '⚠️'
            };
            
            const statusClasses = {
                'running': 'status-running',
                'stopped': 'status-stopped',
                'error': 'status-error'
            };
            
            // Ordenar sistemas por estado (running primero)
            systems.sort((a, b) => {
                const statusOrder = { 'running': 0, 'error': 1, 'stopped': 2 };
                return statusOrder[a.status] - statusOrder[b.status];
            });
            
            systemsGrid.innerHTML = systems.map(system => `
                <div class="system-card">
                    <div class="system-header">
                        <div class="system-name">${system.name}</div>
                        <div class="system-status ${statusClasses[system.status]}">
                            ${statusIcons[system.status]} ${system.status}
                        </div>
                    </div>
                    <div class="system-info">
                        <strong>Puerto:</strong> ${system.port} | 
                        <strong>URL:</strong> <a href="http://localhost:${system.port}" class="system-link" target="_blank">Acceder</a>
                    </div>
                    <div class="system-description">${system.description}</div>
                    <span class="category-badge">${system.category}</span>
                </div>
            `).join('');
        }
        
        // Cargar datos iniciales
        loadData();
        
        // Actualizar cada 30 segundos
        setInterval(loadData, 30000);
        
        // Auto-refresh cada 5 segundos si hay sistemas con error
        setInterval(() => {
            if (systemsData && systemsData.systems.some(s => s.status === 'error')) {
                loadData();
            }
        }, 5000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Dashboard principal"""
    return render_template_string(DASHBOARD_TEMPLATE, 
                                api_url=DASHBOARD_API_URL, 
                                port=PORT)

@app.route('/api/systems')
def get_systems():
    """Proxy para obtener datos del dashboard original"""
    try:
        response = requests.get(f"{DASHBOARD_API_URL}/api/systems", timeout=10)
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": f"No se pudo conectar al dashboard: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "total_systems": 0,
            "running_systems": 0,
            "systems": []
        }), 500

@app.route('/api/metrics')
def get_metrics():
    """Obtener métricas del sistema"""
    try:
        response = requests.get(f"{DASHBOARD_API_URL}/metrics", timeout=5)
        return response.text, response.status_code
    except:
        return jsonify({"error": "Métricas no disponibles"}), 500

@app.route('/api/status')
def get_status():
    """Estado del servidor"""
    return jsonify({
        "status": "active",
        "message": "Dashboard Web SilhouetteMCP funcionando correctamente",
        "timestamp": datetime.now().isoformat(),
        "backend_url": DASHBOARD_API_URL,
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        "status": "healthy", 
        "service": "SilhouetteMCP Dashboard Web Server",
        "port": PORT,
        "timestamp": datetime.now().isoformat()
    })

def background_updater():
    """Actualización en background cada 5 segundos"""
    while True:
        try:
            # Verificar conectividad con el dashboard original
            requests.get(f"{DASHBOARD_API_URL}/health", timeout=2)
        except:
            pass
        time.sleep(5)

if __name__ == '__main__':
    print("🚀 Iniciando Servidor Web Dashboard SilhouetteMCP")
    print("=" * 70)
    print(f"🌐 Dashboard disponible en: http://localhost:{PORT}")
    print(f"🔗 API backend en: {DASHBOARD_API_URL}")
    print("=" * 70)
    print("📊 Opciones de acceso:")
    print(f"   • Local: http://localhost:{PORT}")
    print(f"   • Ngrok: npx ngrok http {PORT}")
    print(f"   • DNS: Configurar dominio personalizado")
    print("=" * 70)
    print("🎯 Características:")
    print("   • Interfaz web moderna y responsive")
    print("   • Actualización automática cada 30 segundos")
    print("   • Acceso directo a todos los sistemas")
    print("   • Monitoreo en tiempo real del estado")
    print("=" * 70)
    
    # Iniciar hilo de actualización en background
    updater_thread = threading.Thread(target=background_updater, daemon=True)
    updater_thread.start()
    
    # Iniciar servidor Flask
    app.run(host='0.0.0.0', port=PORT, debug=False, threaded=True)