# Guía de Usuario - SilhouetteMCP v4.0.0

## 👋 Bienvenido a SilhouetteMCP

**SilhouetteMCP v4.0.0 FINAL UNIFIED** es un servidor unificado que proporciona **51 herramientas especializadas** distribuidas en **6 agentes inteligentes**, todo accesible a través de una API simple y un dashboard web moderno.

### 🎯 ¿Qué puedes hacer con SilhouetteMCP?

- **🗺️ Mapas y Geolocalización**: Geocodificación, búsqueda de lugares, cálculo de rutas
- **💰 Análisis Financiero**: Precios de acciones, criptomonedas, análisis de mercado
- **✈️ Viajes y Redes Sociales**: Planificación de viajes, análisis de redes sociales
- **📝 Creación de Contenido**: Generación de texto, imágenes, optimización SEO
- **🗄️ Gestión de Datos**: Operaciones completas con bases de datos
- **🔍 Investigación**: Búsquedas web avanzadas, investigación académica

## 🌐 Acceso al Sistema

### URLs Principales

| Servicio | URL | Descripción |
|----------|-----|-------------|
| **Dashboard** | http://tu-servidor:8001/files/dashboard | Interfaz web principal |
| **API** | http://tu-servidor:8001 | Documentación y endpoints |
| **Documentación** | http://tu-servidor:8001/docs | Swagger UI completa |
| **Health Check** | http://tu-servidor:8001/health | Estado del sistema |
| **Estadísticas** | http://tu-servidor:8001/stats | Métricas del sistema |

## 🖥️ Dashboard Web

### Acceso al Dashboard

1. Abre tu navegador web
2. Ve a: `http://tu-servidor:8001/files/dashboard`
3. Inicia sesión con tus credenciales

### Características del Dashboard

- **📊 Panel Principal**: Resumen de agentes y herramientas
- **🚀 Ejecutor Rápido**: Ejecuta herramientas directamente
- **📈 Monitoreo**: Estadísticas en tiempo real
- **📋 Historial**: Últimas ejecuciones
- **⚙️ Configuración**: Ajustes del sistema

### Navegación del Dashboard

#### Pestaña: Resumen
- Información general del sistema
- Estado de servicios
- Estadísticas rápidas

#### Pestaña: Agentes
- Lista de 6 agentes disponibles
- Herramientas por agente
- Estado de cada agente

#### Pestaña: Ejecutor
- Formulario para ejecutar herramientas
- Selección de agente y herramienta
- Parámetros configurables

#### Pestaña: Historial
- Últimas ejecuciones
- Resultados guardados
- Filtrado por fecha/agente

#### Pestaña: Monitoreo
- Métricas del sistema
- Gráficos de uso
- Alertas

## 🔑 Autenticación y Seguridad

### Métodos de Acceso

#### 1. Dashboard Web
- Usuario: `alberto.farahb@hotmail.com`
- Contraseña: `Fbalberto1910` (por defecto)

#### 2. API
```bash
# Via Bearer Token
curl -H "Authorization: Bearer tu_token" http://localhost:8001/agents

# Via API Key
curl -H "X-API-Key: tu_api_key" http://localhost:8001/agents

# Via consulta directa (para desarrollo)
curl http://localhost:8001/agents
```

### Cambiar Contraseña

1. Ve al dashboard
2. Pestaña **Configuración**
3. **Cambiar Contraseña**
4. Confirma tu contraseña actual
5. Ingresa la nueva contraseña
6. Guarda los cambios

## 🚀 Uso Básico

### Ejecutar una Herramienta Simple

#### Ejemplo 1: Geocodificación
```bash
curl -X POST "http://localhost:8001/execute/maps/geocode" \
  -H "Content-Type: application/json" \
  -d '{
    "address": "Madrid, España"
  }'
```

**Resultado:**
```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "result": {
        "latitude": 40.4168,
        "longitude": -3.7038,
        "formatted_address": "Madrid, España"
    },
    "processing_time": "0.85s"
}
```

#### Ejemplo 2: Precio de Acción
```bash
curl -X POST "http://localhost:8001/execute/financial/stock_price" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL"
  }'
```

#### Ejemplo 3: Búsqueda de Vuelos
```bash
curl -X POST "http://localhost:8001/execute/social_travel/flight_search" \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "MAD",
    "destination": "BCN",
    "departure_date": "2024-05-01",
    "passengers": 2
  }'
```

