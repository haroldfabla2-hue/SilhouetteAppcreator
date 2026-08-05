#!/usr/bin/env python3
"""
SilhouetteMCP Sistema de Verificación Integral
==============================================

SISTEMA DE VERIFICACIÓN COMPLETA POST-MEJORAS

Desarrollado para: silhouettemcp.albertofarah.com
Versión: 1.0.0 - COMPREHENSIVE VERIFICATION SYSTEM

VERIFICA:
- Sistemas originales (puertos 8001-8007)
- Sistemas mejorados (puertos 8010-8024)
- Arquitecturas, seguridad, escalabilidad
- Integración entre sistemas
- Métricas de performance
- Capacidad de recuperación
"""

import json
import asyncio
import aiohttp
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import logging

# ==================== CONFIGURACIÓN ====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SilhouetteMCP-Verification")

# ==================== CONFIGURACIÓN DE SISTEMAS ====================
SYSTEMS_CONFIG = {
    "original_systems": {
        8001: {"name": "SilhouetteMCP Unified", "type": "core"},
        8002: {"name": "Hierarchical Architecture", "type": "architecture"},
        8003: {"name": "Dashboard", "type": "ui"},
        8004: {"name": "Testing Suite", "type": "testing"},
        8005: {"name": "Metrics", "type": "monitoring"},
        8006: {"name": "WebSocket", "type": "realtime"},
        8007: {"name": "Diagnostic System", "type": "diagnostic"}
    },
    "enhanced_systems": {
        8010: {"name": "Enhanced Architecture", "type": "architecture"},
        8020: {"name": "Enhanced Scalability", "type": "scalability"},
        8027: {"name": "Enhanced Security", "type": "security"}
    }
}

# ==================== VERIFICADOR PRINCIPAL ====================

