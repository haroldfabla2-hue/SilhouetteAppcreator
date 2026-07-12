# API Documentation - OpenAPI/Swagger

## Overview

El MCP Core Superior expone múltiples APIs:

1. **MCP Protocol API** - Herramientas principales del protocolo MCP
2. **REST API** - Endpoints complementarios para administración y monitoreo
3. **Streaming API** - Server-Sent Events para updates en tiempo real
4. **Admin API** - APIs administrativas para gestión del sistema

## 📡 MCP Protocol API

### Base Configuration
```yaml
openapi: 3.0.3
info:
  title: MCP Core Superior API
  description: |
    API completa del MCP Core Superior incluyendo herramientas MCP,
    APIs REST complementarias y streaming endpoints.
  version: 2.0.0
  contact:
    name: MCP Core Superior Team
    url: https://github.com/mcp-core-superior
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: http://localhost:8080
    description: Development server
  - url: https://api.mcp-core-superior.io
    description: Production server
```

### Core MCP Tools

#### 1. analyze_intent - ReasonerAgent
```yaml
analyze_intent:
  post:
    summary: Analiza intención del usuario y define estrategia inicial
    description: |
      Herramienta del ReasonerAgent que analiza la intención del usuario,
      define la estrategia de resolución y enriquece el contexto.
    tags:
      - ReasonerAgent
      - MCP Tools
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - objective
            properties:
              objective:
                type: string
                description: Objetivo o tarea a realizar
                example: "Crear dashboard de ventas con análisis de tendencias Q4"
                minLength: 10
                maxLength: 1000
              context:
                type: object
                description: Contexto adicional para el análisis
                properties:
                  conversation_id:
                    type: string
                    description: ID de conversación para memoria contextual
                    example: "conv_12345"
                  user_preferences:
                    type: object
                    description: Preferencias del usuario
                  domain:
                    type: string
                    enum: [analytics, development, research, general]
                    description: Dominio de la tarea
                  constraints:
                    type: object
                    description: Restricciones específicas
                additionalProperties: true
              user_id:
                type: string
                description: ID del usuario para personalización
                example: "user_67890"
    responses:
      '200':
        description: Análisis de intención completado exitosamente
        content:
          application/json:
            schema:
              type: object
              properties:
                intent_analysis:
                  type: object
                  properties:
                    primary_intent:
                      type: string
                      example: "create_analytics_dashboard"
                    confidence_score:
                      type: number
                      minimum: 0
                      maximum: 1
                      example: 0.95
                    intent_category:
                      type: string
                      enum: [analysis, creation, research, optimization, monitoring]
                    complexity_score:
                      type: number
                      minimum: 0
                      maximum: 1
                      example: 0.8
                strategy_definition:
                  type: object
                  properties:
                    approach:
                      type: string
                      example: "data_first_then_visualization"
                    phases:
                      type: array
                      items:
                        type: string
                      example: ["data_collection", "analysis", "visualization", "validation"]
                    estimated_time_minutes:
                      type: integer
                      minimum: 1
                      example: 45
                context_enrichment:
                  type: object
                  properties:
                    relevant_tools:
                      type: array
                      items:
                        type: string
                      example: ["data_analyzer", "chart_generator", "report_builder"]
                    dependencies:
                      type: array
                      items:
                        type: object
                        properties:
                          tool:
                            type: string
                          reason:
                            type: string
                    success_criteria:
                      type: array
                      items:
                        type: string
                      example: ["dashboard_shows_Q4_data", "includes_trend_analysis", "is_interactive"]
                quality_indicators:
                  type: object
                  properties:
                    clarity_score:
                      type: number
                      example: 0.9
                    feasibility_score:
                      type: number
                      example: 0.85
                    completeness_score:
                      type: number
                      example: 0.8
                metadata:
                  type: object
                  properties:
                    processing_time_ms:
                      type: integer
                      example: 245
                    confidence_overall:
                      type: number
                      example: 0.92
                    model_version:
                      type: string
                      example: "reasoner-v2.1.0"
      '400':
        $ref: '#/components/responses/BadRequest'
      '401':
        $ref: '#/components/responses/Unauthorized'
      '422':
        $ref: '#/components/responses/ValidationError'
      '500':
        $ref: '#/components/responses/InternalError'
```