### Usando el Dashboard

#### Paso 1: Seleccionar Agente
1. Ve a la pestaña **Ejecutor**
2. Selecciona un agente del dropdown:
   - 🗺️ **Maps Intelligence** (6 herramientas)
   - 💰 **Financial Intelligence** (9 herramientas)
   - ✈️ **Social Media + Travel** (13 herramientas)
   - 📝 **Content Creation** (8 herramientas)
   - 🗄️ **Database Operations** (13 herramientas)
   - 🔍 **Research Intelligence** (2 herramientas)

#### Paso 2: Elegir Herramienta
1. Selecciona la herramienta que necesitas
2. Lee la descripción y parámetros requeridos

#### Paso 3: Configurar Parámetros
1. Completa los campos requeridos
2. Ajusta parámetros opcionales si es necesario

#### Paso 4: Ejecutar
1. Haz clic en **Ejecutar**
2. Espera el resultado
3. Revisa la respuesta

## 📋 Ejemplos por Agente

### 🗺️ Maps Intelligence Agent

#### Geocodificación
```json
{
    "address": "Barcelona, España",
    "language": "es"
}
```

#### Búsqueda de Lugares
```json
{
    "query": "restaurantes cerca de mí",
    "location": {
        "latitude": 40.4168,
        "longitude": -3.7038
    },
    "radius": 5000,
    "type": "restaurant"
}
```

#### Cálculo de Distancia
```json
{
    "origins": ["Madrid", "Barcelona"],
    "destinations": ["Valencia", "Sevilla"],
    "mode": "driving"
}
```

### 💰 Financial Intelligence Agent

#### Precio de Acción
```json
{
    "symbol": "TSLA",
    "source": "yahoo"
}
```

#### Precio de Criptomoneda
```json
{
    "symbol": "BTC",
    "currency": "EUR"
}
```

#### Tipo de Cambio
```json
{
    "from_currency": "USD",
    "to_currency": "EUR"
}
```

### ✈️ Social Media + Travel Agent

#### Búsqueda de Vuelos
```json
{
    "origin": "MAD",
    "destination": "BCN",
    "departure_date": "2024-06-01",
    "return_date": "2024-06-05",
    "passengers": 2,
    "class": "economy"
}
```

#### Búsqueda de Hoteles
```json
{
    "destination": "Madrid",
    "checkin": "2024-06-01",
    "checkout": "2024-06-03",
    "guests": 2,
    "stars": 4
}
```

#### Planificador de Viajes
```json
{
    "destination": "París",
    "duration": 5,
    "interests": ["cultura", "gastronomía", "arte"],
    "travel_style": "cultural",
    "budget_level": "medium"
}
```

#### Análisis de Redes Sociales
```json
{
    "platform": "twitter",
    "account": "@example",
    "metrics": ["followers", "engagement", "tweets"]
}
```

### 📝 Content Creation Agent

#### Generación de Texto
```json
{
    "prompt": "Escribe un artículo sobre inteligencia artificial",
    "max_tokens": 500,
    "style": "profesional",
    "language": "es"
}
```

#### Optimización SEO
```json
{
    "content": "Tu contenido aquí...",
    "target_keywords": ["inteligencia artificial", "IA", "machine learning"],
    "meta_description": "Descripción meta optimizada"
}
```

#### Traducción
```json
{
    "text": "Hello, how are you?",
    "target_language": "es"
}
```

### 🗄️ Database Operations Agent

#### Consulta a Base de Datos
```json
{
    "table": "users",
    "operation": "select",
    "conditions": {
        "active": true,
        "created_at": {
            "gte": "2024-01-01"
        }
    },
    "columns": ["id", "name", "email"]
}
```

#### Inserción de Datos
```json
{
    "table": "products",
    "data": {
        "name": "Producto Ejemplo",
        "price": 29.99,
        "category": "electronics",
        "active": true
    }
}
```

#### Subida de Archivo
```json
{
    "bucket": "uploads",
    "file_path": "documentos/documento.pdf",
    "content": "base64_encoded_content",
    "content_type": "application/pdf"
}
```

### 🔍 Research Intelligence Agent

#### Búsqueda Web
```json
{
    "query": "últimas tendencias en inteligencia artificial 2024",
    "num_results": 20,
    "search_type": "general",
    "language": "es"
}
```