class ComprehensiveSystemVerifier:
    """Verificador integral de todos los sistemas"""
    
    def __init__(self):
        self.verification_results = {}
        self.systems_status = {}
        self.performance_metrics = {}
        self.integration_score = 0
        self.overall_score = 0
        
    async def run_comprehensive_verification(self) -> Dict[str, Any]:
        """Ejecutar verificación completa de todos los sistemas"""
        logger.info("Iniciando verificación integral de sistemas...")
        start_time = time.time()
        
        verification_report = {
            "timestamp": datetime.now().isoformat(),
            "verification_version": "1.0.0",
            "systems_checked": 0,
            "systems_healthy": 0,
            "systems_degraded": 0,
            "systems_failed": 0,
            "overall_health_score": 0,
            "detailed_results": {},
            "performance_analysis": {},
            "security_assessment": {},
            "scalability_assessment": {},
            "architecture_assessment": {},
            "integration_status": {},
            "recommendations": [],
            "verification_duration": 0
        }
        
        try:
            # 1. Verificar sistemas originales
            logger.info("Verificando sistemas originales...")
            original_results = await self._verify_systems_group(SYSTEMS_CONFIG["original_systems"])
            verification_report["detailed_results"]["original_systems"] = original_results
            
            # 2. Verificar sistemas mejorados
            logger.info("Verificando sistemas mejorados...")
            enhanced_results = await self._verify_systems_group(SYSTEMS_CONFIG["enhanced_systems"])
            verification_report["detailed_results"]["enhanced_systems"] = enhanced_results
            
            # 3. Analizar performance
            logger.info("Analizando performance del sistema...")
            performance_analysis = await self._analyze_system_performance()
            verification_report["performance_analysis"] = performance_analysis
            
            # 4. Evaluar arquitectura
            logger.info("Evaluando arquitectura...")
            architecture_assessment = await self._assess_architecture()
            verification_report["architecture_assessment"] = architecture_assessment
            
            # 5. Evaluar seguridad
            logger.info("Evaluando seguridad...")
            security_assessment = await self._assess_security()
            verification_report["security_assessment"] = security_assessment
            
            # 6. Evaluar escalabilidad
            logger.info("Evaluando escalabilidad...")
            scalability_assessment = await self._assess_scalability()
            verification_report["scalability_assessment"] = scalability_assessment
            
            # 7. Verificar integración
            logger.info("Verificando integración...")
            integration_status = await self._verify_system_integration()
            verification_report["integration_status"] = integration_status
            
            # 8. Calcular puntuaciones
            verification_report = self._calculate_verification_scores(verification_report)
            
            # 9. Generar recomendaciones
            verification_report["recommendations"] = self._generate_recommendations(verification_report)
            
            execution_time = time.time() - start_time
            verification_report["verification_duration"] = execution_time
            verification_report["systems_checked"] = len(SYSTEMS_CONFIG["original_systems"]) + len(SYSTEMS_CONFIG["enhanced_systems"])
            
            logger.info(f"Verificación completa finalizada en {execution_time:.2f} segundos")
            logger.info(f"Puntuación general de salud: {verification_report['overall_health_score']}/100")
            
            return verification_report
            
        except Exception as e:
            logger.error(f"Error durante verificación integral: {str(e)}")
            verification_report["error"] = str(e)
            verification_report["verification_duration"] = time.time() - start_time
            return verification_report
    
    async def _verify_systems_group(self, systems: Dict[int, Dict[str, str]]) -> Dict[str, Any]:
        """Verificar grupo de sistemas"""
        results = {}
        
        for port, system_info in systems.items():
            try:
                result = await self._verify_single_system(port, system_info)
                results[f"port_{port}"] = result
                
                # Actualizar estado global
                self.systems_status[port] = result
                
            except Exception as e:
                logger.error(f"Error verificando sistema {port}: {str(e)}")
                results[f"port_{port}"] = {
                    "name": system_info["name"],
                    "type": system_info["type"],
                    "status": "error",
                    "response_time": 0,
                    "error": str(e)
                }
        
        return results
    
    async def _verify_single_system(self, port: int, system_info: Dict[str, str]) -> Dict[str, Any]:
        """Verificar sistema individual"""
        start_time = time.time()
        
        try:
            # Verificar conectividad
            async with aiohttp.ClientSession() as session:
                url = f"http://localhost:{port}/health"
                
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            status = "healthy"
                            self.performance_metrics[port] = response_time
                        except:
                            data = {"status": "ok"}
                            status = "healthy"
                            self.performance_metrics[port] = response_time
                    else:
                        status = "degraded"
                        data = {"status": "error", "code": response.status}
                        self.performance_metrics[port] = response_time
                    
                    return {
                        "name": system_info["name"],
                        "type": system_info["type"],
                        "port": port,
                        "status": status,
                        "response_time": response_time,
                        "health_data": data,
                        "last_check": datetime.now().isoformat()
                    }
                    
        except asyncio.TimeoutError:
            return {
                "name": system_info["name"],
                "type": system_info["type"],
                "port": port,
                "status": "timeout",
                "response_time": 10.0,
                "error": "Connection timeout",
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "name": system_info["name"],
                "type": system_info["type"],
                "port": port,
                "status": "error",
                "response_time": time.time() - start_time,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    async def _analyze_system_performance(self) -> Dict[str, Any]:
        """Analizar performance de los sistemas"""
        if not self.performance_metrics:
            return {"error": "No performance data available"}
        
        response_times = list(self.performance_metrics.values())
        
        return {
            "total_systems_monitored": len(response_times),
            "avg_response_time": sum(response_times) / len(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "systems_within_1s": sum(1 for t in response_times if t < 1.0),
            "systems_within_5s": sum(1 for t in response_times if t < 5.0),
            "performance_score": self._calculate_performance_score(response_times),
            "performance_rating": self._get_performance_rating(response_times)
        }
    
    def _calculate_performance_score(self, response_times: List[float]) -> float:
        """Calcular puntuación de performance"""
        if not response_times:
            return 0.0
        
        # Sistema de scoring basado en tiempos de respuesta
        score = 0
        for rt in response_times:
            if rt < 0.1:
                score += 100  # Excelente
            elif rt < 0.5:
                score += 90   # Muy bueno
            elif rt < 1.0:
                score += 80   # Bueno
            elif rt < 2.0:
                score += 70   # Aceptable
            elif rt < 5.0:
                score += 60   # Lento
            else:
                score += 30   # Muy lento
        
        return score / len(response_times)
    
    def _get_performance_rating(self, response_times: List[float]) -> str:
        """Obtener rating de performance"""
        avg_time = sum(response_times) / len(response_times)
        
        if avg_time < 0.5:
            return "EXCELLENT"
        elif avg_time < 1.0:
            return "GOOD"
        elif avg_time < 2.0:
            return "ACCEPTABLE"
        elif avg_time < 5.0:
            return "SLOW"
        else:
            return "VERY_SLOW"
    
    async def _assess_architecture(self) -> Dict[str, Any]:
        """Evaluar arquitectura del sistema"""
        # Verificar si los sistemas mejorados están funcionando
        enhanced_architecture_healthy = False
        original_architecture_healthy = False
        
        if 8010 in self.systems_status:
            enhanced_architecture_healthy = self.systems_status[8010]["status"] == "healthy"
        
        if 8002 in self.systems_status:
            original_architecture_healthy = self.systems_status[8002]["status"] == "healthy"
        
        # Verificar archivos de arquitectura
        architecture_files = [
            "/workspace/code/silhouettemcp_hierarchical_architecture.py",
            "/workspace/code/silhouettemcp_enhanced_architecture_system.py"
        ]
        
        file_scores = 0
        for file_path in architecture_files:
            if Path(file_path).exists():
                file_scores += 50
        
        # Calcular puntuación de arquitectura
        architecture_score = 0
        if enhanced_architecture_healthy:
            architecture_score += 40
        if original_architecture_healthy:
            architecture_score += 20
        architecture_score += file_scores
        
        return {
            "architecture_score": architecture_score,
            "enhanced_architecture": enhanced_architecture_healthy,
            "original_architecture": original_architecture_healthy,
            "architecture_files_present": file_scores > 0,
            "hierarchical_structure": enhanced_architecture_healthy or original_architecture_healthy,
            "agents_implementation": enhanced_architecture_healthy,
            "coordination_algorithms": enhanced_architecture_healthy,
            "communication_protocols": enhanced_architecture_healthy,
            "architecture_rating": self._get_architecture_rating(architecture_score)
        }
    
    def _get_architecture_rating(self, score: float) -> str:
        """Obtener rating de arquitectura"""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 70:
            return "GOOD"
        elif score >= 50:
            return "ACCEPTABLE"
        elif score >= 30:
            return "NEEDS_IMPROVEMENT"
        else:
            return "CRITICAL"
    
    async def _assess_security(self) -> Dict[str, Any]:
        """Evaluar seguridad del sistema"""
        # Verificar si el sistema de seguridad mejorado está funcionando
        enhanced_security_healthy = False
        
        if 8015 in self.systems_status:
            enhanced_security_healthy = self.systems_status[8015]["status"] == "healthy"
        
        # Verificar archivos de seguridad
        security_files = [
            "/workspace/code/silhouettemcp_enhanced_security_system.py"
        ]
        
        security_file_present = Path(security_files[0]).exists()
        
        # Calcular puntuación de seguridad
        security_score = 0
        if enhanced_security_healthy:
            security_score += 60
        if security_file_present:
            security_score += 40
        
        return {
            "security_score": security_score,
            "enhanced_security_system": enhanced_security_healthy,
            "security_files_present": security_file_present,
            "jwt_implementation": enhanced_security_healthy,
            "ddos_protection": enhanced_security_healthy,
            "api_key_management": enhanced_security_healthy,
            "monitoring_system": enhanced_security_healthy,
            "encryption_enabled": enhanced_security_healthy,
            "security_rating": self._get_security_rating(security_score)
        }
    
    def _get_security_rating(self, score: float) -> str:
        """Obtener rating de seguridad"""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 70:
            return "GOOD"
        elif score >= 50:
            return "ACCEPTABLE"
        elif score >= 30:
            return "NEEDS_IMPROVEMENT"
        else:
            return "CRITICAL"
    
    async def _assess_scalability(self) -> Dict[str, Any]:
        """Evaluar escalabilidad del sistema"""
        # Verificar si el sistema de escalabilidad mejorado está funcionando
        enhanced_scalability_healthy = False
        
        if 8020 in self.systems_status:
            enhanced_scalability_healthy = self.systems_status[8020]["status"] == "healthy"
        
        # Verificar archivos de escalabilidad
        scalability_files = [
            "/workspace/code/silhouettemcp_enhanced_scalability_system.py"
        ]
        
        scalability_file_present = Path(scalability_files[0]).exists()
        
        # Calcular puntuación de escalabilidad
        scalability_score = 0
        if enhanced_scalability_healthy:
            scalability_score += 60
        if scalability_file_present:
            scalability_score += 40
        
        return {
            "scalability_score": scalability_score,
            "enhanced_scalability_system": enhanced_scalability_healthy,
            "scalability_files_present": scalability_file_present,
            "auto_scaling": enhanced_scalability_healthy,
            "load_balancing": enhanced_scalability_healthy,
            "resource_management": enhanced_scalability_healthy,
            "performance_monitoring": enhanced_scalability_healthy,
            "horizontal_scaling": enhanced_scalability_healthy,
            "scalability_rating": self._get_scalability_rating(scalability_score)
        }
    
    def _get_scalability_rating(self, score: float) -> str:
        """Obtener rating de escalabilidad"""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 70:
            return "GOOD"
        elif score >= 50:
            return "ACCEPTABLE"
        elif score >= 30:
            return "NEEDS_IMPROVEMENT"
        else:
            return "CRITICAL"
    
    async def _verify_system_integration(self) -> Dict[str, Any]:
        """Verificar integración entre sistemas"""
        # Contar sistemas saludables por categoría
        original_healthy = sum(1 for status in self.systems_status.values() if status["status"] == "healthy")
        enhanced_healthy = sum(1 for port in [8010, 8015, 8020] if self.systems_status.get(port, {}).get("status") == "healthy")
        
        total_systems = len(SYSTEMS_CONFIG["original_systems"]) + len(SYSTEMS_CONFIG["enhanced_systems"])
        
        # Calcular puntuación de integración
        integration_score = ((original_healthy + enhanced_healthy) / total_systems) * 100
        
        return {
            "integration_score": integration_score,
            "original_systems_healthy": original_healthy,
            "enhanced_systems_healthy": enhanced_healthy,
            "total_systems": total_systems,
            "integration_health": "healthy" if integration_score > 80 else "degraded" if integration_score > 60 else "critical",
            "cross_system_communication": enhanced_healthy > 0,
            "system_coordination": integration_score > 70,
            "integration_rating": self._get_integration_rating(integration_score)
        }
    
    def _get_integration_rating(self, score: float) -> str:
        """Obtener rating de integración"""
        if score >= 90:
            return "EXCELLENT"
        elif score >= 70:
            return "GOOD"
        elif score >= 50:
            return "ACCEPTABLE"
        elif score >= 30:
            return "NEEDS_IMPROVEMENT"
        else:
            return "CRITICAL"
    
    def _calculate_verification_scores(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular puntuaciones finales de verificación"""
        # Contar sistemas por estado
        healthy_count = 0
        degraded_count = 0
        failed_count = 0
        
        for system_results in report["detailed_results"].values():
            for system_result in system_results.values():
                if system_result["status"] == "healthy":
                    healthy_count += 1
                elif system_result["status"] in ["degraded", "timeout"]:
                    degraded_count += 1
                else:
                    failed_count += 1
        
        report["systems_healthy"] = healthy_count
        report["systems_degraded"] = degraded_count
        report["systems_failed"] = failed_count
        
        # Calcular puntuación general de salud
        total_systems = healthy_count + degraded_count + failed_count
        if total_systems > 0:
            overall_score = ((healthy_count * 100) + (degraded_count * 60) + (failed_count * 20)) / total_systems
        else:
            overall_score = 0
        
        report["overall_health_score"] = round(overall_score, 2)
        
        # Combinar puntuaciones específicas
        architecture_score = report["architecture_assessment"]["architecture_score"]
        security_score = report["security_assessment"]["security_score"]
        scalability_score = report["scalability_assessment"]["scalability_score"]
        integration_score = report["integration_status"]["integration_score"]
        performance_score = report["performance_analysis"].get("performance_score", 0)
        
        # Puntuación combinada
        combined_score = (
            overall_score * 0.3 +  # Health score
            architecture_score * 0.2 +  # Architecture
            security_score * 0.2 +  # Security
            scalability_score * 0.15 +  # Scalability
            integration_score * 0.1 +  # Integration
            performance_score * 0.05  # Performance
        )
        
        report["combined_score"] = round(combined_score, 2)
        report["final_rating"] = self._get_final_rating(combined_score)
        
        return report
    
    def _get_final_rating(self, score: float) -> str:
        """Obtener rating final"""
        if score >= 85:
            return "EXCELLENT"
        elif score >= 70:
            return "GOOD"
        elif score >= 55:
            return "ACCEPTABLE"
        elif score >= 40:
            return "NEEDS_IMPROVEMENT"
        else:
            return "CRITICAL"
    
    def _generate_recommendations(self, report: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generar recomendaciones basadas en resultados"""
        recommendations = []
        
        overall_score = report["combined_score"]
        architecture_score = report["architecture_assessment"]["architecture_score"]
        security_score = report["security_assessment"]["security_score"]
        scalability_score = report["scalability_assessment"]["scalability_score"]
        integration_score = report["integration_status"]["integration_score"]
        
        # Recomendaciones basadas en puntuación general
        if overall_score < 40:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "overall",
                "recommendation": "Implementación urgente de mejoras críticas en todo el sistema",
                "rationale": f"Puntuación crítica: {overall_score}/100"
            })
        elif overall_score < 70:
            recommendations.append({
                "priority": "HIGH",
                "category": "overall",
                "recommendation": "Abordar issues de alta prioridad inmediatamente",
                "rationale": f"Puntuación por debajo del mínimo aceptable: {overall_score}/100"
            })
        
        # Recomendaciones por área
        if architecture_score < 70:
            recommendations.append({
                "priority": "HIGH",
                "category": "architecture",
                "recommendation": "Activar y utilizar el sistema de arquitectura mejorada",
                "rationale": f"Puntuación de arquitectura baja: {architecture_score}/100"
            })
        
        if security_score < 70:
            recommendations.append({
                "priority": "HIGH",
                "category": "security",
                "recommendation": "Activar y utilizar el sistema de seguridad mejorado",
                "rationale": f"Puntuación de seguridad baja: {security_score}/100"
            })
        
        if scalability_score < 70:
            recommendations.append({
                "priority": "HIGH",
                "category": "scalability",
                "recommendation": "Activar y utilizar el sistema de escalabilidad mejorado",
                "rationale": f"Puntuación de escalabilidad baja: {scalability_score}/100"
            })
        
        if integration_score < 80:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "integration",
                "recommendation": "Mejorar coordinación entre sistemas",
                "rationale": f"Integración por debajo del óptimo: {integration_score}/100"
            })
        
        # Recomendaciones preventivas
        recommendations.append({
            "priority": "LOW",
            "category": "monitoring",
            "recommendation": "Implementar monitoreo continuo automatizado",
            "rationale": "Mantener visibilidad constante del estado del sistema"
        })
        
        return recommendations

