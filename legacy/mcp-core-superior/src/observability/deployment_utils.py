"""
Utilidades de despliegue y configuración para OpenTelemetry en MCP Core Superior

Este módulo proporciona utilidades para desplegar y configurar fácilmente
el sistema de observabilidad en diferentes entornos y configuraciones.
"""

import asyncio
import json
import logging
import os
import subprocess
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .opentelemetry_system import (
    TraceConfig, ExportBackend, SamplingType, TraceLevel, 
    OpenTelemetrySystem, initialize_opentelemetry, get_otel_system
)
from .dashboard_config import DashboardConfig, DashboardType, setup_observability_dashboard
from .fastmcp_integration import FastMCPServerInstrumentor, MCPMiddleware


class DeploymentConfig:
    """Configuración de despliegue para diferentes entornos"""
    
    def __init__(
        self,
        environment: str = "development",
        services: List[str] = None,
        export_backends: List[ExportBackend] = None,
        sampling_type: SamplingType = SamplingType.RATIO_BASED,
        sampling_ratio: float = 0.1,
        jaeger_host: str = "localhost",
        jaeger_port: int = 16686,
        prometheus_port: int = 9090,
        grafana_port: int = 3000,
        enable_dashboard: bool = True,
        custom_config: Dict[str, Any] = None
    ):
        self.environment = environment
        self.services = services or ["fastmcp", "agents", "database", "redis"]
        self.export_backends = export_backends or [ExportBackend.JAEGER, ExportBackend.OTLP]
        self.sampling_type = sampling_type
        self.sampling_ratio = sampling_ratio
        
        # Hosts y puertos de servicios de observabilidad
        self.jaeger_host = jaeger_host
        self.jaeger_port = jaeger_port
        self.prometheus_port = prometheus_port
        self.grafana_port = grafana_port
        
        self.enable_dashboard = enable_dashboard
        self.custom_config = custom_config or {}
    
    def create_trace_config(self) -> TraceConfig:
        """Crear configuración de trace basada en deployment config"""
        return TraceConfig(
            enabled=True,
            export_backend=ExportBackend.ALL if len(self.export_backends) > 1 else self.export_backends[0],
            sampling_type=self.sampling_type,
            sampling_ratio=self.sampling_ratio,
            service_name=f"mcp-core-{self.environment}",
            service_version="1.0.0",
            environment=self.environment,
            trace_level=TraceLevel.DETAILED,
            custom_attributes={
                "deployment.environment": self.environment,
                "deployment.services": ",".join(self.services),
                "deployment.timestamp": str(int(time.time()))
            }
        )
    
    def create_dashboard_config(self) -> DashboardConfig:
        """Crear configuración de dashboard basada en deployment config"""
        return DashboardConfig(
            dashboard_type=DashboardType.GRAFANA if self.enable_dashboard else DashboardType.PROMETHEUS,
            enabled=self.enable_dashboard,
            jaeger_port=self.jaeger_port,
            prometheus_port=self.prometheus_port,
            port=self.grafana_port
        )