#### Investigación Académica
```json
{
    "topic": "machine learning",
    "fields": ["computer science", "artificial intelligence"],
    "date_range": {
        "start": "2020",
        "end": "2024"
    },
    "max_results": 50
}
```

## 🔄 Uso Avanzado

### Tareas Asíncronas

Para operaciones que toman tiempo, usa el sistema de tareas asíncronas:

#### Crear Tarea
```bash
curl -X POST "http://localhost:8001/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "financial",
    "tool_name": "market_news",
    "parameters": {
      "limit": 50
    },
    "priority": 5
  }'
```

#### Verificar Estado
```bash
curl http://localhost:8001/tasks/550e8400-e29b-41d4-a716-446655440000
```

### Manejo de Archivos

#### Subir Archivo
```bash
curl -X POST "http://localhost:8001/upload" \
  -F "file=@documento.pdf" \
  -F "folder=documentos"
```

#### Listar Archivos
```bash
curl "http://localhost:8001/files/list?folder=documentos"
```

### Integración con Aplicaciones

#### Ejemplo en JavaScript
```javascript
async function geocodeAddress(address) {
    const response = await fetch('http://tu-servidor:8001/execute/maps/geocode', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ address })
    });
    
    const result = await response.json();
    return result;
}

// Uso
geocodeAddress('Madrid, España')
    .then(result => console.log(result.result));
```

#### Ejemplo en Python
```python
import requests

def get_stock_price(symbol):
    response = requests.post(
        'http://tu-servidor:8001/execute/financial/stock_price',
        json={'symbol': symbol}
    )
    return response.json()

# Uso
price = get_stock_price('AAPL')
print(f"Precio de AAPL: {price['result']['price']}")
```

#### Ejemplo en cURL
```bash
# Script para búsqueda de vuelos
#!/bin/bash

ORIGIN="MAD"
DESTINATION="BCN"
DATE="2024-06-01"

curl -X POST "http://localhost:8001/execute/social_travel/flight_search" \
  -H "Content-Type: application/json" \
  -d "{
    \"origin\": \"$ORIGIN\",
    \"destination\": \"$DESTINATION\",
    \"departure_date\": \"$DATE\",
    \"passengers\": 2
  }"
```

## 📊 Monitoreo y Estadísticas

### Endpoint de Estadísticas
```bash
curl http://localhost:8001/stats
```

**Respuesta:**
```json
{
    "system_stats": {
        "total_requests": 15847,
        "successful_requests": 15421,
        "failed_requests": 426
    },
    "agents_info": {
        "maps": {
            "tools_count": 6
        },
        "financial": {
            "tools_count": 9
        }
    },
    "tasks_summary": {
        "total": 1247,
        "completed": 1239,
        "failed": 0
    }
}
```

### Dashboard de Monitoreo

1. Ve a **Monitoreo** en el dashboard
2. Revisa gráficos en tiempo real:
   - Requests por minuto
   - Tiempo de respuesta promedio
   - Uso por agente
   - Errores por hora

## ⚙️ Configuración

### Variables de Entorno

Edita `/opt/silhouettemcp_v4_unified/.env`:

```bash
# Puerto del servidor
PORT=8001

# Configuración de Supabase (requerido)
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key
SUPABASE_ANON_KEY=tu_anon_key

# API Keys (opcional)
GOOGLE_MAPS_API_KEY=tu_google_maps_key
OPENAI_API_KEY=tu_openai_key

# Configuración de seguridad
ADMIN_EMAIL=alberto.farahb@hotmail.com
ADMIN_PASSWORD_HASH=sha256_hash_de_tu_contraseña
```

### Configuración del Sistema

#### Reiniciar Servicios
```bash
sudo systemctl restart silhouettemcp
sudo systemctl restart nginx
```

#### Ver Logs
```bash
# Logs del servicio
sudo journalctl -u silhouettemcp -f

# Logs de la aplicación
sudo tail -f /var/log/silhouettemcp/app.log

# Logs de nginx
sudo tail -f /var/log/nginx/error.log
```

## 🔧 Solución de Problemas

### Problemas Comunes

#### 1. "Connection refused"
**Problema**: No se puede conectar al servidor
**Solución**:
```bash
# Verificar estado del servicio
sudo systemctl status silhouettemcp

# Verificar puerto
netstat -tuln | grep 8001

# Reiniciar servicio
sudo systemctl restart silhouettemcp
```