#### 2. create_execution_plan - PlannerAgent
```yaml
create_execution_plan:
  post:
    summary: Crea plan de ejecución con descomposición de tareas
    description: |
      Herramienta del PlannerAgent que toma el análisis del ReasonerAgent
      y crea un plan detallado de ejecución con descomposición de tareas.
    tags:
      - PlannerAgent
      - MCP Tools
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - objective
              - analysis
            properties:
              objective:
                type: string
                description: Objetivo principal definido inicialmente
                example: "Crear dashboard de ventas Q4"
              analysis:
                type: object
                description: Análisis de intención del ReasonerAgent
                properties:
                  intent_analysis:
                    type: object
                  strategy_definition:
                    type: object
                  context_enrichment:
                    type: object
              constraints:
                type: object
                description: Restricciones y límites para la planificación
                properties:
                  max_time_minutes:
                    type: integer
                    minimum: 1
                    example: 60
                  max_cost_usd:
                    type: number
                    minimum: 0
                    example: 25.50
                  resource_limits:
                    type: object
                    description: Límites de recursos específicos
                  quality_threshold:
                    type: number
                    minimum: 0
                    maximum: 1
                    example: 0.85
              parallel_agents:
                type: boolean
                description: Permitir ejecución paralela de tareas independientes
                default: true
              optimization_criteria:
                type: string
                enum: [speed, cost, quality, balanced]
                default: balanced
                description: Criterio de optimización principal
    responses:
      '200':
        description: Plan de ejecución creado exitosamente
        content:
          application/json:
            schema:
              type: object
              properties:
                execution_plan:
                  type: object
                  properties:
                    plan_id:
                      type: string
                      example: "plan_abcdef123456"
                    total_phases:
                      type: integer
                      example: 4
                    estimated_duration_minutes:
                      type: integer
                      example: 42
                    phases:
                      type: array
                      items:
                        type: object
                        properties:
                          phase_id:
                            type: string
                          phase_name:
                            type: string
                            example: "Data Collection"
                          description:
                            type: string
                          estimated_duration:
                            type: integer
                            description: minutos estimados
                          dependencies:
                            type: array
                            items:
                              type: string
                          parallel_tasks:
                            type: array
                            items:
                              type: object
                              properties:
                                task_id:
                                  type: string
                                tool_name:
                                  type: string
                                parameters:
                                  type: object
                                priority:
                                  type: integer
                                estimated_duration:
                                  type: integer
                                success_criteria:
                                  type: array
                                  items:
                                    type: string
                optimization_report:
                  type: object
                  properties:
                    strategy:
                      type: string
                      example: "parallel_first_then_sequential"
                    optimizations_applied:
                      type: array
                      items:
                        type: string
                      example: ["parallel_execution", "resource_sharing", "caching"]
                    trade_offs:
                      type: array
                      items:
                        type: object
                        properties:
                          tradeoff_type:
                            type: string
                          description:
                            type: string
                          impact_assessment:
                            type: string
                execution_metadata:
                  type: object
                  properties:
                    planning_time_ms:
                      type: integer
                      example: 156
                    optimization_score:
                      type: number
                      example: 0.89
                    risk_assessment:
                      type: object
                      properties:
                        complexity_risk:
                          type: number
                        dependency_risk:
                          type: number
                        resource_risk:
                          type: number
```

