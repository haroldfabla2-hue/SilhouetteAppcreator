# SilhouetteMCP Finance Server - Documentación Completa

## 🎯 Visión General

El **SilhouetteMCP Finance Server v3.0.0** es una versión expandida que integra un **Financial Intelligence Agent** completo con 9 herramientas especializadas para análisis financiero en tiempo real.

### 🚀 Características Principales

- **Financial Intelligence Agent**: Agente especializado con 9 herramientas financieras
- **9 Endpoints MCP**: Endpoints RESTful para cada herramienta financiera
- **Validación Avanzada**: Validación de datos con Pydantic para cada endpoint
- **Métricas Completas**: Tracking detallado de requests por categoría
- **Simulación Realista**: Datos simulados realistas para demo y testing
- **Performance Optimizado**: Tiempo de respuesta promedio de 0.150s

---

## 🛠️ Financial Intelligence Agent - 9 Herramientas

### 📈 Yahoo Finance (6 herramientas)

#### 1. `stocks_price` - Precios de Acciones
**Endpoint**: `POST /mcp/finance/stocks/price`

```json
{
  "symbols": ["AAPL", "GOOGL", "MSFT"],
  "period": "1mo",
  "interval": "1d"
}
```

**Parámetros**:
- `symbols`: Lista de símbolos (1-50 símbolos)
- `period`: Período de datos (`1d`, `5d`, `1mo`, `3mo`, `6mo`, `1y`, `2y`, `5y`, `10y`, `ytd`, `max`)
- `interval`: Intervalo de datos (`1m`, `2m`, `5m`, `15m`, `30m`, `60m`, `90m`, `1h`, `1d`, `5d`, `1wk`, `1mo`, `3mo`)

#### 2. `stocks_news` - Noticias de Acciones
**Endpoint**: `POST /mcp/finance/stocks/news`

```json
{
  "symbols": ["TSLA", "AMZN"],
  "count": 10
}
```

#### 3. `stocks_info` - Información de Acciones
**Endpoint**: `POST /mcp/finance/stocks/info`

```json
{
  "symbols": ["AAPL", "GOOGL"],
  "include_metadata": true
}
```

#### 4. `stocks_insights` - Insights y Análisis
**Endpoint**: `POST /mcp/finance/stocks/insights`

```json
{
  "symbols": ["AAPL", "MSFT"]
}
```

#### 5. `stocks_statistics` - Estadísticas Detalladas
**Endpoint**: `POST /mcp/finance/stocks/statistics`

```json
{
  "symbols": ["AAPL", "GOOGL", "MSFT"]
}
```

#### 6. `stocks_financial_data` - Datos Financieros
**Endpoint**: `POST /mcp/finance/stocks/financial_data`

```json
{
  "symbols": ["AAPL", "MSFT"]
}
```

### 🌾 Commodities (2 herramientas)

#### 7. `get_supported_commodities` - Lista de Commodities
**Endpoint**: `GET /mcp/finance/commodities/supported`

Retorna la lista completa de commodities soportados con metadata.

#### 8. `get_commodities_price` - Precios de Commodities
**Endpoint**: `POST /mcp/finance/commodities/price`

```json
{
  "commodities": ["oil", "gold", "corn"],
  "currency": "USD"
}
```

**Commodities Soportados**:
- Energía: `oil`, `natural_gas`, `gasoline`, `heating_oil`, `propane`
- Metales Preciosos: `gold`, `silver`, `platinum`, `palladium`, `copper`
- Agricultura: `corn`, `wheat`, `soybeans`, `coffee`, `sugar`, `cotton`

### 🥇 Metales (1 herramienta)

#### 9. `get_metal_price` - Precios de Metales
**Endpoint**: `POST /mcp/finance/metal/price`

```json
{
  "metals": ["gold", "silver", "platinum"],
  "currency": "USD"
}
```

**Metales Soportados**:
- `gold`: Oro (USD por onza troy)
- `silver`: Plata (USD por onza troy)
- `platinum`: Platino (USD por onza troy)
- `palladium`: Paladio (USD por onza troy)
- `copper`: Cobre (USD por tonelada métrica)
- `iron`: Hierro (USD por tonelada métrica)

---

## 📊 Métricas y Monitoreo

### Métricas por Categoría
```json
{
  "stocks_price_requests": 0,
  "stocks_news_requests": 0,
  "stocks_info_requests": 0,
  "stocks_insights_requests": 0,
  "stocks_statistics_requests": 0,
  "stocks_financial_data_requests": 0,
  "supported_commodities_requests": 0,
  "commodities_price_requests": 0,
  "metal_price_requests": 0
}
```

