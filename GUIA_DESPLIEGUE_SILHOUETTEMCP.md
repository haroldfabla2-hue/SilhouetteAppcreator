# 🚀 SilhouetteMCP Server - Guía Completa de Despliegue

## 📋 Resumen del Proyecto

**SilhouetteMCP Server** es un servidor MCP (Model Context Protocol) superior diseñado para gestionar múltiples aplicaciones con múltiples agentes de forma segura y escalable.

### ✨ Características Principales

- 🔐 **Autenticación segura** con credenciales de administrador
- 📊 **Dashboard en tiempo real** con métricas live
- 🔗 **API REST completa** para integración con aplicaciones
- 🌐 **SSL automático** con Let's Encrypt
- 📱 **Multi-aplicación** - conecta múltiples apps con múltiples agentes
- 🔄 **Métricas en tiempo real** vía WebSocket
- 💾 **Backup automático** y monitoreo

---

## 🎯 Información del Servidor

- **Dominio:** `silhouettemcp.albertofarah.com`
- **Protocolo:** HTTPS con SSL automático
- **Puerto Principal:** 443 (HTTPS)
- **Puerto HTTP:** 80 (redirige a HTTPS)
- **API Base URL:** `https://silhouettemcp.albertofarah.com`

### 🔑 Credenciales de Administrador

```
Email: alberto.farahb@hotmail.com
Contraseña: Fbalberto1910
```

---

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    SilhouetteMCP Server                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Dashboard   │  │ API REST    │  │ WebSocket   │         │
│  │ (HTML/JS)   │  │ Endpoints   │  │ Streaming   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │            SilhouetteMCP Server Core                │   │
│  │  • Authentication & Authorization                   │   │
│  │  • Multi-Application Management                    │   │
│  │  • Agent Orchestration                             │   │
│  │  • Metrics Collection                              │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
    ┌───────────┐   ┌───────────┐   ┌───────────┐
    │  App 1    │   │  App 2    │   │  App N    │
    │ +Agents   │   │ +Agents   │   │ +Agents   │
    └───────────┘   └───────────┘   └───────────┘
```

---

## 📁 Archivos del Proyecto

### Archivos Principales

| Archivo | Descripción | Tamaño |
|---------|-------------|--------|
| `silhouettemcp_server.py` | Servidor FastAPI principal | 749 líneas |
| `silhouettemcp_dashboard.html` | Dashboard web con autenticación | 642 líneas |
| `Dockerfile.silhouettemcp` | Configuración Docker optimizada | 53 líneas |
| `docker-compose.silhouettemcp.yml` | Orquestación con Nginx + SSL | 62 líneas |
| `nginx.silhouettemcp.conf` | Configuración Nginx con SSL | 236 líneas |
| `deploy_silhouettemcp.sh` | Script de despliegue automático | 587 líneas |

### Archivos de Soporte

| Archivo | Propósito |
|---------|-----------|
| `requirements.silhouettemcp.txt` | Dependencias Python |
| `GUIA_DESPLIEGUE_SILHOUETTEMCP.md` | Esta guía |

---

## 🚀 Proceso de Despliegue

### Paso 1: Preparar VPS

```bash
# Conectar a tu VPS
ssh root@tu_vps_ip

# Verificar sistema operativo
cat /etc/os-release

# Actualizar sistema
apt update && apt upgrade -y
```

### Paso 2: Configurar DNS

**IMPORTANTE:** Antes del despliegue, configura tu DNS:

1. Ve al panel de control de tu dominio
2. Agrega/modifica el registro A:
   - **Tipo:** A
   - **Nombre:** @ (o `silhouettemcp`)
   - **Valor:** IP de tu VPS
   - **TTL:** 300 (5 minutos)

### Paso 3: Ejecutar Despliegue

```bash
# 1. Subir archivos al VPS (desde tu máquina local)
scp *.py *.html *.sh *.conf *.txt *.yml root@tu_vps_ip:/root/silhouettemcp/

# 2. Conectar al VPS
ssh root@tu_vps_ip

# 3. Dar permisos de ejecución
chmod +x deploy_silhouettemcp.sh