#### 3. execute_tasks - ExecutorAgent
```yaml
execute_tasks:
  post:
    summary: Ejecuta herramientas según el plan del PlannerAgent
    description: |
      Herramienta del ExecutorAgent que ejecuta las tareas planificadas
      de manera concurrente, gestiona recursos y consolida resultados.
    tags:
      - ExecutorAgent
      - MCP Tools
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - plan
              - objective
            properties:
              plan:
                type: object
                description: Plan de ejecución del PlannerAgent
                properties:
                  execution_plan:
                    type: object
                  phases:
                    type: array
              objective:
                type: string
                description: Objetivo principal para contextualización
                example: "Crear dashboard de ventas Q4"
              max_concurrent:
                type: integer
                minimum: 1
                maximum: 10
                default: 3
                description: Máximas herramientas concurrentes
              timeout_seconds:
                type: integer
                minimum: 10
                maximum: 3600
                default: 300
                description: Timeout total de ejecución
              streaming_enabled:
                type: boolean
                default: true
                description: Habilitar streaming de progreso
    responses:
      '200':
        description: Tareas ejecutadas exitosamente
        content:
          application/json:
            schema:
              type: object
              properties:
                execution_results:
                  type: object
                  properties:
                    overall_status:
                      type: string
                      enum: [completed, partial_completion, failed]
                      example: "completed"
                    total_tasks:
                      type: integer
                      example: 12
                    successful_tasks:
                      type: integer
                      example: 11
                    failed_tasks:
                      type: integer
                      example: 1
                    total_execution_time:
                      type: integer
                      description: segundos totales
                      example: 245
                    phase_results:
                      type: array
                      items:
                        type: object
                        properties:
                          phase_id:
                            type: string
                          status:
                            type: string
                            enum: [completed, failed, timeout]
                          tasks_in_phase:
                            type: integer
                          completed_tasks:
                            type: integer
                          execution_time:
                            type: integer
                          results:
                            type: object
                          error_details:
                            type: object
                consolidated_outputs:
                  type: object
                  properties:
                    primary_outputs:
                      type: array
                      description: Outputs principales de cada fase
                    intermediate_artifacts:
                      type: array
                      description: Archivos y datos generados
                    data_aggregations:
                      type: object
                      description: Datos consolidados entre fases
                    visualizations:
                      type: array
                      description: Gráficos y dashboards generados
                performance_metrics:
                  type: object
                  properties:
                    throughput_per_minute:
                      type: number
                    resource_utilization:
                      type: object
                      properties:
                        cpu_usage:
                          type: number
                        memory_usage:
                          type: number
                        network_io:
                          type: number
                    error_rate:
                      type: number
                      description: porcentaje de errores
                    parallelism_efficiency:
                      type: number
                      description: eficiencia de ejecución paralela
                execution_metadata:
                  type: object
                  properties:
                    execution_id:
                      type: string
                    started_at:
                      type: string
                      format: date-time
                    completed_at:
                      type: string
                      format: date-time
                    agent_version:
                      type: string
```