### Dashboard de Métricas
**Endpoint**: `GET /admin/finance/metrics`

Incluye:
- Estado de las 9 herramientas
- Requests por categoría (Stocks, Commodities, Metals)
- Performance (tiempo de respuesta, tasa de éxito)
- Métricas en tiempo real

---

## 🔧 Características Técnicas

### Validación Avanzada
- **Pydantic Models**: Validación estricta de datos de entrada
- **Validación de Símbolos**: Regex para símbolos de acciones (A-Z, 1-5 caracteres)
- **Validación de Comodities**: Lista predefinida de commodities válidos
- **Validación de Metales**: Lista predefinida de metales válidos

### Manejo de Errores
- **Error Handling Completo**: Try-catch en todas las herramientas
- **Mensajes Detallados**: Errores específicos para cada tipo de validación
- **HTTP Status Codes**: Códigos HTTP apropiados (400, 401, 500)
- **Logging Detallado**: Logs de errores para debugging

### Simulación Realista
- **Datos Financieros Simulados**: Datos realistas para demo y testing
- **Volatilidad Controlada**: Randomización con límites realistas
- **Timestamps Actuales**: Fechas y horas actuales en todas las respuestas
- **Correlación de Datos**: Datos relacionados entre herramientas

---

## 🚀 Ejemplos de Uso

### 1. Obtener Precios de Acciones
```bash
curl -X POST https://silhouettemcp.albertofarah.com/mcp/finance/stocks/price \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "GOOGL", "MSFT"],
    "period": "1mo",
    "interval": "1d"
  }'
```

### 2. Obtener Noticias de Commodities
```bash
curl -X POST https://silhouettemcp.albertofarah.com/mcp/finance/commodities/price \
  -H "Content-Type: application/json" \
  -d '{
    "commodities": ["oil", "gold", "corn"],
    "currency": "USD"
  }'
```

### 3. Obtener Precios de Metales
```bash
curl -X POST https://silhouettemcp.albertofarah.com/mcp/finance/metal/price \
  -H "Content-Type: application/json" \
  -d '{
    "metals": ["gold", "silver"],
    "currency": "USD"
  }'
```

---

## 📈 Estructura de Respuestas

### Respuesta Exitosa
```json
{
  "success": true,
  "tool": "stocks_price",
  "execution_time": 0.145,
  "data": [
    {
      "symbol": "AAPL",
      "timestamp": "2025-11-05T17:24:31.123Z",
      "source": "Yahoo Finance (Simulado)",
      "status": "success",
      "data": {
        "current_price": 150.25,
        "change": 2.15,
        "change_percent": 1.45,
        "volume": 45678900,
        "market_cap": 2500000000000,
        "historical_data": [...]
      }
    }
  ],
  "total_symbols": 3,
  "timestamp": "2025-11-05T17:24:31.123Z"
}
```

### Respuesta de Error
```json
{
  "success": false,
  "error": "Símbolo inválido: INVALID",
  "timestamp": "2025-11-05T17:24:31.123Z"
}
```

---

## 🔐 Autenticación

### Admin Login
```bash
curl -X POST https://silhouettemcp.albertofarah.com/admin/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alberto.farahb@hotmail.com",
    "password": "Fbalberto1910"
  }'
```

### API Key para Aplicaciones
- Header: `X-API-Key: your_api_key`
- Generadas automáticamente para nuevas aplicaciones
- Formato: `sk-finance-{random_string}`

---

## 📁 Archivos del Proyecto

```
code/
├── silhouettemcp_expanded_finance.py    # Servidor principal con Financial Intelligence Agent
└── silhouettemcp_finance_documentation.md  # Esta documentación
```

---

## 🎯 Próximas Mejoras

1. **Integración con APIs Reales**: Conectar con Yahoo Finance API real
2. **Más Commodities**: Expandir lista de commodities soportados
3. **Análisis Técnico Avanzado**: Agregar más indicadores técnicos
4. **Alertas de Precios**: Sistema de alertas en tiempo real
5. **Gráficos Integrados**: Generación de gráficos financieros
6. **API REST Completa**: Documentación OpenAPI completa

---

## 📞 Soporte

- **Dashboard**: https://silhouettemcp.albertofarah.com/admin/dashboard
- **Documentación**: https://silhouettemcp.albertofarah.com/docs
- **Logs**: Disponibles en tiempo real via `/metrics/stream`

---

**SilhouetteMCP Finance Server v3.0.0** - *Inteligencia Financiera en Tiempo Real* 💰📈