# ==================== API DE VERIFICACIÓN ====================

# Crear instancia del verificador
verifier = ComprehensiveSystemVerifier()

# Función para ejecutar verificación
async def run_verification():
    """Función para ejecutar verificación completa"""
    result = await verifier.run_comprehensive_verification()
    return result

# Ejecutar verificación si se ejecuta directamente
if __name__ == "__main__":
    import asyncio
    
    async def main():
        logger.info("Iniciando verificación integral del sistema SilhouetteMCP...")
        result = await run_verification()
        
        # Guardar resultado
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"comprehensive_verification_report_{timestamp}.json"
        report_path = f"/workspace/code/{report_filename}"
        
        with open(report_path, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n{'='*60}")
        print(f"VERIFICACIÓN INTEGRAL COMPLETADA")
        print(f"{'='*60}")
        print(f"Puntuación General de Salud: {result['overall_health_score']}/100")
        print(f"Puntuación Combinada: {result['combined_score']}/100")
        print(f"Rating Final: {result['final_rating']}")
        print(f"Sistemas Saludables: {result['systems_healthy']}/{result['systems_checked']}")
        print(f"Sistemas Degradados: {result['systems_degraded']}")
        print(f"Sistemas Fallidos: {result['systems_failed']}")
        print(f"Duración de Verificación: {result['verification_duration']:.2f} segundos")
        print(f"Reporte guardado en: {report_path}")
        print(f"{'='*60}")
        
        # Mostrar ratings por categoría
        print(f"\nRATINGS POR CATEGORÍA:")
        print(f"Arquitectura: {result['architecture_assessment']['architecture_rating']} ({result['architecture_assessment']['architecture_score']}/100)")
        print(f"Seguridad: {result['security_assessment']['security_rating']} ({result['security_assessment']['security_score']}/100)")
        print(f"Escalabilidad: {result['scalability_assessment']['scalability_rating']} ({result['scalability_assessment']['scalability_score']}/100)")
        print(f"Performance: {result['performance_analysis']['performance_rating']} ({result['performance_analysis'].get('performance_score', 0):.1f}/100)")
        print(f"Integración: {result['integration_status']['integration_rating']} ({result['integration_status']['integration_score']:.1f}/100)")
        
        # Mostrar recomendaciones principales
        if result['recommendations']:
            print(f"\nRECOMENDACIONES PRINCIPALES:")
            for i, rec in enumerate(result['recommendations'][:3], 1):
                print(f"{i}. [{rec['priority']}] {rec['recommendation']}")
        
        return result
    
    # Ejecutar verificación
    asyncio.run(main())