#### 2. "Agent not found"
**Problema**: Agente no existe
**Solución**: Verifica el nombre del agente:
```bash
curl http://localhost:8001/agents
```

#### 3. "Tool not found"
**Problema**: Herramienta no existe
**Solución**: Lista las herramientas disponibles:
```bash
curl http://localhost:8001/tools
```

#### 4. "Authentication failed"
**Problema**: No se puede autenticar
**Solución**: 
1. Verifica credenciales en el dashboard
2. Usa Bearer token en lugar de API key
3. Contacta al administrador

#### 5. "Rate limit exceeded"
**Problema**: Demasiadas requests
**Solución**:
- Espera antes de hacer más requests
- Implementa delays en tu aplicación
- Contacta para aumentar límites

### Logs de Error

#### Ubicación de Logs
- **Servicio**: `journalctl -u silhouettemcp`
- **Aplicación**: `/var/log/silhouettemcp/app.log`
- **Nginx**: `/var/log/nginx/error.log`

#### Comandos de Diagnóstico
```bash
# Ver logs recientes
sudo journalctl -u silhouettemcp -n 50

# Buscar errores específicos
sudo journalctl -u silhouettemcp --since "1 hour ago" | grep ERROR

# Verificar configuración
sudo systemctl status silhouettemcp

# Verificar conectividad
curl -I http://localhost:8001/health
```

## 📚 Recursos Adicionales

### Documentación Completa
- **API Docs**: http://tu-servidor:8001/docs
- **Guías**: `/opt/silhouettemcp_v4_unified/docs/`
- **Ejemplos**: `/opt/silhouettemcp_v4_unified/examples/`

### Comandos Útiles

#### Gestión del Servicio
```bash
# Ver estado
sudo systemctl status silhouettemcp

# Iniciar/Detener/Reiniciar
sudo systemctl start silhouettemcp
sudo systemctl stop silhouettemcp
sudo systemctl restart silhouettemcp

# Ver logs en tiempo real
sudo journalctl -u silhouettemcp -f
```

#### Backup y Restauración
```bash
# Crear backup
sudo /opt/silhouettemcp_v4_unified/scripts/backup.sh

# Ver backups disponibles
ls -la /var/backups/silhouettemcp/
```

#### Verificación de Salud
```bash
# Health check básico
curl http://localhost:8001/health

# Estadísticas completas
curl http://localhost:8001/stats

# Ver agentes disponibles
curl http://localhost:8001/agents
```

## 🆘 Soporte

### Contacto
- **Email**: alberto.farahb@hotmail.com
- **Dashboard**: http://tu-servidor:8001/files/dashboard

### Antes de Contactar Soporte
1. Verifica el estado del servicio: `curl http://localhost:8001/health`
2. Revisa logs recientes: `sudo journalctl -u silhouettemcp -n 50`
3. Intenta reiniciar el servicio: `sudo systemctl restart silhouettemcp`
4. Verifica configuración: `sudo systemctl status silhouettemcp`

### Información a Proporcionar
- Descripción del problema
- Pasos para reproducir
- Logs de error relevantes
- Configuración del sistema
- Versión del software

## 🎯 Mejores Prácticas

### Uso Eficiente
1. **Reutiliza conexiones**: Mantén conexiones HTTP activas
2. **Batch requests**: Agrupa operaciones cuando sea posible
3. **Cache results**: Guarda resultados frecuentes localmente
4. **Monitor usage**: Revisa estadísticas regularmente

### Seguridad
1. **Cambia credenciales por defecto**
2. **Usa HTTPS en producción**
3. **Limita acceso por IP cuando sea posible**
4. **Revisa logs de seguridad regularmente**

### Desarrollo
1. **Usa el modo de desarrollo** para testing
2. **Implementa retry logic** para operaciones críticas
3. **Valida parámetros** antes de enviar
4. **Maneja errores** apropiadamente

---

## 🎉 ¡Bienvenido a SilhouetteMCP v4.0.0!

Ahora tienes acceso a **51 herramientas especializadas** en un servidor unificado. Explora, experimenta y descubre todo lo que puedes hacer con los 6 agentes inteligentes.

**¡Disfruta creando aplicaciones increíbles!**

---

*Para soporte técnico o consultas avanzadas, no dudes en contactarnos.*