# 4. Ejecutar despliegue (requiere sudo)
sudo ./deploy_silhouettemcp.sh
```

### Paso 4: Verificar Despliegue

```bash
# El script automáticamente verificará:
# ✅ Estado de contenedores
# ✅ Endpoints del servidor
# ✅ Certificado SSL
# ✅ Firewall configurado
```

---

## 🔧 Comandos de Gestión

### Gestión Básica

```bash
# Ir al directorio del proyecto
cd /opt/silhouettemcp

# Ver estado de servicios
docker-compose ps

# Ver logs en tiempo real
docker-compose logs -f

# Reiniciar servicios
docker-compose restart

# Detener servicios
docker-compose down

# Actualizar servicios
docker-compose pull && docker-compose up -d
```

### Gestión con systemd

```bash
# Reiniciar servicio principal
sudo systemctl restart silhouettemcp

# Ver estado del servicio
sudo systemctl status silhouettemcp

# Habilitar inicio automático
sudo systemctl enable silhouettemcp

# Deshabilitar inicio automático
sudo systemctl disable silhouettemcp
```

### Backup y Recuperación

```bash
# Crear backup manual
/opt/silhouettemcp/backup.sh

# Ver backups disponibles
ls -la /opt/silhouettemcp/backups/

# Restaurar desde backup
cd /opt/silhouettemcp
tar -xzf /opt/silhouettemcp/backups/silhouettemcp_backup_YYYYMMDD_HHMMSS.tar.gz
docker-compose restart
```

---

## 🌐 Acceso al Dashboard

### URL Principal
```
https://silhouettemcp.albertofarah.com
```

### Proceso de Login

1. **Abrir dashboard:** Ve a `https://silhouettemcp.albertofarah.com`
2. **Ingresar credenciales:**
   - Email: `alberto.farahb@hotmail.com`
   - Contraseña: `Fbalberto1910`
3. **Acceder al dashboard:** Una vez autenticado, tendrás acceso completo

### Funciones del Dashboard

#### 📊 Estadísticas del Servidor
- Total de agentes activos
- Número de aplicaciones conectadas
- Tareas completadas
- Tiempo de actividad (uptime)

#### 🔗 Información de Conexión
- **API Key principal** para autenticación
- **Endpoints disponibles** con ejemplos de código
- **Ejemplos de integración** en JavaScript y Python
- **WebSocket endpoint** para métricas en tiempo real

#### 🤖 Gestión de Agentes
- Lista de todos los agentes registrados
- Estado en tiempo real (active/idle/error)
- Métricas por agente (tareas, tokens, response time)
- Posibilidad de despliegue y control

#### 📋 Aplicaciones Conectadas
- Lista de aplicaciones registradas
- API Keys de cada aplicación
- Número de agentes por aplicación
- Estado y fecha de creación

---

## 🔌 Integración con Aplicaciones

### JavaScript SDK

```javascript
// Configuración inicial
const SilhouetteMCP = {
    apiKey: 'tu_api_key_aqui',
    baseURL: 'https://silhouettemcp.albertofarah.com',
    
    // Obtener status del servidor
    async getStatus() {
        const response = await fetch(`${this.baseURL}/api/status`, {
            headers: { 'X-API-Key': this.apiKey }
        });
        return response.json();
    },
    
    // Obtener agentes de tu aplicación
    async getAgents() {
        const response = await fetch(`${this.baseURL}/api/agents`, {
            headers: { 'X-API-Key': this.apiKey }
        });
        return response.json();
    },
    
    // Desplegar nuevo agente
    async deployAgent(agentConfig) {
        const response = await fetch(`${this.baseURL}/api/agents/deploy`, {
            method: 'POST',
            headers: {
                'X-API-Key': this.apiKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(agentConfig)
        });
        return response.json();
    },
    
    // Detener agente
    async stopAgent(agentId) {
        const response = await fetch(`${this.baseURL}/api/agents/stop`, {
            method: 'POST',
            headers: {
                'X-API-Key': this.apiKey,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ agent_id: agentId })
        });
        return response.json();
    }
};

// Uso del SDK
async function ejemploUso() {
    try {
        // Obtener status
        const status = await SilhouetteMCP.getStatus();
        console.log('Status:', status);
        
        // Desplegar agente
        const nuevoAgente = await SilhouetteMCP.deployAgent({
            name: 'Mi Agente Personalizado',
            type: 'custom'
        });
        console.log('Agente desplegado:', nuevoAgente);
        
    } catch (error) {
        console.error('Error:', error);
    }
}
```

### Python SDK