class DockerComposeGenerator:
    """Generador de archivos docker-compose para servicios de observabilidad"""
    
    def __init__(self, deployment_config: DeploymentConfig):
        self.config = deployment_config
    
    def generate_compose_file(self) -> Dict[str, Any]:
        """Generar archivo docker-compose completo"""
        services = {}
        
        # Jaeger
        if ExportBackend.JAEGER in self.config.export_backends:
            services["jaeger"] = self._create_jaeger_service()
        
        # Prometheus
        if ExportBackend.PROMETHEUS in self.config.export_backends:
            services["prometheus"] = self._create_prometheus_service()
        
        # Grafana
        if self.config.enable_dashboard:
            services["grafana"] = self._create_grafana_service()
        
        # OpenTelemetry Collector
        services["otel-collector"] = self._create_otel_collector_service()
        
        return {
            "version": "3.8",
            "services": services,
            "networks": {
                "observability": {
                    "driver": "bridge"
                }
            },
            "volumes": {
                "prometheus_data": {},
                "grafana_data": {}
            }
        }
    
    def _create_jaeger_service(self) -> Dict[str, Any]:
        """Crear servicio de Jaeger"""
        return {
            "image": "jaegertracing/all-in-one:1.45",
            "container_name": "jaeger",
            "ports": [
                "5775:5775/udp",
                "6831:6831/udp", 
                "6832:6832/udp",
                "5778:5778",
                f"{self.config.jaeger_port}:16686",
                "14268:14268",
                "14250:14250",
                "9411:9411"
            ],
            "environment": [
                "COLLECTOR_ZIPKIN_HOST_PORT=:9411"
            ],
            "networks": ["observability"],
            "healthcheck": {
                "test": ["CMD", "wget", "--quiet", "--tries=1", "--spider", f"http://localhost:{self.config.jaeger_port}/"],
                "interval": "30s",
                "timeout": "10s",
                "retries": 3
            }
        }
    
    def _create_prometheus_service(self) -> Dict[str, Any]:
        """Crear servicio de Prometheus"""
        return {
            "image": "prom/prometheus:v2.40.0",
            "container_name": "prometheus",
            "ports": [f"{self.config.prometheus_port}:9090"],
            "volumes": [
                "./prometheus.yml:/etc/prometheus/prometheus.yml"
            ],
            "networks": ["observability"],
            "command": [
                "--config.file=/etc/prometheus/prometheus.yml",
                "--storage.tsdb.path=/prometheus",
                "--web.console.libraries=/etc/prometheus/console_libraries",
                "--web.console.templates=/etc/prometheus/consoles",
                "--storage.tsdb.retention.time=200h",
                "--web.enable-lifecycle"
            ]
        }
    
    def _create_grafana_service(self) -> Dict[str, Any]:
        """Crear servicio de Grafana"""
        return {
            "image": "grafana/grafana:9.3.0",
            "container_name": "grafana",
            "ports": [f"{self.config.grafana_port}:3000"],
            "environment": [
                "GF_SECURITY_ADMIN_PASSWORD=admin",
                "GF_USERS_ALLOW_SIGN_UP=false"
            ],
            "volumes": [
                "grafana_data:/var/lib/grafana",
                "./grafana/provisioning:/etc/grafana/provisioning"
            ],
            "networks": ["observability"],
            "depends_on": ["prometheus"]
        }
    
    def _create_otel_collector_service(self) -> Dict[str, Any]:
        """Crear servicio de OpenTelemetry Collector"""
        return {
            "image": "otel/opentelemetry-collector:0.68.0",
            "container_name": "otel-collector",
            "ports": [
                "4317:4317",  # OTLP gRPC
                "4318:4318",  # OTLP HTTP
                "8888:8888",  # Metrics
                "8889:8889",  # Metrics alternative
                "13133:13133" # Health check
            ],
            "volumes": [
                "./otel-collector-config.yaml:/etc/otelcol/config.yaml"
            ],
            "networks": ["observability"],
            "command": ["--config=/etc/otelcol/config.yaml"]
        }
    
    def save_compose_file(self, output_path: Union[str, Path] = "docker-compose.observability.yml"):
        """Guardar archivo docker-compose generado"""
        compose_data = self.generate_compose_file()
        
        with open(output_path, 'w') as f:
            json.dump(compose_data, f, indent=2)
        
        logging.info(f"Docker compose file saved to {output_path}")