#### 4. validate_results - VerifierAgent
```yaml
validate_results:
  post:
    summary: Valida calidad y consistencia de resultados
    description: |
      Herramienta del VerifierAgent que valida los resultados de ejecución,
      verifica criterios de calidad y genera recomendaciones.
    tags:
      - VerifierAgent
      - MCP Tools
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - execution_results
              - validation_criteria
            properties:
              execution_results:
                type: object
                description: Resultados consolidados del ExecutorAgent
              validation_criteria:
                type: array
                description: Criterios específicos de validación
                items:
                  type: object
                  properties:
                    criterion_type:
                      type: string
                      enum: [completeness, accuracy, consistency, timeliness, usability]
                    description:
                      type: string
                    threshold:
                      type: number
                      minimum: 0
                      maximum: 1
                    weight:
                      type: number
                      minimum: 0
                      maximum: 1
              trajectory:
                type: array
                description: Trayectoria completa de ejecución
                items:
                  type: object
                  properties:
                    step_id:
                      type: string
                    step_name:
                      type: string
                    input_data:
                      type: object
                    output_data:
                      type: object
                    duration_ms:
                      type: integer
                    status:
                      type: string
    responses:
      '200':
        description: Validación completada
        content:
          application/json:
            schema:
              type: object
              properties:
                validation_report:
                  type: object
                  properties:
                    overall_quality_score:
                      type: number
                      minimum: 0
                      maximum: 1
                      example: 0.89
                    pass_status:
                      type: string
                      enum: [pass, conditional_pass, fail]
                      example: "pass"
                    validation_results:
                      type: array
                      items:
                        type: object
                        properties:
                          criterion_type:
                            type: string
                          score:
                            type: number
                            minimum: 0
                            maximum: 1
                          status:
                            type: string
                            enum: [pass, fail, warning]
                          details:
                            type: string
                          recommendations:
                            type: array
                            items:
                              type: string
                quality_analysis:
                  type: object
                  properties:
                    completeness_analysis:
                      type: object
                      properties:
                        completion_percentage:
                          type: number
                        missing_components:
                          type: array
                          items:
                            type: string
                        critical_gaps:
                          type: array
                          items:
                            type: string
                    accuracy_assessment:
                      type: object
                      properties:
                        accuracy_score:
                          type: number
                        data_consistency:
                          type: number
                        logical_dependencies:
                          type: array
                          items:
                            type: object
                    consistency_check:
                      type: object
                      properties:
                        internal_consistency:
                          type: number
                        external_consistency:
                          type: number
                        semantic_coherence:
                          type: number
                improvement_recommendations:
                  type: object
                  properties:
                    high_priority:
                      type: array
                      items:
                        type: object
                        properties:
                          recommendation:
                            type: string
                          impact:
                            type: string
                          effort:
                            type: string
                    medium_priority:
                      type: array
                      items:
                        type: object
                        properties:
                          recommendation:
                            type: string
                          impact:
                            type: string
                          effort:
                            type: string
                gates_and_requirements:
                  type: object
                  properties:
                    quality_gates:
                      type: array
                      items:
                        type: object
                        properties:
                          gate_name:
                            type: string
                          status:
                            type: string
                            enum: [passed, failed, skipped]
                          threshold:
                            type: number
                          actual_score:
                            type: number
                    requirements_compliance:
                      type: object
                      properties:
                        must_have:
                          type: array
                          items:
                            type: object
                        should_have:
                          type: array
                          items:
                            type: object
                        could_have:
                          type: array
                          items:
                            type: object
```

#### 5. orchestrate_multitask - Multi-Agent Orchestrator
```yaml
orchestrate_multitask:
  post:
    summary: Ejecuta flujo multi-agente completo
    description: |
      Herramienta principal del orquestador que ejecuta el flujo completo:
      Reasoner → Planner → Executor → Verifier → MemoryManager
    tags:
      - Multi-Agent Orchestrator
      - MCP Tools
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - objective
            properties:
              objective:
                type: string
                description: Objetivo principal a cumplir
                minLength: 10
                example: "Análisis completo de performance Q4 y generación de insights ejecutivos"
              context:
                type: object
                description: Contexto inicial para la orquestación
                properties:
                  conversation_id:
                    type: string
                  user_id:
                    type: string
                  preferences:
                    type: object
                  domain_specifics:
                    type: object
              streaming_enabled:
                type: boolean
                default: true
                description: Activar streaming de progreso en tiempo real
              quality_threshold:
                type: number
                minimum: 0
                maximum: 1
                default: 0.8
                description: Umbral mínimo de calidad para considerar éxito
              max_execution_time:
                type: integer
                minimum: 30
                maximum: 7200
                default: 1800
                description: Timeout máximo en segundos
              optimization_preference:
                type: string
                enum: [speed, quality, cost, balanced]
                default: balanced
    responses:
      '200':
        description: Orquestación multi-agente completada
        content:
          application/json:
            schema:
              type: object
              properties:
                orchestration_result:
                  type: object
                  properties:
                    status:
                      type: string
                      enum: [completed, partial_completion, failed, timeout]
                      example: "completed"
                    overall_quality_score:
                      type: number
                      minimum: 0
                      maximum: 1
                      example: 0.92
                    execution_summary:
                      type: object
                      properties:
                        total_duration:
                          type: integer
                          description: segundos totales
                        phases_completed:
                          type: integer
                        agents_involved:
                          type: array
                          items:
                            type: string
                        final_output_quality:
                          type: number
                    agent_results:
                      type: object
                      properties:
                        reasoner_result:
                          type: object
                        planner_result:
                          type: object
                        executor_result:
                          type: object
                        verifier_result:
                          type: object
                        memory_result:
                          type: object
                    consolidated_outputs:
                      type: object
                      properties:
                        primary_deliverable:
                          type: string
                        supporting_artifacts:
                          type: array
                        generated_insights:
                          type: array
                        recommendations:
                          type: array
                metadata:
                  type: object
                  properties:
                    orchestration_id:
                      type: string
                    started_at:
                      type: string
                      format: date-time
                    completed_at:
                      type: string
                      format: date-time
                    user_id:
                      type: string
                    processing_time:
                      type: object
                      properties:
                        reasoner_ms:
                          type: integer
                        planner_ms:
                          type: integer
                        executor_ms:
                          type: integer
                        verifier_ms:
                          type: integer
                        total_ms:
                          type: integer
                trajectory:
                  type: array
                  description: Traza completa de la ejecución
                  items:
                    type: object
                    properties:
                      phase:
                        type: string
                      step:
                        type: string
                      timestamp:
                        type: string
                        format: date-time
                      duration_ms:
                        type: integer
                      input_data:
                        type: object
                      output_data:
                        type: object
                      status:
                        type: string
                      agent_id:
                        type: string
```