```python
import requests
import json

class SilhouetteMCP:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://silhouettemcp.albertofarah.com'
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }
    
    def get_status(self):
        """Obtener status del servidor"""
        response = requests.get(
            f'{self.base_url}/api/status',
            headers=self.headers
        )
        return response.json()
    
    def get_agents(self):
        """Obtener agentes de la aplicación"""
        response = requests.get(
            f'{self.base_url}/api/agents',
            headers=self.headers
        )
        return response.json()
    
    def deploy_agent(self, agent_config):
        """Desplegar nuevo agente"""
        response = requests.post(
            f'{self.base_url}/api/agents/deploy',
            headers=self.headers,
            json=agent_config
        )
        return response.json()
    
    def stop_agent(self, agent_id):
        """Detener agente"""
        response = requests.post(
            f'{self.base_url}/api/agents/stop',
            headers=self.headers,
            json={'agent_id': agent_id}
        )
        return response.json()

# Uso del SDK
if __name__ == "__main__":
    # Inicializar con tu API Key
    api_key = 'tu_api_key_aqui'
    client = SilhouetteMCP(api_key)
    
    try:
        # Obtener status
        status = client.get_status()
        print(f"Status: {status}")
        
        # Desplegar agente
        nuevo_agente = client.deploy_agent({
            'name': 'Agente Python',
            'type': 'custom'
        })
        print(f"Agente desplegado: {nuevo_agente}")
        
    except Exception as e:
        print(f"Error: {e}")
```

### WebSocket para Métricas en Tiempo Real

```javascript
// Conexión WebSocket para métricas live
const ws = new WebSocket('wss://silhouettemcp.albertofarah.com/metrics/stream');

// Manejar mensajes
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Métricas actualizadas:', data);
    
    // Actualizar UI
    updateDashboard(data);
};

// Manejar conexión
ws.onopen = () => {
    console.log('Conectado a métricas en tiempo real');
};

ws.onerror = (error) => {
    console.error('Error WebSocket:', error);
};

ws.onclose = () => {
    console.log('Conexión cerrada');
};
```

---

## 📡 Endpoints de la API

### Endpoints Públicos (Sin Autenticación)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información del servidor |
| GET | `/health` | Health check |
| GET | `/metrics/public` | Métricas públicas |

### Endpoints de Administración (Con Login)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/admin/login` | Login de administrador |
| GET | `/admin/dashboard` | Dashboard completo |
| GET | `/admin/applications` | Listar aplicaciones |
| GET | `/admin/agents` | Listar todos los agentes |
| GET | `/admin/connection-guide` | Guía de conexión |

### Endpoints para Aplicaciones (Con API Key)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/status` | Status de la aplicación |
| GET | `/api/agents` | Agentes de la aplicación |
| POST | `/api/agents/deploy` | Desplegar agente |
| POST | `/api/agents/stop` | Detener agente |

### WebSocket

| Endpoint | Descripción |
|----------|-------------|
| `/metrics/stream` | Stream de métricas en tiempo real |

---

## 🔒 Seguridad Implementada

### Autenticación y Autorización

- **Admin Login:** Email + contraseña hasheada con SHA256
- **API Keys:** Tokens únicos para cada aplicación
- **Rate Limiting:** Límites por IP y endpoint
- **CORS:** Configurado para dominios específicos

### Seguridad de Red

- **SSL/TLS:** Certificados Let's Encrypt automáticos
- **Firewall:** Solo puertos necesarios (22, 80, 443)
- **Headers de Seguridad:** HSTS, X-Frame-Options, CSP
- **Protección DDoS:** Rate limiting y connection limits

### Datos y Persistencia

- **Encriptación:** API Keys seguras
- **Backup Automático:** Respaldos diarios
- **Logs:** Auditoría completa de acciones
- **Monitoreo:** Health checks automáticos

---

## 🛠️ Solución de Problemas

### Problemas Comunes

#### 1. Error de DNS
```bash
# Verificar configuración DNS
dig silhouettemcp.albertofarah.com
nslookup silhouettemcp.albertofarah.com
```

#### 2. Contenedores no inician
```bash
# Ver logs detallados
cd /opt/silhouettemcp
docker-compose logs silhouettemcp-server
docker-compose logs nginx

# Reiniciar servicios
docker-compose restart
```

