"""
Agente de Evaluación de Riesgos Financieros
Evalúa y monitorea riesgos en operaciones financieras, transacciones y proveedores
Implementa modelos de scoring, alertas automáticas y reportes de riesgo
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import json
import math

@dataclass
class RiskFactor:
    """Factor de riesgo individual"""
    factor_id: str
    factor_name: str
    category: str  # credit, operational, market, liquidity, compliance
    weight: float
    current_value: float
    threshold_values: Dict[str, float]  # low, medium, high, critical
    trend: str  # improving, stable, deteriorating
    
@dataclass
class RiskAssessment:
    """Evaluación de riesgo completa"""
    assessment_id: str
    entity_id: str  # customer, transaction, account
    assessment_type: str  # credit_score, transaction_risk, operational_risk
    overall_score: float
    risk_level: str  # low, medium, high, critical
    assessment_date: datetime
    factors: List[RiskFactor]
    recommendations: List[str]
    next_review_date: datetime
    confidence_level: float

@dataclass
class RiskAlert:
    """Alerta de riesgo generada"""
    alert_id: str
    alert_type: str  # threshold_breach, trend_change, anomaly
    severity: str  # low, medium, high, critical
    entity_id: str
    risk_factors_affected: List[str]
    triggered_value: float
    threshold_value: float
    description: str
    recommended_actions: List[str]
    generated_at: datetime

@dataclass
class TransactionRiskProfile:
    """Perfil de riesgo de transacción"""
    transaction_id: str
    merchant_risk_score: float
    location_risk_score: float
    amount_risk_score: float
    time_risk_score: float
    device_risk_score: float
    behavior_risk_score: float
    overall_risk_score: float
    risk_factors: Dict[str, Any]
    flags: List[str]

class RiskCategory(Enum):
    CREDIT = "credit"
    OPERATIONAL = "operational"
    MARKET = "market"
    LIQUIDITY = "liquidity"
    COMPLIANCE = "compliance"
    CYBER = "cyber"
    REPUTATIONAL = "reputational"

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskAssessmentAgent:
    """
    Agente especializado en evaluación y gestión de riesgos financieros
    Implementa modelos predictivos, scoring automático y alertas en tiempo real
    """
    
    def __init__(self,
                 risk_models_config: Dict[str, Any],
                 alert_thresholds: Dict[str, Dict[str, float]]):
        
        self.risk_models_config = risk_models_config
        self.alert_thresholds = alert_thresholds
        
        # Modelos de riesgo preconfigurados
        self.risk_models = self._initialize_risk_models()
        
        # Cache de evaluaciones
        self.assessment_cache = {}
        self.alert_history = []
        
        # Configuración de aprendizaje
        self.ml_models = {}
        self.feature_weights = {}
        
    async def assess_credit_risk(self,
                               customer_id: str,
                               application_data: Dict[str, Any],
                               historical_data: Optional[Dict[str, Any]] = None) -> RiskAssessment:
        """
        Evalúa riesgo crediticio de un cliente o aplicación
        """
        assessment_id = self._generate_assessment_id()
        
        try:
            print(f"Evaluando riesgo crediticio para cliente {customer_id}")
            
            # Factores de riesgo crediticio
            credit_factors = [
                RiskFactor(
                    factor_id="credit_score",
                    factor_name="Puntuación Crediticia",
                    category="credit",
                    weight=0.3,
                    current_value=application_data.get("credit_score", 650),
                    threshold_values={"low": 750, "medium": 650, "high": 550, "critical": 400},
                    trend="stable"
                ),
                RiskFactor(
                    factor_id="debt_to_income",
                    factor_name="Ratio Deuda/Ingresos",
                    category="credit",
                    weight=0.25,
                    current_value=application_data.get("debt_to_income", 0.3),
                    threshold_values={"low": 0.2, "medium": 0.35, "high": 0.5, "critical": 0.7},
                    trend="stable"
                ),
                RiskFactor(
                    factor_id="payment_history",
                    factor_name="Historial de Pagos",
                    category="credit",
                    weight=0.2,
                    current_value=application_data.get("payment_history_score", 0.85),
                    threshold_values={"low": 0.95, "medium": 0.85, "high": 0.7, "critical": 0.5},
                    trend="improving"
                ),
                RiskFactor(
                    factor_id="employment_stability",
                    factor_name="Estabilidad Laboral",
                    category="credit",
                    weight=0.15,
                    current_value=application_data.get("employment_years", 3),
                    threshold_values={"low": 5, "medium": 2, "high": 1, "critical": 0.5},
                    trend="stable"
                ),
                RiskFactor(
                    factor_id="bankruptcy_history",
                    factor_name="Historial de Quiebra",
                    category="credit",
                    weight=0.1,
                    current_value=1.0 if application_data.get("bankruptcies", 0) == 0 else 0.2,
                    threshold_values={"low": 1.0, "medium": 0.7, "high": 0.4, "critical": 0.1},
                    trend="stable"
                )
            ]
            
            # Calcular score ponderado
            overall_score = self._calculate_weighted_score(credit_factors)
            risk_level = self._determine_risk_level(overall_score, "credit")
            
            # Generar recomendaciones
            recommendations = self._generate_credit_recommendations(credit_factors, risk_level)
            
            # Crear evaluación
            assessment = RiskAssessment(
                assessment_id=assessment_id,
                entity_id=customer_id,
                assessment_type="credit_score",
                overall_score=overall_score,
                risk_level=risk_level,
                assessment_date=datetime.now(),
                factors=credit_factors,
                recommendations=recommendations,
                next_review_date=datetime.now() + timedelta(days=90),
                confidence_level=0.85
            )
            
            # Cache de la evaluación
            self.assessment_cache[assessment_id] = assessment
            
            # Generar alertas si es necesario
            await self._check_risk_alerts(assessment)
            
            return assessment
            
        except Exception as e:
            raise Exception(f"Error evaluando riesgo crediticio: {str(e)}")
    
    async def assess_transaction_risk(self,
                                    transaction_data: Dict[str, Any]) -> TransactionRiskProfile:
        """
        Evalúa riesgo de una transacción individual en tiempo real
        """
        try:
            tx_id = transaction_data.get("transaction_id", "unknown")
            print(f"Evaluando riesgo de transacción {tx_id}")
            
            # Calcular scores por factor
            merchant_score = await self._assess_merchant_risk(
                transaction_data.get("merchant_id"),
                transaction_data.get("merchant_category")
            )
            
            location_score = await self._assess_location_risk(
                transaction_data.get("location"),
                transaction_data.get("merchant_country")
            )
            
            amount_score = await self._assess_amount_risk(
                transaction_data.get("amount", 0),
                transaction_data.get("customer_id")
            )
            
            time_score = await self._assess_time_risk(
                transaction_data.get("timestamp"),
                transaction_data.get("customer_id")
            )
            
            device_score = await self._assess_device_risk(
                transaction_data.get("device_fingerprint"),
                transaction_data.get("ip_address")
            )
            
            behavior_score = await self._assess_behavior_risk(
                transaction_data,
                transaction_data.get("customer_id")
            )
            
            # Calcular score general
            weights = {
                "merchant": 0.15,
                "location": 0.15,
                "amount": 0.25,
                "time": 0.10,
                "device": 0.15,
                "behavior": 0.20
            }
            
            overall_score = (
                merchant_score * weights["merchant"] +
                location_score * weights["location"] +
                amount_score * weights["amount"] +
                time_score * weights["time"] +
                device_score * weights["device"] +
                behavior_score * weights["behavior"]
            )
            
            # Identificar flags de riesgo
            flags = self._identify_risk_flags({
                "merchant_score": merchant_score,
                "location_score": location_score,
                "amount_score": amount_score,
                "time_score": time_score,
                "device_score": device_score,
                "behavior_score": behavior_score,
                "overall_score": overall_score
            })
            
            profile = TransactionRiskProfile(
                transaction_id=tx_id,
                merchant_risk_score=merchant_score,
                location_risk_score=location_score,
                amount_risk_score=amount_score,
                time_risk_score=time_score,
                device_risk_score=device_score,
                behavior_risk_score=behavior_score,
                overall_risk_score=overall_score,
                risk_factors={
                    "merchant_id": transaction_data.get("merchant_id"),
                    "location": transaction_data.get("location"),
                    "amount": transaction_data.get("amount"),
                    "timestamp": transaction_data.get("timestamp"),
                    "device_fingerprint": transaction_data.get("device_fingerprint")
                },
                flags=flags
            )
            
            # Generar alerta si score supera umbral
            if overall_score > 0.7:
                await self._generate_transaction_alert(profile)
            
            return profile
            
        except Exception as e:
            raise Exception(f"Error evaluando riesgo de transacción: {str(e)}")
    
    async def assess_portfolio_risk(self,
                                  portfolio_data: Dict[str, Any],
                                  risk_models: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evalúa riesgo de un portafolio completo
        """
        try:
            portfolio_id = portfolio_data.get("portfolio_id")
            print(f"Evaluando riesgo de portafolio {portfolio_id}")
            
            # Componentes del riesgo de portafolio
            risk_components = {
                "concentration_risk": await self._assess_concentration_risk(portfolio_data),
                "market_risk": await self._assess_market_risk(portfolio_data),
                "liquidity_risk": await self._assess_liquidity_risk(portfolio_data),
                "credit_risk": await self._assess_portfolio_credit_risk(portfolio_data),
                "operational_risk": await self._assess_operational_risk(portfolio_data)
            }
            
            # Calcular métricas de riesgo
            var_95 = await self._calculate_value_at_risk(portfolio_data, confidence=0.95)
            expected_shortfall = await self._calculate_expected_shortfall(portfolio_data, var_95)
            
            # Stress testing
            stress_test_results = await self._run_stress_tests(portfolio_data)
            
            # Diversificación
            diversification_metrics = self._calculate_diversification_metrics(portfolio_data)
            
            # Score de riesgo del portafolio
            portfolio_risk_score = self._calculate_portfolio_risk_score(risk_components)
            
            assessment = {
                "portfolio_id": portfolio_id,
                "assessment_date": datetime.now().isoformat(),
                "overall_risk_score": portfolio_risk_score,
                "risk_level": self._determine_portfolio_risk_level(portfolio_risk_score),
                "risk_components": risk_components,
                "var_95": var_95,
                "expected_shortfall": expected_shortfall,
                "stress_test_results": stress_test_results,
                "diversification_metrics": diversification_metrics,
                "risk_concentration_areas": self._identify_risk_concentrations(portfolio_data),
                "recommendations": self._generate_portfolio_recommendations(risk_components),
                "next_review_date": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            return assessment
            
        except Exception as e:
            raise Exception(f"Error evaluando riesgo de portafolio: {str(e)}")
    
    async def generate_risk_dashboard(self,
                                    entity_type: str,  # customer, portfolio, institution
                                    entity_id: str,
                                    time_period: str = "30d") -> Dict[str, Any]:
        """
        Genera dashboard de riesgo con métricas en tiempo real
        """
        try:
            end_date = datetime.now()
            if time_period == "7d":
                start_date = end_date - timedelta(days=7)
            elif time_period == "30d":
                start_date = end_date - timedelta(days=30)
            elif time_period == "90d":
                start_date = end_date - timedelta(days=90)
            else:
                start_date = end_date - timedelta(days=30)
            
            # Métricas de riesgo
            risk_metrics = await self._calculate_risk_metrics(entity_id, start_date, end_date)
            
            # Tendencias de riesgo
            risk_trends = await self._analyze_risk_trends(entity_id, start_date, end_date)
            
            # Top factores de riesgo
            top_risk_factors = await self._identify_top_risk_factors(entity_id, start_date, end_date)
            
            # Alertas activas
            active_alerts = await self._get_active_alerts(entity_id)
            
            # Comparación con benchmarks
            benchmark_comparison = await self._compare_with_benchmarks(entity_id, risk_metrics)
            
            dashboard = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "time_period": time_period,
                "generated_at": datetime.now().isoformat(),
                "summary": {
                    "overall_risk_level": risk_metrics.get("overall_level", "medium"),
                    "risk_score": risk_metrics.get("overall_score", 0.5),
                    "trend": risk_trends.get("trend_direction", "stable"),
                    "active_alerts_count": len(active_alerts)
                },
                "risk_metrics": risk_metrics,
                "risk_trends": risk_trends,
                "top_risk_factors": top_risk_factors,
                "active_alerts": active_alerts,
                "benchmark_comparison": benchmark_comparison,
                "recommendations": await self._generate_dashboard_recommendations(risk_metrics, risk_trends)
            }
            
            return dashboard
            
        except Exception as e:
            raise Exception(f"Error generando dashboard de riesgo: {str(e)}")
    
    async def run_continuous_monitoring(self,
                                      monitoring_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta monitoreo continuo de riesgos
        """
        monitoring_id = self._generate_monitoring_id()
        
        try:
            print(f"Iniciando monitoreo continuo {monitoring_id}")
            
            # Configurar monitoreo por tipo de entidad
            entity_configs = monitoring_config.get("entities", {})
            
            monitoring_results = {}
            
            for entity_type, entities in entity_configs.items():
                entity_results = []
                
                for entity_id in entities:
                    try:
                        # Obtener evaluación de riesgo actual
                        current_assessment = await self._get_current_risk_assessment(entity_type, entity_id)
                        
                        # Comparar con evaluación anterior
                        trend_analysis = await self._analyze_risk_trend(entity_id)
                        
                        # Verificar umbrales
                        threshold_breaches = await self._check_threshold_breaches(entity_type, entity_id, current_assessment)
                        
                        # Detectar anomalías
                        anomalies = await self._detect_risk_anomalies(entity_id, current_assessment)
                        
                        result = {
                            "entity_id": entity_id,
                            "entity_type": entity_type,
                            "current_assessment": current_assessment,
                            "trend_analysis": trend_analysis,
                            "threshold_breaches": threshold_breaches,
                            "anomalies": anomalies,
                            "monitoring_timestamp": datetime.now().isoformat()
                        }
                        
                        entity_results.append(result)
                        
                        # Generar alertas si es necesario
                        if threshold_breaches or anomalies:
                            await self._generate_monitoring_alerts(result)
                        
                    except Exception as e:
                        print(f"Error monitoreando entidad {entity_id}: {str(e)}")
                        entity_results.append({
                            "entity_id": entity_id,
                            "entity_type": entity_type,
                            "error": str(e),
                            "monitoring_timestamp": datetime.now().isoformat()
                        })
                
                monitoring_results[entity_type] = entity_results
            
            # Generar reporte de monitoreo
            monitoring_summary = {
                "monitoring_id": monitoring_id,
                "monitoring_period": {
                    "start": datetime.now().isoformat(),
                    "end": datetime.now().isoformat()
                },
                "entities_monitored": sum(len(entities) for entities in entity_configs.values()),
                "alerts_generated": len([r for r in monitoring_results.values() 
                                       if any(r.get("threshold_breaches", []) or r.get("anomalies", []))]),
                "summary_by_entity_type": self._generate_monitoring_summary(monitoring_results),
                "recommendations": self._generate_monitoring_recommendations(monitoring_results)
            }
            
            return monitoring_summary
            
        except Exception as e:
            raise Exception(f"Error en monitoreo continuo: {str(e)}")
    
    # Métodos privados de implementación
    
    def _initialize_risk_models(self) -> Dict[str, Any]:
        """Inicializa modelos de riesgo"""
        return {
            "credit_scoring": {
                "type": "linear_combination",
                "factors": ["credit_score", "debt_to_income", "payment_history"],
                "weights": {"credit_score": 0.4, "debt_to_income": 0.3, "payment_history": 0.3}
            },
            "transaction_scoring": {
                "type": "weighted_average",
                "factors": ["merchant", "location", "amount", "time", "device", "behavior"],
                "weights": {"merchant": 0.15, "location": 0.15, "amount": 0.25, 
                           "time": 0.10, "device": 0.15, "behavior": 0.20}
            },
            "portfolio_risk": {
                "type": "monte_carlo",
                "confidence_levels": [0.95, 0.99],
                "time_horizons": [1, 5, 10]
            }
        }
    
    def _calculate_weighted_score(self, factors: List[RiskFactor]) -> float:
        """Calcula score ponderado de factores de riesgo"""
        if not factors:
            return 0.0
        
        total_weight = sum(factor.weight for factor in factors)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(
            factor.current_value * factor.weight / total_weight
            for factor in factors
        )
        
        return weighted_sum
    
    def _determine_risk_level(self, score: float, category: str) -> str:
        """Determina nivel de riesgo basado en score"""
        if category == "credit":
            if score >= 0.8:
                return "low"
            elif score >= 0.6:
                return "medium"
            elif score >= 0.4:
                return "high"
            else:
                return "critical"
        else:
            # Lógica genérica para otros tipos
            if score >= 0.7:
                return "low"
            elif score >= 0.5:
                return "medium"
            elif score >= 0.3:
                return "high"
            else:
                return "critical"
    
    def _generate_credit_recommendations(self, factors: List[RiskFactor], risk_level: str) -> List[str]:
        """Genera recomendaciones para riesgo crediticio"""
        recommendations = []
        
        if risk_level in ["high", "critical"]:
            recommendations.append("Requerir garantías adicionales")
            recommendations.append("Reducir límite de crédito")
            recommendations.append("Aumentar monitoreo de pagos")
        
        # Recomendaciones específicas por factor
        for factor in factors:
            if factor.current_value < 0.5:  # Score bajo
                if factor.factor_id == "credit_score":
                    recommendations.append("Implementar programa de mejora crediticia")
                elif factor.factor_id == "debt_to_income":
                    recommendations.append("Establecer plan de consolidación de deuda")
                elif factor.factor_id == "payment_history":
                    recommendations.append("Establecer recordatorios de pago automáticos")
        
        if not recommendations:
            recommendations.append("Mantener monitoreo regular")
            recommendations.append("Considerar ofertas de crédito adicionales")
        
        return recommendations
    
    def _generate_assessment_id(self) -> str:
        """Genera ID único de evaluación"""
        import uuid
        timestamp = int(datetime.now().timestamp() * 1000000)
        return f"risk_assessment_{timestamp}_{str(uuid.uuid4())[:8]}"
    
    async def _check_risk_alerts(self, assessment: RiskAssessment) -> None:
        """Verifica si se deben generar alertas de riesgo"""
        for factor in assessment.factors:
            if factor.current_value < factor.threshold_values["high"]:
                alert = RiskAlert(
                    alert_id=str(uuid.uuid4()),
                    alert_type="threshold_breach",
                    severity="medium" if factor.current_value > factor.threshold_values["critical"] else "high",
                    entity_id=assessment.entity_id,
                    risk_factors_affected=[factor.factor_id],
                    triggered_value=factor.current_value,
                    threshold_value=factor.threshold_values["high"],
                    description=f"Factor {factor.factor_name} por debajo del umbral",
                    recommended_actions=assessment.recommendations,
                    generated_at=datetime.now()
                )
                
                self.alert_history.append(alert)
    
    # Métodos de evaluación de transacciones
    async def _assess_merchant_risk(self, merchant_id: str, merchant_category: str) -> float:
        """Evalúa riesgo del merchant"""
        if not merchant_id or not merchant_category:
            return 0.5  # Score neutral
        
        # Scores base por categoría de merchant
        category_scores = {
            "grocery": 0.1,  # Bajo riesgo
            "gas_station": 0.2,
            "retail": 0.3,
            "restaurant": 0.4,
            "entertainment": 0.5,
            "travel": 0.6,
            "luxury": 0.7,
            "gambling": 0.9,
            "cryptocurrency": 0.8,
            "adult": 0.9
        }
        
        base_score = category_scores.get(merchant_category.lower(), 0.5)
        
        # Ajustes por historial del merchant (simulado)
        import random
        adjustment = random.uniform(-0.2, 0.2)
        
        return max(0.0, min(1.0, base_score + adjustment))
    
    async def _assess_location_risk(self, location: str, merchant_country: str) -> float:
        """Evalúa riesgo por ubicación"""
        if not location or not merchant_country:
            return 0.5
        
        # Scores por país
        country_scores = {
            "US": 0.1, "CA": 0.1, "GB": 0.2, "DE": 0.2, "FR": 0.2,
            "MX": 0.3, "BR": 0.4, "RU": 0.7, "CN": 0.6, "IN": 0.5
        }
        
        base_score = country_scores.get(merchant_country.upper(), 0.5)
        
        # Ajustes por tipo de ubicación
        location_type_risk = {
            "residential": 0.1,
            "commercial": 0.3,
            "mixed_use": 0.4,
            "high_traffic": 0.5,
            "remote": 0.6
        }
        
        # Análisis de coordenadas (simulado)
        location_adjustment = 0.0
        
        return max(0.0, min(1.0, base_score + location_adjustment))
    
    async def _assess_amount_risk(self, amount: float, customer_id: str) -> float:
        """Evalúa riesgo por monto de transacción"""
        if amount <= 0:
            return 0.5
        
        # Análisis por percentiles típicos de gasto
        if amount < 10:
            return 0.1  # Muy bajo riesgo
        elif amount < 50:
            return 0.2  # Bajo riesgo
        elif amount < 200:
            return 0.4  # Riesgo medio
        elif amount < 1000:
            return 0.6  # Riesgo medio-alto
        elif amount < 5000:
            return 0.8  # Alto riesgo
        else:
            return 0.9  # Muy alto riesgo
    
    async def _assess_time_risk(self, timestamp: str, customer_id: str) -> float:
        """Evalúa riesgo por hora de transacción"""
        if not timestamp:
            return 0.5
        
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        hour = dt.hour
        
        # Riesgo por horario
        if 6 <= hour <= 22:  # Horario normal
            return 0.2
        elif 22 <= hour <= 24 or 0 <= hour <= 6:  # Madrugada
            return 0.7
        else:
            return 0.5
    
    async def _assess_device_risk(self, device_fingerprint: str, ip_address: str) -> float:
        """Evalúa riesgo por dispositivo"""
        risk_score = 0.3  # Score base
        
        if device_fingerprint:
            # Análisis de dispositivo conocido vs nuevo
            risk_score += 0.1  # Dispositivo conocido
        
        if ip_address:
            # Análisis de IP (simulado)
            if self._is_private_ip(ip_address):
                risk_score -= 0.1
            else:
                risk_score += 0.2
        
        return max(0.0, min(1.0, risk_score))
    
    async def _assess_behavior_risk(self, transaction_data: Dict[str, Any], customer_id: str) -> float:
        """Evalúa riesgo por comportamiento de usuario"""
        # Análisis de patrones de comportamiento
        risk_factors = {
            "frequency_anomaly": 0.2,
            "amount_deviation": 0.2,
            "location_anomaly": 0.2,
            "time_anomaly": 0.2,
            "merchant_anomaly": 0.2
        }
        
        # Simular análisis de comportamiento
        import random
        for factor in risk_factors:
            risk_factors[factor] = random.uniform(0.1, 0.8)
        
        # Calcular score promedio ponderado
        behavior_score = sum(risk_factors.values()) / len(risk_factors)
        
        return behavior_score
    
    def _is_private_ip(self, ip: str) -> bool:
        """Verifica si IP es privada"""
        if not ip:
            return False
        
        # Rangos de IP privada
        private_ranges = [
            "192.168.",
            "10.",
            "172.16.",
            "172.17.",
            "172.18.",
            "172.19.",
            "172.20.",
            "172.21.",
            "172.22.",
            "172.23.",
            "172.24.",
            "172.25.",
            "172.26.",
            "172.27.",
            "172.28.",
            "172.29.",
            "172.30.",
            "172.31."
        ]
        
        return any(ip.startswith(range_ip) for range_ip in private_ranges)
    
    def _identify_risk_flags(self, scores: Dict[str, float]) -> List[str]:
        """Identifica flags de riesgo basados en scores"""
        flags = []
        
        if scores.get("overall_score", 0) > 0.8:
            flags.append("HIGH_OVERALL_RISK")
        
        if scores.get("merchant_score", 0) > 0.7:
            flags.append("HIGH_MERCHANT_RISK")
        
        if scores.get("location_score", 0) > 0.7:
            flags.append("HIGH_LOCATION_RISK")
        
        if scores.get("amount_score", 0) > 0.8:
            flags.append("HIGH_AMOUNT_RISK")
        
        if scores.get("device_score", 0) > 0.7:
            flags.append("SUSPICIOUS_DEVICE")
        
        if scores.get("behavior_score", 0) > 0.8:
            flags.append("UNUSUAL_BEHAVIOR")
        
        if scores.get("time_score", 0) > 0.7:
            flags.append("UNUSUAL_TIME")
        
        return flags
    
    async def _generate_transaction_alert(self, profile: TransactionRiskProfile) -> None:
        """Genera alerta para transacción de alto riesgo"""
        alert = RiskAlert(
            alert_id=str(uuid.uuid4()),
            alert_type="high_risk_transaction",
            severity="high" if profile.overall_risk_score > 0.9 else "medium",
            entity_id=profile.transaction_id,
            risk_factors_affected=profile.flags,
            triggered_value=profile.overall_risk_score,
            threshold_value=0.7,
            description=f"Transacción con score de riesgo alto: {profile.overall_risk_score:.3f}",
            recommended_actions=[
                "Revisar transacción manualmente",
                "Solicitar verificación adicional",
                "Considerar bloquear transacción"
            ],
            generated_at=datetime.now()
        )
        
        self.alert_history.append(alert)
    
    # Métodos de evaluación de portafolio
    async def _assess_concentration_risk(self, portfolio_data: Dict[str, Any]) -> float:
        """Evalúa riesgo de concentración"""
        # Análisis de diversificación
        holdings = portfolio_data.get("holdings", [])
        
        if not holdings:
            return 1.0  # Máximo riesgo si no hay holdings
        
        # Calcular concentración usando índice Herfindahl
        total_value = sum(holding.get("value", 0) for holding in holdings)
        
        if total_value == 0:
            return 1.0
        
        herfindahl_index = sum(
            (holding.get("value", 0) / total_value) ** 2
            for holding in holdings
        )
        
        # Normalizar a score de riesgo (mayor concentración = mayor riesgo)
        return herfindahl_index
    
    async def _assess_market_risk(self, portfolio_data: Dict[str, Any]) -> float:
        """Evalúa riesgo de mercado"""
        # Simulación de análisis de riesgo de mercado
        holdings = portfolio_data.get("holdings", [])
        
        if not holdings:
            return 0.5
        
        # Calcular exposición por clase de activo
        asset_classes = {}
        total_value = 0
        
        for holding in holdings:
            asset_class = holding.get("asset_class", "unknown")
            value = holding.get("value", 0)
            asset_classes[asset_class] = asset_classes.get(asset_class, 0) + value
            total_value += value
        
        # Volatilidad promedio ponderada
        volatilities = {
            "stocks": 0.25,
            "bonds": 0.05,
            "commodities": 0.35,
            "crypto": 0.50,
            "cash": 0.01
        }
        
        weighted_volatility = sum(
            (value / total_value) * volatilities.get(asset_class, 0.15)
            for asset_class, value in asset_classes.items()
        )
        
        return weighted_volatility
    
    async def _assess_liquidity_risk(self, portfolio_data: Dict[str, Any]) -> float:
        """Evalúa riesgo de liquidez"""
        holdings = portfolio_data.get("holdings", [])
        
        if not holdings:
            return 0.5
        
        # Calcular liquidez promedio ponderada
        liquidity_scores = {
            "stocks_large_cap": 0.9,
            "stocks_mid_cap": 0.7,
            "stocks_small_cap": 0.4,
            "bonds_investment_grade": 0.8,
            "bonds_high_yield": 0.5,
            "commodities": 0.3,
            "crypto": 0.6,
            "real_estate": 0.2,
            "cash": 1.0
        }
        
        total_value = sum(holding.get("value", 0) for holding in holdings)
        
        if total_value == 0:
            return 0.5
        
        weighted_liquidity = sum(
            (holding.get("value", 0) / total_value) * liquidity_scores.get(
                holding.get("liquidity_category", "unknown"), 0.5
            )
            for holding in holdings
        )
        
        # Invertir para obtener score de riesgo
        return 1.0 - weighted_liquidity
    
    async def _assess_portfolio_credit_risk(self, portfolio_data: Dict[str, Any]) -> float:
        """Evalúa riesgo crediticio del portafolio"""
        holdings = portfolio_data.get("holdings", [])
        
        if not holdings:
            return 0.5
        
        # Calcular score crediticio promedio ponderado
        credit_scores = {
            "AAA": 0.01,
            "AA": 0.02,
            "A": 0.05,
            "BBB": 0.1,
            "BB": 0.2,
            "B": 0.3,
            "CCC": 0.5,
            "unrated": 0.4
        }
        
        total_value = sum(holding.get("value", 0) for holding in holdings)
        
        if total_value == 0:
            return 0.5
        
        weighted_credit_risk = sum(
            (holding.get("value", 0) / total_value) * credit_scores.get(
                holding.get("credit_rating", "unrated"), 0.4
            )
            for holding in holdings
        )
        
        return weighted_credit_risk
    
    async def _assess_operational_risk(self, portfolio_data: Dict[str, Any]) -> float:
        """Evalúa riesgo operacional"""
        # Factores de riesgo operacional
        factors = {
            "counterparty_risk": 0.3,
            "technology_risk": 0.2,
            "regulatory_risk": 0.2,
            "process_risk": 0.15,
            "people_risk": 0.15
        }
        
        # Calcular score promedio (simulado)
        operational_scores = {}
        for factor, weight in factors.items():
            # Simular score para cada factor
            import random
            operational_scores[factor] = random.uniform(0.1, 0.6)
        
        weighted_operational_risk = sum(
            score * factors[factor]
            for factor, score in operational_scores.items()
        )
        
        return weighted_operational_risk
    
    async def _calculate_value_at_risk(self, portfolio_data: Dict[str, Any], confidence: float) -> float:
        """Calcula Value at Risk (VaR)"""
        # Simulación de cálculo VaR usando método histórico
        holdings = portfolio_data.get("holdings", [])
        total_value = sum(holding.get("value", 0) for holding in holdings)
        
        if total_value == 0:
            return 0.0
        
        # Simular retornos históricos
        import random
        returns = [random.normalvariate(-0.02, 0.15) for _ in range(252)]  # 1 año de datos
        
        # Calcular VaR
        returns_sorted = sorted(returns)
        var_index = int((1 - confidence) * len(returns_sorted))
        var = abs(returns_sorted[var_index] * total_value)
        
        return var
    
    async def _calculate_expected_shortfall(self, portfolio_data: Dict[str, Any], var: float) -> float:
        """Calcula Expected Shortfall (ES)"""
        # Simulación de Expected Shortfall
        # ES es típicamente 1.5-2 veces el VaR
        return var * 1.7
    
    async def _run_stress_tests(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta stress tests en el portafolio"""
        scenarios = {
            "market_crash_2008": -0.35,
            "covid_pandemic": -0.25,
            "interest_rate_shock": -0.15,
            "credit_crisis": -0.20,
            "geopolitical_crisis": -0.18
        }
        
        total_value = sum(
            holding.get("value", 0) 
            for holding in portfolio_data.get("holdings", [])
        )
        
        stress_results = {}
        for scenario, shock in scenarios.items():
            stress_value = total_value * shock
            stress_results[scenario] = {
                "shock_percentage": shock,
                "loss_amount": abs(stress_value),
                "loss_percentage": abs(shock),
                "risk_level": "critical" if shock < -0.3 else "high" if shock < -0.2 else "medium"
            }
        
        return stress_results
    
    def _calculate_diversification_metrics(self, portfolio_data: Dict[str, Any]) -> Dict[str, float]:
        """Calcula métricas de diversificación"""
        holdings = portfolio_data.get("holdings", [])
        
        if not holdings:
            return {"diversification_ratio": 0.0, "effective_positions": 1.0}
        
        # Calcular número efectivo de posiciones
        total_value = sum(holding.get("value", 0) for holding in holdings)
        
        if total_value == 0:
            return {"diversification_ratio": 0.0, "effective_positions": 1.0}
        
        # Índice Herfindahl-Hirschman para concentración
        hhi = sum(
            (holding.get("value", 0) / total_value) ** 2
            for holding in holdings
        )
        
        effective_positions = 1 / hhi if hhi > 0 else 1.0
        
        # Ratio de diversificación (relación entre diversificación teórica y actual)
        diversification_ratio = effective_positions / len(holdings)
        
        return {
            "diversification_ratio": diversification_ratio,
            "effective_positions": effective_positions,
            "concentration_index": hhi,
            "max_single_position": max(
                holding.get("value", 0) / total_value
                for holding in holdings
            ) if holdings else 0.0
        }
    
    def _calculate_portfolio_risk_score(self, risk_components: Dict[str, float]) -> float:
        """Calcula score de riesgo del portafolio"""
        # Pesos para componentes de riesgo
        weights = {
            "concentration_risk": 0.2,
            "market_risk": 0.3,
            "liquidity_risk": 0.2,
            "credit_risk": 0.2,
            "operational_risk": 0.1
        }
        
        portfolio_score = sum(
            risk_components[component] * weights[component]
            for component in weights.keys()
            if component in risk_components
        )
        
        return portfolio_score
    
    def _determine_portfolio_risk_level(self, score: float) -> str:
        """Determina nivel de riesgo del portafolio"""
        if score < 0.2:
            return "low"
        elif score < 0.4:
            return "medium"
        elif score < 0.6:
            return "high"
        else:
            return "critical"
    
    def _identify_risk_concentrations(self, portfolio_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identifica concentraciones de riesgo"""
        concentrations = []
        holdings = portfolio_data.get("holdings", [])
        
        if not holdings:
            return concentrations
        
        total_value = sum(holding.get("value", 0) for holding in holdings)
        
        # Identificar posiciones grandes
        large_positions = [
            {
                "holding": holding,
                "percentage": (holding.get("value", 0) / total_value * 100) if total_value > 0 else 0,
                "concentration_type": "single_position"
            }
            for holding in holdings
            if holding.get("value", 0) / total_value > 0.1 if total_value > 0 else False
        ]
        
        concentrations.extend(large_positions)
        
        # Análisis por categoría
        categories = {}
        for holding in holdings:
            category = holding.get("asset_class", "unknown")
            categories[category] = categories.get(category, 0) + holding.get("value", 0)
        
        category_concentrations = [
            {
                "category": category,
                "total_value": value,
                "percentage": (value / total_value * 100) if total_value > 0 else 0,
                "concentration_type": "asset_class"
            }
            for category, value in categories.items()
            if value / total_value > 0.3 if total_value > 0 else False
        ]
        
        concentrations.extend(category_concentrations)
        
        return concentrations
    
    def _generate_portfolio_recommendations(self, risk_components: Dict[str, float]) -> List[str]:
        """Genera recomendaciones para portafolio"""
        recommendations = []
        
        if risk_components.get("concentration_risk", 0) > 0.5:
            recommendations.append("Diversificar el portafolio para reducir concentración de riesgo")
        
        if risk_components.get("liquidity_risk", 0) > 0.4:
            recommendations.append("Aumentar proporción de activos líquidos")
        
        if risk_components.get("market_risk", 0) > 0.3:
            recommendations.append("Considerar hedging contra riesgo de mercado")
        
        if risk_components.get("credit_risk", 0) > 0.3:
            recommendations.append("Revisar calificaciones crediticias de holdings")
        
        recommendations.append("Implementar monitoreo continuo de riesgos")
        
        return recommendations
    
    # Métodos para dashboard y monitoreo
    def _generate_monitoring_id(self) -> str:
        """Genera ID único de monitoreo"""
        import uuid
        timestamp = int(datetime.now().timestamp() * 1000000)
        return f"monitoring_{timestamp}_{str(uuid.uuid4())[:8]}"
    
    # Métodos adicionales para completar funcionalidad
    async def _calculate_risk_metrics(self, entity_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Calcula métricas de riesgo para dashboard"""
        # Simulación de métricas
        return {
            "overall_score": 0.45,
            "overall_level": "medium",
            "credit_risk": 0.3,
            "operational_risk": 0.5,
            "market_risk": 0.4,
            "liquidity_risk": 0.6,
            "trend_direction": "improving"
        }
    
    async def _analyze_risk_trends(self, entity_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analiza tendencias de riesgo"""
        return {
            "trend_direction": "stable",
            "trend_strength": 0.6,
            "key_changes": [
                {"factor": "credit_score", "change": "improved", "magnitude": 0.1},
                {"factor": "operational_risk", "change": "increased", "magnitude": 0.05}
            ]
        }
    
    async def _identify_top_risk_factors(self, entity_id: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Identifica principales factores de riesgo"""
        return [
            {"factor": "liquidity_risk", "score": 0.6, "impact": "high"},
            {"factor": "operational_risk", "score": 0.5, "impact": "medium"},
            {"factor": "market_risk", "score": 0.4, "impact": "medium"}
        ]
    
    async def _get_active_alerts(self, entity_id: str) -> List[Dict[str, Any]]:
        """Obtiene alertas activas"""
        return [
            {
                "alert_id": "alert_1",
                "type": "threshold_breach",
                "severity": "medium",
                "description": "Riesgo de liquidez por encima del umbral",
                "generated_at": datetime.now().isoformat()
            }
        ]
    
    async def _compare_with_benchmarks(self, entity_id: str, risk_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compara con benchmarks de la industria"""
        return {
            "overall_percentile": 45,
            "peer_group_comparison": "below_average",
            "industry_average": 0.50,
            "top_quartile": 0.25,
            "bottom_quartile": 0.75
        }
    
    async def _generate_dashboard_recommendations(self, risk_metrics: Dict[str, Any], risk_trends: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones para dashboard"""
        recommendations = [
            "Revisar métricas de liquidez mensualmente",
            "Implementar hedging para riesgo de mercado"
        ]
        
        if risk_trends.get("trend_direction") == "deteriorating":
            recommendations.append("Acción inmediata requerida para mejorar controles de riesgo")
        
        return recommendations
    
    async def _get_current_risk_assessment(self, entity_type: str, entity_id: str) -> Dict[str, Any]:
        """Obtiene evaluación actual de riesgo"""
        return {
            "assessment_id": "current_assessment",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "overall_score": 0.45,
            "risk_level": "medium",
            "last_updated": datetime.now().isoformat()
        }
    
    async def _analyze_risk_trend(self, entity_id: str) -> Dict[str, Any]:
        """Analiza tendencia de riesgo"""
        return {
            "trend_direction": "stable",
            "change_magnitude": 0.02,
            "time_period": "30_days"
        }
    
    async def _check_threshold_breaches(self, entity_type: str, entity_id: str, assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verifica violaciones de umbrales"""
        breaches = []
        
        # Simular verificación de umbrales
        if assessment.get("overall_score", 0) > 0.7:
            breaches.append({
                "threshold_type": "overall_risk_score",
                "current_value": assessment["overall_score"],
                "threshold_value": 0.7,
                "severity": "high"
            })
        
        return breaches
    
    async def _detect_risk_anomalies(self, entity_id: str, assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detecta anomalías en patrones de riesgo"""
        anomalies = []
        
        # Simular detección de anomalías
        import random
        if random.random() < 0.1:  # 10% probabilidad de anomalía
            anomalies.append({
                "anomaly_type": "sudden_increase",
                "description": "Aumento súbito en score de riesgo operacional",
                "severity": "medium",
                "detected_at": datetime.now().isoformat()
            })
        
        return anomalies
    
    async def _generate_monitoring_alerts(self, monitoring_result: Dict[str, Any]) -> None:
        """Genera alertas de monitoreo"""
        # Implementar generación de alertas
        print(f"Generando alertas para {monitoring_result['entity_id']}")
    
    def _generate_monitoring_summary(self, monitoring_results: Dict[str, Any]) -> Dict[str, str]:
        """Genera resumen de monitoreo por tipo de entidad"""
        summary = {}
        
        for entity_type, results in monitoring_results.items():
            successful_assessments = sum(1 for r in results if "error" not in r)
            total_assessments = len(results)
            
            summary[entity_type] = {
                "success_rate": f"{(successful_assessments / total_assessments * 100):.1f}%" if total_assessments > 0 else "0%",
                "assessments_completed": successful_assessments,
                "total_assessments": total_assessments
            }
        
        return summary
    
    def _generate_monitoring_recommendations(self, monitoring_results: Dict[str, Any]) -> List[str]:
        """Genera recomendaciones de monitoreo"""
        recommendations = [
            "Continuar monitoreo continuo de todas las entidades",
            "Revisar y ajustar umbrales de alerta regularmente"
        ]
        
        total_entities = sum(len(results) for results in monitoring_results.values())
        if total_entities > 100:
            recommendations.append("Considerar escalado de infraestructura de monitoreo")
        
        return recommendations
