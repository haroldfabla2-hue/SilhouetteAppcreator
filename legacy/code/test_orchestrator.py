#!/usr/bin/env python3
"""
Script de Prueba para SilhouetteMCP Integration Orchestrator
===========================================================

Script de testing para verificar el funcionamiento del orquestador.
Incluye pruebas de conectividad, endpoints, WebSocket, y métricas.

Uso:
    python test_orchestrator.py
"""

import asyncio
import json
import sys
import time
from typing import Dict, Any

import aiohttp
import websockets
from requests.auth import HTTPBasicAuth

class OrchestratorTester:
    """Tester para el orquestador SilhouetteMCP"""
    
    def __init__(self, base_url: str = "http://localhost:8025"):
        self.base_url = base_url
        self.websocket_url = base_url.replace("http", "ws")
        self.auth_token = None
        self.test_results = []
    
    def log(self, message: str, level: str = "INFO") -> None:
        """Logging simplificado"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        self.test_results.append(f"[{timestamp}] [{level}] {message}")
    
    async def test_connectivity(self) -> bool:
        """Probar conectividad básica"""
        self.log("🔍 Probando conectividad...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ Conectividad OK - Estado: {data.get('status')}")
                        return True
                    else:
                        self.log(f"❌ Error conectividad - Status: {response.status}", "ERROR")
                        return False
        except Exception as e:
            self.log(f"❌ Error conectando al orquestador: {e}", "ERROR")
            return False
    
    async def test_health_check(self) -> bool:
        """Probar endpoint de salud"""
        self.log("❤️  Probando health check...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        self.log(f"✅ Health check OK - Status: {data.get('status')}")
                        self.log(f"   Componentes: {list(data.get('components', {}).keys())}")
                        return True
                    else:
                        self.log(f"❌ Health check falló - Status: {response.status}", "ERROR")
                        return False
        except Exception as e:
            self.log(f"❌ Error en health check: {e}", "ERROR")
            return False
    
    async def test_metrics(self) -> bool:
        """Probar endpoint de métricas"""
        self.log("📊 Probando métricas...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/metrics") as response:
                    if response.status == 200:
                        metrics = await response.json()
                        self.log(f"✅ Métricas obtenidas exitosamente:")
                        self.log(f"   Total servicios: {metrics.get('total_services')}")
                        self.log(f"   Servicios saludables: {metrics.get('healthy_services')}")
                        self.log(f"   Uso CPU: {metrics.get('cpu_usage', 0):.1f}%")
                        self.log(f"   Uso memoria: {metrics.get('memory_usage', 0):.1f}%")
                        self.log(f"   Instancias totales: {metrics.get('total_instances')}")
                        return True
                    else:
                        self.log(f"❌ Error obteniendo métricas - Status: {response.status}", "ERROR")
                        return False
        except Exception as e:
            self.log(f"❌ Error obteniendo métricas: {e}", "ERROR")
            return False
    
    async def test_services(self) -> bool:
        """Probar endpoint de servicios"""
        self.log("🔧 Probando servicios...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/services") as response:
                    if response.status == 200:
                        services = await response.json()
                        self.log(f"✅ Servicios obtenidos: {len(services)} instancias")
                        
                        # Agrupar por servicio
                        service_groups = {}
                        for service in services:
                            service_id = service['config']['service_id']
                            if service_id not in service_groups:
                                service_groups[service_id] = 0
                            service_groups[service_id] += 1
                        
                        self.log("   Distribución por servicio:")
                        for service_id, count in service_groups.items():
                            self.log(f"     • {service_id}: {count} instancias")
                        
                        return True
                    else:
                        self.log(f"❌ Error obteniendo servicios - Status: {response.status}", "ERROR")
                        return False
        except Exception as e:
            self.log(f"❌ Error obteniendo servicios: {e}", "ERROR")
            return False
    
    async def test_authentication(self) -> bool:
        """Probar autenticación"""
        self.log("🔐 Probando autenticación...")
        
        try:
            auth_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/auth/login",
                    json=auth_data
                ) as response:
                    if response.status == 200:
                        auth_response = await response.json()
                        self.auth_token = auth_response.get('token')
                        self.log(f"✅ Autenticación exitosa - Token obtenido")
                        self.log(f"   Expira en: {auth_response.get('expires_in')} segundos")
                        return True
                    else:
                        self.log(f"❌ Autenticación falló - Status: {response.status}", "ERROR")
                        return False
        except Exception as e:
            self.log(f"❌ Error en autenticación: {e}", "ERROR")
            return False
    
    async def test_authenticated_endpoint(self) -> bool:
        """Probar endpoint protegido"""
        if not self.auth_token:
            self.log("⚠️  No hay token de autenticación, saltando test", "WARNING")
            return True
        
        self.log("🔒 Probando endpoint protegido...")
        
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/auth/verify",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        self.log("✅ Endpoint protegido accesible con token")
                        return True
                    else:
                        self.log(f"❌ Error accediendo a endpoint protegido - Status: {response.status}", "ERROR")
                        return False
        except Exception as e:
            self.log(f"❌ Error en endpoint protegido: {e}", "ERROR")
            return False
    
    async def test_websocket(self) -> bool:
        """Probar conexión WebSocket"""
        self.log("🔗 Probando WebSocket...")
        
        try:
            client_id = f"test_client_{int(time.time())}"
            ws_url = f"{self.websocket_url}/ws/{client_id}"
            
            async with websockets.connect(ws_url) as websocket:
                self.log(f"✅ Conexión WebSocket establecida - Cliente: {client_id}")
                
                # Enviar mensaje de prueba
                test_message = {"type": "test", "message": "Hello from test client"}
                await websocket.send(json.dumps(test_message))
                self.log("   Mensaje de prueba enviado")
                
                # Recibir respuesta
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)
                self.log("   Respuesta recibida:")
                self.log(f"     Tipo: {response_data.get('type')}")
                self.log(f"     Timestamp: {response_data.get('timestamp')}")
                
                return True
                
        except asyncio.TimeoutError:
            self.log("❌ Timeout en WebSocket", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Error en WebSocket: {e}", "ERROR")
            return False
    
    async def test_load_balancer_strategies(self) -> bool:
        """Probar estrategias de load balancer"""
        self.log("⚖️  Probando load balancer...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Obtener estrategias disponibles
                async with session.get(f"{self.base_url}/load_balancer/strategies") as response:
                    if response.status == 200:
                        strategies = await response.json()
                        self.log(f"✅ Estrategias de load balancer obtenidas: {len(strategies)}")
                        self.log(f"   Disponibles: {', '.join(strategies)}")
                        
                        # Probar routing con una estrategia
                        routing_data = {"strategy": "round_robin"}
                        async with session.post(
                            f"{self.base_url}/load_balancer/route/enhanced_scalability",
                            json=routing_data
                        ) as route_response:
                            if route_response.status == 200:
                                route_info = await route_response.json()
                                self.log(f"   ✅ Routing exitoso - Servicio: {route_info.get('selected_service')}")
                            else:
                                self.log(f"   ⚠️  Routing falló - Status: {route_response.status}", "WARNING")
                        
                        return True
                    else:
                        self.log(f"❌ Error obteniendo estrategias - Status: {response.status}", "ERROR")
                        return False
        except Exception as e:
            self.log(f"❌ Error en load balancer: {e}", "ERROR")
            return False
    
    async def test_alerts(self) -> bool:
        """Probar sistema de alertas"""
        self.log("🚨 Probando sistema de alertas...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Obtener reglas de alerta
                async with session.get(f"{self.base_url}/alerts/rules") as response:
                    if response.status == 200:
                        alert_rules = await response.json()
                        self.log(f"✅ Reglas de alerta obtenidas: {len(alert_rules)}")
                        for rule in alert_rules:
                            self.log(f"   • {rule.get('name')}: {rule.get('condition')}")
                        
                        # Obtener alertas activas
                        async with session.get(f"{self.base_url}/alerts") as active_response:
                            active_alerts = await active_response.json()
                            self.log(f"   Alertas activas: {len(active_alerts)}")
                        
                        return True
                    else:
                        self.log(f"❌ Error obteniendo reglas - Status: {response.status}", "ERROR")
                        return False
        except Exception as e:
            self.log(f"❌ Error en sistema de alertas: {e}", "ERROR")
            return False
    
    async def run_all_tests(self) -> bool:
        """Ejecutar todos los tests"""
        self.log("🚀 Iniciando suite de tests del orquestador")
        self.log("=" * 80)
        
        tests = [
            ("Conectividad", self.test_connectivity),
            ("Health Check", self.test_health_check),
            ("Métricas", self.test_metrics),
            ("Servicios", self.test_services),
            ("Autenticación", self.test_authentication),
            ("Endpoint Protegido", self.test_authenticated_endpoint),
            ("WebSocket", self.test_websocket),
            ("Load Balancer", self.test_load_balancer_strategies),
            ("Alertas", self.test_alerts),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                self.log(f"\n🧪 Ejecutando test: {test_name}")
                self.log("-" * 60)
                
                if await test_func():
                    passed += 1
                    self.log(f"✅ Test '{test_name}' PASSED")
                else:
                    failed += 1
                    self.log(f"❌ Test '{test_name}' FAILED", "ERROR")
                
            except Exception as e:
                failed += 1
                self.log(f"❌ Test '{test_name}' EXCEPTION: {e}", "ERROR")
        
        self.log("\n" + "=" * 80)
        self.log("📊 RESUMEN DE TESTS")
        self.log("=" * 80)
        self.log(f"✅ Passed: {passed}")
        self.log(f"❌ Failed: {failed}")
        self.log(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            self.log("🎉 ¡Todos los tests pasaron exitosamente!")
        else:
            self.log(f"⚠️  {failed} test(s) fallaron. Revisar logs para detalles.")
        
        return failed == 0
    
    def save_results(self, filename: str = "orchestrator_test_results.log") -> None:
        """Guardar resultados de tests"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.test_results))
            self.log(f"📄 Resultados guardados en: {filename}")
        except Exception as e:
            self.log(f"❌ Error guardando resultados: {e}", "ERROR")

async def main():
    """Función principal"""
    print("🔧 SilhouetteMCP Integration Orchestrator - Test Suite")
    print("=" * 80)
    
    # Verificar argumentos
    base_url = "http://localhost:8025"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"🌐 URL base del orquestador: {base_url}")
    print(f"📱 WebSocket URL: {base_url.replace('http', 'ws')}")
    print("=" * 80)
    
    # Crear tester y ejecutar
    tester = OrchestratorTester(base_url)
    success = await tester.run_all_tests()
    
    # Guardar resultados
    tester.save_results()
    
    # Código de salida
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())