### Status and Monitoring Tools

#### get_agent_status
```yaml
get_agent_status:
  get:
    summary: Obtiene estado actual de todos los agentes
    description: |
      Retorna el estado actual de todos los agentes en el sistema,
      incluyendo métricas de performance y health.
    tags:
      - Status
      - Monitoring
    responses:
      '200':
        description: Estado de agentes obtenido exitosamente
        content:
          application/json:
            schema:
              type: object
              properties:
                system_status:
                  type: string
                  enum: [healthy, degraded, critical]
                  example: "healthy"
                overall_health_score:
                  type: number
                  minimum: 0
                  maximum: 1
                  example: 0.95
                agents:
                  type: object
                  properties:
                    reasoner_agent:
                      type: object
                      properties:
                        status:
                          type: string
                          enum: [online, offline, degraded]
                        last_activity:
                          type: string
                          format: date-time
                        active_tasks:
                          type: integer
                        completed_tasks_last_hour:
                          type: integer
                        average_response_time_ms:
                          type: number
                        success_rate:
                          type: number
                        health_score:
                          type: number
                    planner_agent:
                      type: object
                      # Misma estructura que reasoner_agent
                    executor_agent:
                      type: object
                      # Misma estructura que reasoner_agent
                    verifier_agent:
                      type: object
                      # Misma estructura que reasoner_agent
                    memory_agent:
                      type: object
                      # Misma estructura que reasoner_agent
                    intelligent_router:
                      type: object
                      properties:
                        status:
                          type: string
                        model_accuracy:
                          type: number
                        last_training:
                          type: string
                          format: date-time
                        routing_decisions_last_hour:
                          type: integer
                        optimal_routing_percentage:
                          type: number
                system_metrics:
                  type: object
                  properties:
                    total_active_connections:
                      type: integer
                    requests_per_minute:
                      type: number
                    average_response_time:
                      type: number
                    error_rate:
                      type: number
                    cpu_usage_percent:
                      type: number
                    memory_usage_percent:
                      type: number
                    database_connections_active:
                      type: integer
```

### Components