class ObservabilityDeployment:
    """Manager de despliegue completo para sistema de observabilidad"""
    
    def __init__(self, deployment_config: DeploymentConfig):
        self.config = deployment_config
        self.otel_system: Optional[OpenTelemetrySystem] = None
        self.logger = logging.getLogger(__name__)
    
    async def deploy_all(self, workspace_path: str = "."):
        """Desplegar todos los componentes de observabilidad"""
        self.logger.info(f"Deploying observability stack for {self.config.environment}")
        
        try:
            # 1. Generar archivos de configuración
            await self._generate_config_files(workspace_path)
            
            # 2. Inicializar sistema OpenTelemetry
            await self._initialize_opentelemetry()
            
            # 3. Configurar dashboard si está habilitado
            if self.config.enable_dashboard:
                await self._setup_dashboard()
            
            # 4. Crear scripts de inicio
            await self._create_startup_scripts(workspace_path)
            
            # 5. Generar documentación
            await self._generate_documentation(workspace_path)
            
            self.logger.info("Observability deployment completed successfully")
            
        except Exception as e:
            self.logger.error(f"Deployment failed: {e}")
            raise
    
    async def _generate_config_files(self, workspace_path: str):
        """Generar archivos de configuración necesarios"""
        base_path = Path(workspace_path) / "observability"
        base_path.mkdir(exist_ok=True)
        
        # Configuración de Prometheus
        await self._generate_prometheus_config(base_path)
        
        # Configuración de Grafana
        await self._generate_grafana_config(base_path)
        
        # Configuración de OpenTelemetry Collector
        await self._generate_otel_collector_config(base_path)
        
        # Docker compose
        compose_generator = DockerComposeGenerator(self.config)
        compose_generator.save_compose_file(base_path / "docker-compose.yml")
    
    async def _generate_prometheus_config(self, base_path: Path):
        """Generar configuración de Prometheus"""
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "alerting": {
                "alertmanagers": [
                    {
                        "static_configs": [{"targets": ["alertmanager:9093"]}]
                    }
                ]
            },
            "rule_files": [
                "alert_rules.yml"
            ],
            "scrape_configs": [
                {
                    "job_name": "prometheus",
                    "static_configs": [{"targets": ["localhost:9090"]}]
                },
                {
                    "job_name": "mcp-core-superior",
                    "static_configs": [{"targets": ["localhost:8080"]}],
                    "metrics_path": "/metrics",
                    "scrape_interval": "15s"
                }
            ]
        }
        
        with open(base_path / "prometheus.yml", 'w') as f:
            json.dump(prometheus_config, f, indent=2)
        
        # Reglas de alertas
        alert_rules = {
            "groups": [
                {
                    "name": "mcp_core_alerts",
                    "rules": [
                        {
                            "alert": "HighErrorRate",
                            "expr": "rate(mcp_trace_errors_count[5m]) / rate(mcp_trace_span_count[5m]) > 0.1",
                            "for": "2m",
                            "labels": {"severity": "warning"},
                            "annotations": {
                                "summary": "High error rate detected in MCP Core",
                                "description": "Error rate is {{ $value }}"
                            }
                        },
                        {
                            "alert": "SlowResponseTime",
                            "expr": "histogram_quantile(0.95, rate(mcp_trace_span_duration_bucket[5m])) > 5",
                            "for": "3m",
                            "labels": {"severity": "warning"},
                            "annotations": {
                                "summary": "Slow response time detected",
                                "description": "95th percentile is {{ $value }}s"
                            }
                        }
                    ]
                }
            ]
        }
        
        with open(base_path / "alert_rules.yml", 'w') as f:
            json.dump(alert_rules, f, indent=2)
    
    async def _generate_grafana_config(self, base_path: Path):
        """Generar configuración de Grafana"""
        grafana_path = base_path / "grafana"
        grafana_path.mkdir(exist_ok=True)
        
        provisioning_path = grafana_path / "provisioning"
        provisioning_path.mkdir(exist_ok=True)
        
        # Configuración de datasources
        datasource_config = {
            "apiVersion": 1,
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "access": "proxy",
                    "url": f"http://prometheus:{self.config.prometheus_port}",
                    "isDefault": True
                },
                {
                    "name": "Jaeger",
                    "type": "jaeger",
                    "access": "proxy", 
                    "url": f"http://jaeger:{self.config.jaeger_port}",
                    "jsonData": {
                        "tracesToLogs": {
                            "tags": ["job", "instance", "pod", "namespace"],
                            "mapTagNamesEnabled": False,
                            "mapTagNames": []
                        }
                    }
                }
            ]
        }
        
        datasource_file = provisioning_path / "datasources" / "datasources.yml"
        datasource_file.parent.mkdir(exist_ok=True)
        
        with open(datasource_file, 'w') as f:
            json.dump(datasource_config, f, indent=2)
        
        # Dashboard de ejemplo
        dashboard_config = {
            "dashboard": {
                "id": None,
                "title": "MCP Core Superior Dashboard",
                "tags": ["mcp", "observability"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Request Rate",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "rate(mcp_trace_span_count[5m])",
                                "legendFormat": "Requests/sec"
                            }
                        ]
                    }
                ]
            },
            "folderId": 0,
            "overwrite": True
        }
        
        dashboard_file = provisioning_path / "dashboards" / "dashboard.yml"
        dashboard_file.parent.mkdir(exist_ok=True)
        
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard_config, f, indent=2)
    
    async def _generate_otel_collector_config(self, base_path: Path):
        """Generar configuración de OpenTelemetry Collector"""
        otel_config = {
            "receivers": {
                "otlp": {
                    "protocols": {
                        "grpc": {},
                        "http": {}
                    }
                },
                "prometheus": {
                    "config": {
                        "scrape_configs": [
                            {
                                "job_name": "mcp-core-superior",
                                "static_configs": [{"targets": ["localhost:8080"]}],
                                "metrics_path": "/metrics"
                            }
                        ]
                    }
                }
            },
            "processors": {
                "batch": {},
                "memory_limiter": {
                    "limit_mib": 512
                }
            },
            "exporters": {
                "jaeger": {
                    "endpoint": f"http://jaeger:14268/api/traces",
                    "tls": {"insecure": True}
                },
                "prometheus": {
                    "endpoint": "prometheus:9090/api/v1/write",
                    "namespace": "mcp_core"
                },
                "logging": {
                    "loglevel": "info"
                }
            },
            "service": {
                "pipelines": {
                    "traces": {
                        "receivers": ["otlp"],
                        "processors": ["memory_limiter", "batch"],
                        "exporters": ["jaeger", "logging"]
                    },
                    "metrics": {
                        "receivers": ["otlp", "prometheus"],
                        "processors": ["memory_limiter", "batch"],
                        "exporters": ["prometheus", "logging"]
                    }
                }
            }
        }
        
        with open(base_path / "otel-collector-config.yaml", 'w') as f:
            json.dump(otel_config, f, indent=2)
    
    async def _initialize_opentelemetry(self):
        """Inicializar sistema OpenTelemetry"""
        trace_config = self.config.create_trace_config()
        self.otel_system = initialize_opentelemetry(trace_config)
        
        self.logger.info("OpenTelemetry system initialized")
    
    async def _setup_dashboard(self):
        """Configurar dashboard de observabilidad"""
        if self.config.enable_dashboard:
            dashboard_config = self.config.create_dashboard_config()
            dashboard = await setup_observability_dashboard(dashboard_config)
            
            self.logger.info(f"Dashboard configured at http://localhost:{self.config.grafana_port}")
    
    async def _create_startup_scripts(self, workspace_path: str):
        """Crear scripts de inicio para el sistema"""
        base_path = Path(workspace_path) / "observability"
        
        # Script de inicio
        start_script = base_path / "start-observability.sh"
        with open(start_script, 'w') as f:
            f.write(f"""#!/bin/bash
# Script de inicio para observabilidad de MCP Core Superior

echo "Starting OpenTelemetry Observability Stack..."

# Verificar que Docker esté ejecutándose
if ! command -v docker &> /dev/null; then
    echo "Docker no está instalado o no está ejecutándose"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose no está instalado"
    exit 1
fi

# Crear directorios necesarios
mkdir -p prometheus grafana/data

# Iniciar servicios de observabilidad
docker-compose -f docker-compose.yml up -d

echo "Observability stack started!"
echo "Jaeger UI: http://localhost:{self.config.jaeger_port}"
echo "Grafana: http://localhost:{self.config.grafana_port} (admin/admin)"
echo "Prometheus: http://localhost:{self.config.prometheus_port}"
echo ""
echo "Para detener el stack: ./observability/stop-observability.sh"
""")
        
        # Script de parada
        stop_script = base_path / "stop-observability.sh"
        with open(stop_script, 'w') as f:
            f.write("""#!/bin/bash
# Script de parada para observabilidad de MCP Core Superior

echo "Stopping OpenTelemetry Observability Stack..."

# Detener servicios
docker-compose -f docker-compose.yml down

echo "Observability stack stopped!"
""")
        
        # Hacer ejecutables
        start_script.chmod(0o755)
        stop_script.chmod(0o755)
        
        self.logger.info("Startup scripts created")
    
    async def _generate_documentation(self, workspace_path: str):
        """Generar documentación del sistema"""
        base_path = Path(workspace_path) / "observability"
        docs_path = base_path / "docs"
        docs_path.mkdir(exist_ok=True)
        
        readme_content = f"""# OpenTelemetry Observability para MCP Core Superior

## Servicios Desplegados

- **Jaeger UI**: http://localhost:{self.config.jaeger_port}
- **Grafana**: http://localhost:{self.config.grafana_port} (admin/admin)
- **Prometheus**: http://localhost:{self.config.prometheus_port}
- **OpenTelemetry Collector**: http://localhost:4317

## Uso en Código

### Inicializar OpenTelemetry
```python
from src.observability import initialize_opentelemetry, TraceConfig, ExportBackend

# Configuración básica
config = TraceConfig(
    export_backend=ExportBackend.JAEGER,
    sampling_type=SamplingType.RATIO_BASED,
    sampling_ratio=0.1
)

otel = initialize_opentelemetry(config)
```

### Instrumentar funciones
```python
from src.observability import trace_function, trace_async_function

@trace_function(operation_type="business_logic")
def my_function():
    pass

@trace_async_function(operation_type="async_operation")
async def my_async_function():
    pass
```

### Crear spans personalizados
```python
from src.observability import create_span, get_correlation_id

with create_span("custom_operation") as span:
    span.set_attribute("custom.attribute", "value")
    # Tu código aquí
```

### Workflow tracking
```python
from src.observability import get_otel_system

otel = get_otel_system()

with otel.create_workflow_span("user_registration", user_id="user123") as span:
    otel.track_workflow_progress(span.trace_id, "validate_input", status="running")
    
    # Validar entrada
    
    otel.track_workflow_progress(span.trace_id, "save_to_db", status="running")
    
    # Guardar en BD
    
    otel.complete_workflow(span.trace_id, status="completed")
```

## Integración con FastMCP Server

```python
from fastapi import FastAPI
from src.observability import instrument_fastmcp_server, MCPMiddleware

app = FastAPI()
middleware = instrument_fastmcp_server(app)
app.add_middleware(MCPMiddleware)
```

## Comandos Útiles

- Iniciar stack: `./observability/start-observability.sh`
- Detener stack: `./observability/stop-observability.sh`
- Ver logs: `docker-compose -f observability/docker-compose.yml logs -f`

## Configuración Avanzada

Modifica los archivos en `observability/` para personalizar:
- `prometheus.yml`: Configuración de Prometheus
- `grafana/provisioning/`: Configuración de Grafana
- `otel-collector-config.yaml`: Configuración del collector

## Métricas Disponibles

- `mcp_trace_span_count`: Número de spans creados
- `mcp_trace_span_duration`: Duración de spans
- `mcp_trace_errors_count`: Número de errores
- `mcp_agent_execution_time`: Tiempo de ejecución de agentes
- `mcp_database_operation_duration`: Duración de operaciones de BD
"""
        
        with open(docs_path / "README.md", 'w') as f:
            f.write(readme_content)
        
        self.logger.info("Documentation generated")


# Funciones de conveniencia para despliegue
async def deploy_observability(
    environment: str = "development",
    enable_dashboard: bool = True,
    export_backends: List[ExportBackend] = None
) -> ObservabilityDeployment:
    """Desplegar sistema completo de observabilidad"""
    config = DeploymentConfig(
        environment=environment,
        enable_dashboard=enable_dashboard,
        export_backends=export_backends or [ExportBackend.JAEGER]
    )
    
    deployment = ObservabilityDeployment(config)
    await deployment.deploy_all()
    
    return deployment


def quick_setup_development():
    """Configuración rápida para desarrollo"""
    return asyncio.run(deploy_observability(
        environment="development",
        enable_dashboard=True,
        export_backends=[ExportBackend.JAEGER]
    ))


# Ejemplo de uso
if __name__ == "__main__":
    asyncio.run(deploy_observability("development"))