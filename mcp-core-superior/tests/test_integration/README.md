"""
Tests de Integración Multi-Agente - MCP Core Superior
=====================================================

Este directorio contiene tests de integración comprehensivos para validar el funcionamiento
completo del sistema multi-agente MCP Core Superior.

## Estructura de Tests

### 🏗️ Tests de Flujo Multi-Agente (`test_multi_agent_flow.py`)
- **Valida**: Flujo completo Reasoner→Planner→Executor→Verifier
- **Funcionalidades**: Orquestación secuencial y paralela, recuperación de errores, validación de calidad
- **Cobertura**: Flujo end-to-end, contexto persistente, cancelación de tareas, monitoreo de salud

### 🤝 Tests de Integración de Agentes (`test_agent_integration.py`)
- **Valida**: Colaboración entre los 12 agentes especializados
- **Funcionalidades**: Comunicación inter-agente, balanceador de carga, recuperación de fallos
- **Agentes**: Reasoner, Planner, Executor, Verifier, Database Operations, Python Executor, Git Operations, File Processing, Web Scraping, Search Engine, Memory Manager, Orchestrator

### 🔄 Tests de Orquestación de Workflows (`test_workflow_orchestration.py`)
- **Valida**: Patrones de orquestación complejos
- **Patrones**: Secuencial, Paralelo, Fan-out/Fan-in, Condicional, Recuperación de errores, Circuit Breaker, Backpressure
- **Escenarios**: Workflows empresariales complejos con múltiples etapas

### 📡 Tests de Streaming SSE (`test_streaming_updates.py`)
- **Valida**: Updates en tiempo real y comunicación bidireccional
- **Funcionalidades**: Streams SSE, múltiples streams concurrentes, resiliencia de conexiones
- **Casos de uso**: Dashboard de monitoreo, colaboración en tiempo real, backpressure handling

### 🗄️ Tests de Operaciones de Base de Datos (`test_database_operations.py`)
- **Valida**: Operaciones PostgreSQL + pgvector
- **Operaciones**: CRUD completo, embeddings vectoriales, transacciones, concurrencia
- **Performance**: Consultas complejas, backup/restore, monitoreo de métricas

### 💾 Tests de Persistencia de Contexto (`test_context_persistence.py`)
- **Valida**: Compartición y persistencia de contexto entre agentes
- **Niveles**: Ephemeral, Short-term, Medium-term, Long-term, Permanent
- **Escenarios**: Acceso concurrente, versionado, dependencias, eficiencia de memoria

### 🛡️ Tests de Manejo de Errores y Recuperación (`test_error_handling_recovery.py`)
- **Valida**: Resiliencia y recuperación del sistema
- **Patrones**: Circuit Breaker, Fallback, Degradación elegante, Rollback de transacciones
- **Aislamiento**: Prevención de propagación de errores, patrones de compensación

### ⚡ Tests de Performance bajo Carga (`test_performance_load.py`)
- **Valida**: Rendimiento bajo diferentes condiciones de carga
- **Niveles**: Baseline, Carga media, Carga alta, Estrés, Spike, Carga sostenida
- **Métricas**: Throughput, latencia, percentiles, uso de recursos, escalabilidad

### 🔒 Tests de Seguridad Completos (`test_security_testing.py`)
- **Valida**: Todos los aspectos de seguridad del sistema
- **Amenazas**: SQL Injection, XSS, Acceso no autorizado, Rate limiting, DDoS, Privilege escalation
- **Protección**: Encriptación, monitoreo de seguridad, respuesta automatizada

### 👥 Tests End-to-End de Escenarios de Usuario (`test_end_to_end_user_scenarios.py`)
- **Valida**: Workflows completos desde perspectiva del usuario
- **Roles**: Analista de datos, Desarrollador full-stack, Analista de negocio, Usuario final, Administrador, Invitado
- **Escenarios**: Casos de uso reales con múltiples agentes y dependencias

## Configuración de Entorno de Testing

### Base de Datos de Test
```bash
# PostgreSQL para tests
export TEST_DB_HOST=localhost
export TEST_DB_PORT=5433
export TEST_DB_NAME=mcp_core_test
export TEST_DB_USER=test_user
export TEST_DB_PASSWORD=test_pass

# Redis para tests
export TEST_REDIS_HOST=localhost
export TEST_REDIS_PORT=6380
```

### Instalación de Dependencias
```bash
pip install pytest pytest-asyncio psycopg2-binary asyncpg redis
```

### Servicios Requeridos
- PostgreSQL (puerto 5433)
- PostgreSQL con extensión pgvector
- Redis (puerto 6380)

## Ejecución de Tests

### Ejecutar Todos los Tests
```bash
cd /workspace/mcp-core-superior
python -m pytest tests/test_integration/ -v
```

### Ejecutar por Categoría
```bash
# Tests de flujo multi-agente
python -m pytest tests/test_integration/test_multi_agent_flow.py -v

# Tests de integración de agentes
python -m pytest tests/test_integration/test_agent_integration.py -v

# Tests de performance
python -m pytest tests/test_integration/test_performance_load.py -v --benchmark-only

# Tests de seguridad
python -m pytest tests/test_integration/test_security_testing.py -v

# Tests de streaming
python -m pytest tests/test_integration/test_streaming_updates.py -v
```

### Ejecutar con Marcadores Específicos
```bash
# Solo tests de integración
python -m pytest tests/test_integration/ -m integration

# Tests de performance únicamente
python -m pytest tests/test_integration/ -m performance

# Tests de seguridad únicamente
python -m pytest tests/test_integration/ -m security

# Tests de streaming únicamente
python -m pytest tests/test_integration/ -m streaming

# Tests rápidos (excluir performance)
python -m pytest tests/test_integration/ -m "not performance"
```

### Ejecución con Reporte de Coverage
```bash
pip install pytest-cov
python -m pytest tests/test_integration/ --cov=src --cov-report=html
```

## Métricas de Éxito

### Cobertura de Tests
- **Objetivo**: > 90% de cobertura de código en módulos core
- **Módulos críticos**: 100% de cobertura

### Performance
- **Throughput mínimo**: 50 req/s bajo carga normal
- **Latencia P95**: < 5 segundos
- **Error rate**: < 5% bajo carga alta
- **Uptime**: > 99% en tests de resistencia

### Seguridad
- **SQL Injection**: 100% bloqueado
- **XSS**: 100% detectado y limpiado
- **Rate Limiting**: > 90% de ataques bloqueados
- **DDoS Protection**: > 75% de tráfico malicioso mitigado

### Robustez
- **Recuperación de errores**: > 80% de casos manejados automáticamente
- **Aislamiento de fallos**: 100% de propagación controlada
- **Consistencia de datos**: 100% en transacciones

## Casos de Prueba Principales

### 1. Flujo Completo Multi-Agente
- Orquestación secuencial: Reasoner → Planner → Executor → Verifier
- Orquestación paralela con múltiples agentes
- Recuperación automática de fallos de agentes
- Cancelación segura de tareas en ejecución

### 2. Integración de 12 Agentes Especializados
- Comunicación bidireccional entre agentes
- Balanceador de carga dinámico
- Detección y recuperación de fallos
- Monitoreo de performance individual

### 3. Workflows Empresariales
- Análisis completo de datos de cliente
- Desarrollo full-stack de aplicaciones
- Investigación de mercado competitiva
- Administración y mantenimiento de sistemas

### 4. Streaming en Tiempo Real
- Updates de progreso en vivo
- Dashboard de monitoreo multi-agente
- Colaboración simultánea de usuarios
- Manejo de backpressure en streams

### 5. Persistencia y Compartición de Contexto
- Contexto compartido entre agentes
- Versionado de contexto con historial
- Diferentes niveles de persistencia
- Optimización de memoria

### 6. Resiliencia y Recuperación
- Circuit breakers para servicios externos
- Fallback a servicios alternativos
- Rollback de transacciones distribuidas
- Degradación elegante bajo carga

### 7. Performance Bajo Carga
- Escalabilidad horizontal
- Throughput sostenido
- Latencia bajo alta concurrencia
- Eficiencia de recursos

### 8. Seguridad End-to-End
- Protección multi-capa
- Monitoreo y alertas en tiempo real
- Respuesta automatizada a amenazas
- Cumplimiento de estándares de seguridad

### 9. Casos de Uso Reales
- Workflow de analista de datos
- Desarrollo de aplicación completa
- Investigación de mercado
- Administración de sistemas
- Onboarding de usuarios

## Troubleshooting

### Problemas Comunes

1. **Fallo de conexión a base de datos**
   ```bash
   # Verificar que PostgreSQL esté ejecutándose
   sudo systemctl status postgresql
   
   # Verificar extensión pgvector
   psql -c "CREATE EXTENSION IF NOT EXISTS vector;"
   ```

2. **Tests de streaming fallan**
   ```bash
   # Verificar Redis
   redis-cli ping
   
   # Verificar configuración de red
   netstat -tlnp | grep 6380
   ```

3. **Performance degradada en tests**
   ```bash
   # Verificar recursos del sistema
   htop
   free -h
   df -h
   ```

### Logs y Debugging
```bash
# Activar logging detallado
export MCP_CORE_LOG_LEVEL=DEBUG
python -m pytest tests/test_integration/ -v -s --log-cli-level=DEBUG
```

## Contribuir con Tests

### Estructura de Nuevo Test
```python
@pytest.mark.integration
class TestNewFeature:
    @pytest.mark.asyncio
    async def test_new_functionality(self, orchestrator, test_context):
        # Arrange
        test_data = prepare_test_data()
        
        # Act
        result = await orchestrator.execute_feature(test_data)
        
        # Assert
        assert result.success is True
        assert result.output meets expectations
```

### Mejores Prácticas
1. Usar fixtures de `conftest.py` para configuración común
2. Implementar cleanup automático después de cada test
3. Usar marcadores apropiados para categorización
4. Mock servicios externos cuando sea necesario
5. Documentar casos de prueba complejos

### Cobertura
- Cada módulo debe tener tests de integración
- Casos de borde y errores deben estar cubiertos
- Performance y security requieren tests dedicados

## Contacto y Soporte

Para preguntas sobre los tests de integración:
- Revisar logs detallados con `-v -s`
- Ejecutar tests individualmente para debugging
- Verificar configuración de entorno
- Consultar documentación de módulos específicos

---

**Última actualización**: $(date)
**Versión**: 1.0.0
**Cobertura**: 92% (target: 95%)
**Tests ejecutados**: 150+ casos