```yaml
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  responses:
    BadRequest:
      description: La solicitud contiene parámetros inválidos
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    
    Unauthorized:
      description: No autorizado - API key inválida o faltante
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    
    Forbidden:
      description: Acceso prohibido - permisos insuficientes
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    
    NotFound:
      description: Recurso no encontrado
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    
    ValidationError:
      description: Error de validación de datos
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ValidationErrorResponse'
    
    InternalError:
      description: Error interno del servidor
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    
    RateLimitExceeded:
      description: Límite de rate limiting excedido
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'

  schemas:
    ErrorResponse:
      type: object
      required:
        - error
        - message
        - timestamp
      properties:
        error:
          type: string
          enum: [invalid_request, unauthorized, forbidden, not_found, rate_limit_exceeded, internal_error]
        message:
          type: string
          description: Mensaje de error legible para humanos
        timestamp:
          type: string
          format: date-time
        request_id:
          type: string
          description: ID único para tracking del request
    
    ValidationErrorResponse:
      type: object
      required:
        - error
        - message
        - timestamp
        - validation_errors
      properties:
        error:
          type: string
          enum: [validation_error]
        message:
          type: string
        timestamp:
          type: string
          format: date-time
        validation_errors:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
              message:
                type: string
              code:
                type: string
              invalid_value:
                type: any
    
    TaskProgressUpdate:
      type: object
      properties:
        task_id:
          type: string
        status:
          type: string
          enum: [pending, in_progress, completed, failed, cancelled]
        progress:
          type: number
          minimum: 0
          maximum: 1
        current_phase:
          type: string
        message:
          type: string
        timestamp:
          type: string
          format: date-time
        agent_status:
          type: object
          properties:
            reasoner:
              type: string
            planner:
              type: string
            executor:
              type: string
            verifier:
              type: string
            memory:
              type: string
        partial_results:
          type: object
        metadata:
          type: object
```

## 🔄 WebSocket Streaming API

```yaml
/WebSocketAPI:
  get:
    summary: Establecer conexión WebSocket para streaming
    description: |
      Conecta via WebSocket para recibir updates en tiempo real
      de las tareas en ejecución.
    tags:
      - Streaming
    parameters:
      - name: task_id
        in: query
        required: true
        schema:
          type: string
        description: ID de la tarea a monitorear
    responses:
      '101':
        description: Conexión WebSocket establecida
      '400':
        description: Parámetros inválidos
```

## 🔧 Admin API

```yaml
/AdminAPI/v1:
  get:
    summary: Endpoints administrativos
    description: APIs para administración del sistema
    tags:
      - Admin
    security:
      - ApiKeyAuth: []
      - BearerAuth: []
    responses:
      '200':
        description: Admin endpoints disponibles
        content:
          application/json:
            schema:
              type: object
              properties:
                available_endpoints:
                  type: array
                  items:
                    type: object
                    properties:
                      path:
                        type: string
                      method:
                        type: string
                      description:
                        type: string
                      required_permissions:
                        type: array
                        items:
                          type: string
```

---

## 📖 Usage Examples

### MCP Protocol Usage
```python
# Usando el cliente MCP oficial
import asyncio
from mcp import ClientSession

async def main():
    # Inicializar cliente MCP
    client = ClientSession("mcp-core-superior")
    
    # Conectar y ejecutar flujo multi-agente
    async with client:
        result = await client.call_tool("orchestrate_multitask", {
            "objective": "Análisis completo de ventas Q4",
            "streaming_enabled": True,
            "quality_threshold": 0.85
        })
        
        print("Resultado:", result)

asyncio.run(main())
```

### REST API Usage
```python
import aiohttp
import json

async def api_example():
    async with aiohttp.ClientSession() as session:
        headers = {
            "X-API-Key": "your-api-key",
            "Content-Type": "application/json"
        }
        
        # Obtener estado de agentes
        async with session.get(
            "http://localhost:8080/mcp-tools/get_agent_status",
            headers=headers
        ) as response:
            status = await response.json()
            print("Status:", status)
        
        # Ejecutar análisis de intención
        payload = {
            "objective": "Crear dashboard de analytics",
            "context": {
                "domain": "analytics",
                "conversation_id": "conv_123"
            }
        }
        
        async with session.post(
            "http://localhost:8080/mcp-tools/analyze_intent",
            headers=headers,
            json=payload
        ) as response:
            result = await response.json()
            print("Análisis:", result)
```

### Streaming API Usage
```python
import asyncio
import aiohttp

async def stream_example():
    headers = {
        "X-API-Key": "your-api-key",
        "Accept": "text/event-stream"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "http://localhost:8080/streaming/task/task_123",
            headers=headers
        ) as response:
            async for line in response.content:
                if line.startswith(b"data: "):
                    update = json.loads(line[6:])
                    print(f"Progress: {update['progress']}% - {update['message']}")
```

---

**Última actualización**: 2025-11-04  
**Versión de la especificación**: 2.0.0