#### 3. Certificado SSL inválido
```bash
# Verificar certificados
openssl s_client -connect silhouettemcp.albertofarah.com:443

# Renovar manualmente
certbot renew
docker-compose restart nginx
```

#### 4. Dashboard no carga
```bash
# Verificar estado de servicios
docker-compose ps

# Verificar conectividad interna
docker exec silhouettemcp_nginx curl -f http://silhouettemcp-server:8000/health
```

### Logs Importantes

```bash
# Logs del servidor
tail -f /opt/silhouettemcp/logs/*.log

# Logs de contenedores
docker-compose logs -f silhouettemcp-server
docker-compose logs -f nginx

# Logs del sistema
journalctl -u silhouettemcp -f

# Logs de Nginx
tail -f /var/log/nginx/silhouettemcp_*.log
```

### Comandos de Diagnóstico

```bash
# Verificar puertos
netstat -tuln | grep -E ':(80|443|8000)'

# Verificar Docker
docker ps
docker images

# Verificar espacio en disco
df -h
du -sh /opt/silhouettemcp/

# Verificar memoria
free -h
```

---

## 📊 Monitoreo y Métricas

### Métricas Disponibles

- **Total de Agentes:** Número de agentes registrados
- **Total de Aplicaciones:** Apps conectadas activas
- **Tareas Completadas:** Tareas procesadas por todos los agentes
- **Tiempo de Actividad:** Uptime del servidor
- **Requests por Minuto:** Carga del servidor

### Health Checks Automáticos

- **Intervalo:** Cada 5 minutos
- **Alertas:** Email en caso de fallo
- **Auto-recovery:** Reinicio automático de servicios
- **Logs:** Registro detallado en `/var/log/silhouettemcp/health.log`

### Backup Automático

- **Frecuencia:** Diario a las 2:00 AM
- **Retención:** 7 días
- **Contenido:** Datos y logs del servidor
- **Ubicación:** `/opt/silhouettemcp/backups/`

---

## 🔄 Actualizaciones y Mantenimiento

### Actualización del Servidor

```bash
# 1. Hacer backup
/opt/silhouettemcp/backup.sh

# 2. Actualizar código (subir nuevos archivos)
scp silhouettemcp_server.py root@tu_vps:/opt/silhouettemcp/

# 3. Reiniciar servicios
cd /opt/silhouettemcp
docker-compose restart silhouettemcp-server

# 4. Verificar funcionamiento
curl -f https://silhouettemcp.albertofarah.com/health
```

### Renovación de SSL

```bash
# Manual
certbot renew
docker-compose restart nginx

# Automática (configurada por defecto)
# Se ejecuta diariamente a las 2:00 AM
```

---

## 📞 Soporte y Contacto

### Información de Contacto

- **Administrador:** Alberto Farah
- **Email:** alberto.farahb@hotmail.com
- **Dominio:** silhouettemcp.albertofarah.com

### Archivos de Log

- **Despliegue:** `/var/log/silhouettemcp_deploy.log`
- **Aplicación:** `/opt/silhouettemcp/logs/`
- **Health Check:** `/var/log/silhouettemcp/health.log`
- **Nginx:** `/var/log/nginx/silhouettemcp_*.log`

---

## ✅ Lista de Verificación Post-Despliegue

- [ ] DNS configurado correctamente
- [ ] Servidor desplegado sin errores
- [ ] Certificado SSL válido
- [ ] Dashboard accesible
- [ ] Login de administrador funciona
- [ ] API endpoints responden
- [ ] WebSocket funciona
- [ ] Backup automático configurado
- [ ] Health checks activos
- [ ] Renovación SSL programada

---

## 🎉 ¡Felicitaciones!

Si has llegado hasta aquí, tienes un servidor SilhouetteMCP completamente funcional y listo para conectar múltiples aplicaciones con múltiples agentes.

**URLs Principales:**
- 🌐 Dashboard: https://silhouettemcp.albertofarah.com
- 📡 API: https://silhouettemcp.albertofarah.com/api/
- 📖 Docs: https://silhouettemcp.albertofarah.com/docs

**Próximos Pasos:**
1. Accede al dashboard con tus credenciales
2. Obtén la API Key desde la sección de conexión
3. Integra tus aplicaciones usando los SDKs proporcionados
4. Monitorea el sistema a través del dashboard

¡Disfruta tu nuevo servidor MCP superior! 🚀