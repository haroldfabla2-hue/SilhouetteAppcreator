#!/usr/bin/env python3
"""
Load Testing alternativo con Artillery para MCP-Core-Superior vs MiniMax Agent
Configuración de escenarios de carga, estrés y spike testing
"""

import json
import yaml
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ArtilleryConfigGenerator:
    """Generador de configuraciones de Artillery"""
    
    def __init__(self, output_dir: str = "configs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def generate_load_test_config(self, target_url: str, test_name: str = "baseline") -> dict:
        """Generar configuración básica de load test"""
        config = {
            "config": {
                "target": target_url,
                "phases": [
                    {
                        "duration": 60,  # 1 minuto
                        "arrivalRate": 5  # 5 usuarios por segundo
                    },
                    {
                        "duration": 120,  # 2 minutos
                        "arrivalRate": 10  # 10 usuarios por segundo
                    },
                    {
                        "duration": 60,  # 1 minuto
                        "arrivalRate": 15  # 15 usuarios por segundo
                    }
                ],
                "payload": {
                    "path": "test_data.csv",
                    "fields": [
                        "username",
                        "email"
                    ]
                },
                "variables": {
                    "base_url": target_url
                },
                "plugins": {
                    "expect": {},
                    "metrics-by-endpoint": {},
                    "publish-metrics": {
                        "type": "statsd",
                        "host": "localhost",
                        "port": 8125,
                        "prefix": "artillery"
                    }
                }
            },
            "scenarios": [
                {
                    "name": "Health Check Scenario",
                    "weight": 40,
                    "flow": [
                        {
                            "get": {
                                "url": "/api/health",
                                "headers": {
                                    "Authorization": "Bearer {{ $randomString() }}",
                                    "Content-Type": "application/json"
                                },
                                "expect": [
                                    {
                                        "statusCode": 200
                                    },
                                    {
                                        "hasProperty": "status"
                                    }
                                ]
                            }
                        },
                        {
                            "think": 2
                        }
                    ]
                },
                {
                    "name": "Task Execution Scenario",
                    "weight": 35,
                    "flow": [
                        {
                            "post": {
                                "url": "/api/tasks/execute",
                                "headers": {
                                    "Authorization": "Bearer {{ $randomString() }}",
                                    "Content-Type": "application/json"
                                },
                                "json": {
                                    "task_type": "data_processing",
                                    "parameters": {
                                        "input": "{{ $randomString() }}",
                                        "complexity": "{{ $randomString(['low', 'medium', 'high']) }}"
                                    }
                                },
                                "expect": [
                                    {
                                        "statusCode": [200, 201]
                                    }
                                ]
                            }
                        },
                        {
                            "think": 3
                        }
                    ]
                },
                {
                    "name": "Agent Execution Scenario",
                    "weight": 20,
                    "flow": [
                        {
                            "post": {
                                "url": "/api/agents/python_executor/execute",
                                "headers": {
                                    "Authorization": "Bearer {{ $randomString() }}",
                                    "Content-Type": "application/json"
                                },
                                "json": {
                                    "code": "print('Hello World')",
                                    "timeout": 30,
                                    "environment": "test"
                                },
                                "expect": [
                                    {
                                        "statusCode": [200, 201]
                                    }
                                ]
                            }
                        },
                        {
                            "think": 5
                        }
                    ]
                },
                {
                    "name": "Database Operations Scenario",
                    "weight": 15,
                    "flow": [
                        {
                            "post": {
                                "url": "/api/database/SELECT",
                                "headers": {
                                    "Authorization": "Bearer {{ $randomString() }}",
                                    "Content-Type": "application/json"
                                },
                                "json": {
                                    "query": "SELECT * FROM test_table LIMIT 10",
                                    "parameters": {}
                                },
                                "expect": [
                                    {
                                        "statusCode": [200, 201]
                                    }
                                ]
                            }
                        },
                        {
                            "think": 2
                        }
                    ]
                },
                {
                    "name": "Workflow Execution Scenario",
                    "weight": 10,
                    "flow": [
                        {
                            "post": {
                                "url": "/api/workflows/execute",
                                "headers": {
                                    "Authorization": "Bearer {{ $randomString() }}",
                                    "Content-Type": "application/json"
                                },
                                "json": {
                                    "workflow_type": "data_pipeline",
                                    "steps": [
                                        {
                                            "action": "extract",
                                            "source": "api/data"
                                        },
                                        {
                                            "action": "transform",
                                            "operation": "clean"
                                        },
                                        {
                                            "action": "load",
                                            "destination": "database"
                                        }
                                    ],
                                    "timeout": 60
                                },
                                "expect": [
                                    {
                                        "statusCode": [200, 201]
                                    }
                                ]
                            }
                        },
                        {
                            "think": 8
                        }
                    ]
                }
            ]
        }
        
        return config
    
    def generate_stress_test_config(self, target_url: str) -> dict:
        """Generar configuración para stress testing"""
        config = {
            "config": {
                "target": target_url,
                "phases": [
                    {
                        "duration": 30,
                        "arrivalRate": 20,
                        "name": "Ramp up"
                    },
                    {
                        "duration": 60,
                        "arrivalRate": 50,
                        "name": "Sustained load"
                    },
                    {
                        "duration": 30,
                        "arrivalRate": 100,
                        "name": "High load"
                    },
                    {
                        "duration": 30,
                        "arrivalRate": 150,
                        "name": "Peak load"
                    },
                    {
                        "duration": 60,
                        "arrivalRate": 50,
                        "name": "Recovery"
                    }
                ],
                "ensure": {
                    "p95": 2000,
                    "p99": 5000,
                    "maxErrorRate": 5
                }
            },
            "scenarios": [
                {
                    "name": "Stress Test Scenario",
                    "weight": 100,
                    "flow": [
                        {
                            "get": {
                                "url": "/api/health",
                                "expect": [
                                    {
                                        "statusCode": 200
                                    }
                                ]
                            }
                        },
                        {
                            "post": {
                                "url": "/api/tasks/execute",
                                "json": {
                                    "task_type": "stress_test",
                                    "parameters": {
                                        "intensity": "high",
                                        "duration": 10
                                    }
                                },
                                "expect": [
                                    {
                                        "statusCode": [200, 201, 429]
                                    }
                                ]
                            }
                        },
                        {
                            "think": 1
                        }
                    ]
                }
            ]
        }
        
        return config
    
    def generate_spike_test_config(self, target_url: str) -> dict:
        """Generar configuración para spike testing"""
        config = {
            "config": {
                "target": target_url,
                "phases": [
                    {
                        "duration": 60,
                        "arrivalRate": 5,
                        "name": "Normal load"
                    },
                    {
                        "duration": 10,
                        "arrivalRate": 100,
                        "name": "Spike"
                    },
                    {
                        "duration": 60,
                        "arrivalRate": 5,
                        "name": "Back to normal"
                    },
                    {
                        "duration": 10,
                        "arrivalRate": 200,
                        "name": "Bigger spike"
                    },
                    {
                        "duration": 60,
                        "arrivalRate": 5,
                        "name": "Return to normal"
                    }
                ]
            },
            "scenarios": [
                {
                    "name": "Spike Test Scenario",
                    "weight": 100,
                    "flow": [
                        {
                            "get": {
                                "url": "/api/health",
                                "expect": [
                                    {
                                        "statusCode": 200
                                    }
                                ]
                            }
                        },
                        {
                            "think": 0.5
                        }
                    ]
                }
            ]
        }
        
        return config
    
    def generate_soak_test_config(self, target_url: str) -> dict:
        """Generar configuración para soak testing (largo plazo)"""
        config = {
            "config": {
                "target": target_url,
                "phases": [
                    {
                        "duration": 3600,  # 1 hora
                        "arrivalRate": 10,
                        "name": "Extended soak test"
                    }
                ],
                "timeout": 30
            },
            "scenarios": [
                {
                    "name": "Soak Test Scenario",
                    "weight": 100,
                    "flow": [
                        {
                            "get": {
                                "url": "/api/health",
                                "expect": [
                                    {
                                        "statusCode": 200
                                    }
                                ]
                            }
                        },
                        {
                            "post": {
                                "url": "/api/tasks/execute",
                                "json": {
                                    "task_type": "background_processing",
                                    "parameters": {
                                        "priority": "low",
                                        "timeout": 10
                                    }
                                },
                                "expect": [
                                    {
                                        "statusCode": [200, 201]
                                    }
                                ]
                            }
                        },
                        {
                            "think": 3
                        }
                    ]
                }
            ]
        }
        
        return config
    
    def save_config(self, config: dict, filename: str):
        """Guardar configuración a archivo YAML"""
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        logger.info(f"Config saved: {filepath}")
        return filepath
    
    def generate_all_configs(self, mcp_url: str, minimax_url: str):
        """Generar todas las configuraciones para ambos agentes"""
        configs = []
        
        # MCP-Core-Superior configs
        logger.info("Generating configs for MCP-Core-Superior...")
        configs.extend([
            self.save_config(self.generate_load_test_config(mcp_url, "mcp_load_test"), "mcp_load_test.yml"),
            self.save_config(self.generate_stress_test_config(mcp_url), "mcp_stress_test.yml"),
            self.save_config(self.generate_spike_test_config(mcp_url), "mcp_spike_test.yml"),
            self.save_config(self.generate_soak_test_config(mcp_url), "mcp_soak_test.yml")
        ])
        
        # MiniMax configs
        logger.info("Generating configs for MiniMax Agent...")
        configs.extend([
            self.save_config(self.generate_load_test_config(minimax_url, "minimax_load_test"), "minimax_load_test.yml"),
            self.save_config(self.generate_stress_test_config(minimax_url), "minimax_stress_test.yml"),
            self.save_config(self.generate_spike_test_config(minimax_url), "minimax_spike_test.yml"),
            self.save_config(self.generate_soak_test_config(minimax_url), "minimax_soak_test.yml")
        ])
        
        return configs

def create_test_data():
    """Crear datos de prueba para payload"""
    test_data = [
        "username,email",
        "user1,user1@example.com",
        "user2,user2@example.com",
        "user3,user3@example.com",
        "user4,user4@example.com",
        "user5,user5@example.com"
    ]
    
    with open('test_data.csv', 'w') as f:
        f.write('\n'.join(test_data))
    
    logger.info("Test data created: test_data.csv")

def main():
    """Función principal"""
    generator = ArtilleryConfigGenerator()
    
    # URLs de los agentes
    mcp_url = "http://localhost:8000"
    minimax_url = "http://localhost:8001"
    
    # Crear datos de prueba
    create_test_data()
    
    # Generar todas las configuraciones
    configs = generator.generate_all_configs(mcp_url, minimax_url)
    
    logger.info("=" * 60)
    logger.info("ARTILLERY CONFIG GENERATOR COMPLETED")
    logger.info("=" * 60)
    logger.info(f"Generated {len(configs)} configuration files:")
    for config in configs:
        logger.info(f"  • {config}")
    
    logger.info("\nTo run load tests:")
    logger.info("  Load test: artillery run <config_file>")
    logger.info("  Artillery report: artillery report <results_file>")
    logger.info("\nExample:")
    logger.info("  artillery run configs/mcp_load_test.yml --output results/mcp_load_results.json")
    logger.info("  artillery report results/mcp_load_results.json --output results/mcp_load_report.html")

if __name__ == "__main__":
    main()