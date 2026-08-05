"""
Analytics Agent MCP - Agente de Analíticas
Proporciona análisis de datos financieros, generación de reportes,
seguimiento de KPIs y analíticas predictivas empresariales.

Autor: Analytics Agent
Versión: 1.0.0
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import random
import math
from statistics import mean, median, stdev

# Importar la estructura base del agente MCP
try:
    from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
except ImportError:
    BaseAgentWrapper = object
    AgentCapability = None


class AnalyticsType(Enum):
    """Tipos de análisis disponibles"""
    FINANCIAL = "financial"
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONAL = "operational"
    CUSTOMER = "customer"
    PREDICTIVE = "predictive"


class TimeSeriesPeriod(Enum):
    """Períodos para series temporales"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class MetricType(Enum):
    """Tipos de métricas"""
    REVENUE = "revenue"
    COST = "cost"
    PROFIT = "profit"
    ROI = "roi"
    NPS = "nps"
    CHURN_RATE = "churn_rate"
    CAC = "cac"
    LTV = "ltv"
    CONVERSION_RATE = "conversion_rate"
    CUSTOMER_SATISFACTION = "customer_satisfaction"


@dataclass
class KPI:
    """Estructura de datos para KPIs"""
    name: str
    value: float
    unit: str
    target: Optional[float] = None
    previous_value: Optional[float] = None
    change_percentage: Optional[float] = None
    trend: str = "stable"  # up, down, stable
    period: str = "current"
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class FinancialMetric:
    """Estructura de datos para métricas financieras"""
    revenue: float = 0.0
    costs: float = 0.0
    profit: float = 0.0
    gross_margin: float = 0.0
    net_margin: float = 0.0
    roi: float = 0.0
    cash_flow: float = 0.0
    burn_rate: float = 0.0
    runway_months: float = 0.0


@dataclass
class Report:
    """Estructura de datos para reportes"""
    id: str
    title: str
    report_type: AnalyticsType
    date_range: Tuple[datetime, datetime]
    kpis: List[KPI] = field(default_factory=list)
    metrics: List[Dict[str, Any]] = field(default_factory=list)
    charts_data: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class AnalyticsResponse:
    """Respuesta consolidada de analíticas"""
    success: bool
    report_id: str
    action: str
    timestamp: float
    execution_time: float
    analytics_type: AnalyticsType
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class AnalyticsAgent(BaseAgentWrapper if BaseAgentWrapper else object):
    """
    Agente de Analíticas que proporciona análisis financiero,
    seguimiento de KPIs y reportes empresariales.
    """
    
    def __init__(self):
        if BaseAgentWrapper:
            super().__init__(
                agent_name="AnalyticsAgent",
                capabilities=[
                    AgentCapability.FINANCIAL_ANALYTICS if AgentCapability else "financial_analytics",
                    AgentCapability.DATA_ANALYSIS if AgentCapability else "data_analysis",
                    AgentCapability.REPORT_GENERATION if AgentCapability else "report_generation",
                    AgentCapability.KPI_TRACKING if AgentCapability else "kpi_tracking",
                    AgentCapability.PREDICTIVE_ANALYTICS if AgentCapability else "predictive_analytics",
                ],
                max_concurrent=4,
                timeout_seconds=90,
                retry_attempts=2
            )
        
        self.logger = logging.getLogger(__name__)
        self._kpis: Dict[str, KPI] = {}
        self._reports: Dict[str, Report] = {}
        self._financial_data: Dict[str, List[Dict[str, Any]]] = {}
        self._dashboards: Dict[str, Dict[str, Any]] = {}
        
        # Configuración de alertas
        self.alert_thresholds = {
            "revenue_decline": -0.1,  # Alerta si ingresos caen más del 10%
            "cost_increase": 0.15,    # Alerta si costos aumentan más del 15%
            "profit_margin": 0.05     # Alerta si margen de ganancia es menor al 5%
        }
        
        # Cargar datos de ejemplo
        self._load_sample_data()
    
    async def _initialize(self):
        """Inicialización específica del agente"""
        await asyncio.sleep(0.1)
        self.logger.info("Analytics Agent inicializado")
    
    def _load_sample_data(self):
        """Cargar datos de ejemplo"""
        # KPIs de ejemplo
        sample_kpis = [
            KPI("Ingresos Mensuales", 125000.0, "€", target=150000.0, previous_value=118000.0),
            KPI("Margen de Ganancia", 0.25, "%", target=0.30, previous_value=0.22),
            KPI("ROI", 0.18, "%", target=0.20, previous_value=0.15),
            KPI("NPS", 72, "puntos", target=75, previous_value=68),
            KPI("Tasa de Conversión", 0.035, "%", target=0.040, previous_value=0.032),
            KPI("CAC", 45.0, "€", target=40.0, previous_value=48.0),
            KPI("LTV", 890.0, "€", target=1000.0, previous_value=850.0),
            KPI("Tasa de Churn", 0.045, "%", target=0.030, previous_value=0.050),
        ]
        
        for kpi in sample_kpis:
            # Calcular cambio porcentual
            if kpi.previous_value:
                kpi.change_percentage = ((kpi.value - kpi.previous_value) / kpi.previous_value) * 100
                kpi.trend = "up" if kpi.change_percentage > 0 else "down" if kpi.change_percentage < 0 else "stable"
            
            self._kpis[kpi.name] = kpi
        
        # Datos financieros históricos
        months = []
        for i in range(12):
            month_date = datetime.now() - timedelta(days=30 * (11 - i))
            months.append({
                "date": month_date,
                "revenue": random.uniform(80000, 150000),
                "costs": random.uniform(50000, 90000),
                "customers": random.randint(200, 500),
                "conversions": random.uniform(15, 45),
                "marketing_spend": random.uniform(8000, 20000)
            })
        
        self._financial_data["monthly"] = months
        
        # Dashboard de ejemplo
        self._dashboards["executive"] = {
            "title": "Dashboard Ejecutivo",
            "widgets": [
                {"type": "kpi_card", "kpi": "Ingresos Mensuales"},
                {"type": "kpi_card", "kpi": "Margen de Ganancia"},
                {"type": "chart", "chart_type": "line", "data_source": "revenue_trend"},
                {"type": "chart", "chart_type": "bar", "data_source": "costs_breakdown"}
            ]
        }
    
    async def generate_financial_report(
        self,
        date_range: Tuple[datetime, datetime],
        include_forecasts: bool = True
    ) -> AnalyticsResponse:
        """Generar reporte financiero"""
        start_time = time.time()
        
        try:
            report_id = f"report_{int(time.time() * 1000)}"
            
            # Simular análisis financiero
            await asyncio.sleep(0.5)
            
            # Calcular métricas financieras
            financial_metrics = self._calculate_financial_metrics(date_range)
            
            # Generar insights
            insights = [
                f"Los ingresos han {'aumentado' if financial_metrics.profit > 0 else 'disminuido'} un {abs(financial_metrics.profit):.1f}%",
                f"El margen bruto es del {financial_metrics.gross_margin:.1%}",
                f"La tasa de ROI es del {financial_metrics.roi:.1%}",
                f"El flujo de caja es {'positivo' if financial_metrics.cash_flow > 0 else 'negativo'}"
            ]
            
            # Generar recomendaciones
            recommendations = [
                "Considerar estrategias para reducir costos operativos",
                "Implementar nuevas campañas de marketing dirigidas",
                "Revisar la estructura de precios de productos",
                "Optimizar el proceso de conversión de leads"
            ]
            
            report = Report(
                id=report_id,
                title="Reporte Financiero Mensual",
                report_type=AnalyticsType.FINANCIAL,
                date_range=date_range,
                metrics=[financial_metrics.__dict__],
                insights=insights,
                recommendations=recommendations
            )
            
            self._reports[report_id] = report
            
            self.logger.info(f"Reporte financiero generado: {report_id}")
            
            return AnalyticsResponse(
                success=True,
                report_id=report_id,
                action="generate_financial_report",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                analytics_type=AnalyticsType.FINANCIAL,
                details={
                    "financial_metrics": financial_metrics.__dict__,
                    "insights": insights,
                    "recommendations": recommendations,
                    "date_range": {
                        "start": date_range[0].isoformat(),
                        "end": date_range[1].isoformat()
                    }
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generando reporte financiero: {str(e)}")
            return AnalyticsResponse(
                success=False,
                report_id="",
                action="generate_financial_report",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                analytics_type=AnalyticsType.FINANCIAL,
                error=str(e)
            )
    
    def _calculate_financial_metrics(self, date_range: Tuple[datetime, datetime]) -> FinancialMetric:
        """Calcular métricas financieras"""
        # Simular cálculo basado en datos históricos
        total_revenue = random.uniform(100000, 200000)
        total_costs = random.uniform(70000, 130000)
        
        profit = total_revenue - total_costs
        gross_margin = profit / total_revenue if total_revenue > 0 else 0
        net_margin = profit / total_revenue if total_revenue > 0 else 0
        roi = (profit / total_costs) if total_costs > 0 else 0
        cash_flow = random.uniform(-50000, 100000)
        burn_rate = total_costs / 12  # Simular burn rate mensual
        runway_months = cash_flow / burn_rate if burn_rate > 0 else 0
        
        return FinancialMetric(
            revenue=total_revenue,
            costs=total_costs,
            profit=profit,
            gross_margin=gross_margin,
            net_margin=net_margin,
            roi=roi,
            cash_flow=cash_flow,
            burn_rate=burn_rate,
            runway_months=max(0, runway_months)
        )
    
    async def track_kpi(
        self,
        kpi_name: str,
        value: float,
        unit: str = "",
        target: Optional[float] = None
    ) -> AnalyticsResponse:
        """Registrar nuevo valor de KPI"""
        start_time = time.time()
        
        try:
            # Obtener KPI existente o crear nuevo
            if kpi_name in self._kpis:
                kpi = self._kpis[kpi_name]
                previous_value = kpi.value
            else:
                kpi = KPI(kpi_name, value, unit, target)
                previous_value = None
            
            # Actualizar KPI
            kpi.value = value
            kpi.unit = unit
            kpi.target = target
            kpi.previous_value = previous_value
            kpi.updated_at = datetime.now()
            
            # Calcular cambio
            if previous_value:
                kpi.change_percentage = ((value - previous_value) / previous_value) * 100
                kpi.trend = "up" if kpi.change_percentage > 0 else "down" if kpi.change_percentage < 0 else "stable"
            
            self._kpis[kpi_name] = kpi
            
            # Verificar alertas
            alerts = self._check_kpi_alerts(kpi)
            
            self.logger.info(f"KPI actualizado: {kpi_name} = {value}")
            
            return AnalyticsResponse(
                success=True,
                report_id=kpi_name,
                action="track_kpi",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                analytics_type=AnalyticsType.OPERATIONAL,
                details={
                    "kpi": {
                        "name": kpi.name,
                        "value": kpi.value,
                        "unit": kpi.unit,
                        "target": kpi.target,
                        "previous_value": kpi.previous_value,
                        "change_percentage": kpi.change_percentage,
                        "trend": kpi.trend
                    },
                    "alerts": alerts
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error registrando KPI: {str(e)}")
            return AnalyticsResponse(
                success=False,
                report_id="",
                action="track_kpi",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                analytics_type=AnalyticsType.OPERATIONAL,
                error=str(e)
            )
    
    def _check_kpi_alerts(self, kpi: KPI) -> List[Dict[str, Any]]:
        """Verificar alertas de KPI"""
        alerts = []
        
        if kpi.name == "Ingresos Mensuales" and kpi.change_percentage and kpi.change_percentage < self.alert_thresholds["revenue_decline"] * 100:
            alerts.append({
                "type": "warning",
                "message": f"Ingresos han caído un {abs(kpi.change_percentage):.1f}%",
                "severity": "high"
            })
        
        if kpi.name == "Margen de Ganancia" and kpi.value < self.alert_thresholds["profit_margin"]:
            alerts.append({
                "type": "warning",
                "message": f"Margen de ganancia por debajo del umbral ({kpi.value:.1%})",
                "severity": "medium"
            })
        
        return alerts
    
    async def generate_forecast(
        self,
        metric_name: str,
        periods: int = 6,
        forecast_type: str = "linear"
    ) -> AnalyticsResponse:
        """Generar predicción de métricas"""
        start_time = time.time()
        
        try:
            # Simular análisis predictivo
            await asyncio.sleep(0.3)
            
            # Obtener datos históricos (simulados)
            historical_data = []
            base_value = 100000  # Valor base simulado
            
            for i in range(12):  # 12 períodos históricos
                trend_factor = 1 + (i * 0.02)  # Crecimiento del 2% por período
                noise = random.uniform(0.9, 1.1)  # Ruido aleatorio
                value = base_value * trend_factor * noise
                historical_data.append({
                    "period": i + 1,
                    "value": value,
                    "date": (datetime.now() - timedelta(days=30 * (11 - i))).isoformat()
                })
            
            # Generar predicciones
            forecasts = []
            last_value = historical_data[-1]["value"]
            
            for i in range(periods):
                if forecast_type == "linear":
                    # Predicción lineal simple
                    growth_rate = 0.015  # 1.5% de crecimiento por período
                    predicted_value = last_value * ((1 + growth_rate) ** (i + 1))
                else:
                    # Predicción más compleja con componente estacional
                    seasonal_factor = 1 + 0.1 * math.sin(2 * math.pi * i / 12)
                    growth_factor = 1 + (i + 1) * 0.01
                    predicted_value = last_value * seasonal_factor * growth_factor
                
                forecasts.append({
                    "period": i + 1,
                    "predicted_value": predicted_value,
                    "confidence_interval": {
                        "lower": predicted_value * 0.9,
                        "upper": predicted_value * 1.1
                    },
                    "date": (datetime.now() + timedelta(days=30 * (i + 1))).isoformat()
                })
            
            # Calcular estadísticas de precisión
            accuracy_metrics = {
                "mean_absolute_error": random.uniform(500, 2000),
                "mean_squared_error": random.uniform(100000, 500000),
                "r_squared": random.uniform(0.7, 0.95),
                "confidence_score": random.uniform(0.8, 0.95)
            }
            
            self.logger.info(f"Predicción generada para {metric_name}")
            
            return AnalyticsResponse(
                success=True,
                report_id=f"forecast_{metric_name}",
                action="generate_forecast",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                analytics_type=AnalyticsType.PREDICTIVE,
                details={
                    "metric_name": metric_name,
                    "forecast_type": forecast_type,
                    "historical_data": historical_data,
                    "forecasts": forecasts,
                    "accuracy_metrics": accuracy_metrics,
                    "forecast_horizon": periods
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error generando predicción: {str(e)}")
            return AnalyticsResponse(
                success=False,
                report_id="",
                action="generate_forecast",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                analytics_type=AnalyticsType.PREDICTIVE,
                error=str(e)
            )
    
    async def get_dashboard_data(self, dashboard_name: str) -> AnalyticsResponse:
        """Obtener datos para dashboard"""
        start_time = time.time()
        
        try:
            if dashboard_name not in self._dashboards:
                raise ValueError(f"Dashboard no encontrado: {dashboard_name}")
            
            dashboard = self._dashboards[dashboard_name]
            dashboard_data = {
                "title": dashboard["title"],
                "widgets": []
            }
            
            # Simular carga de datos para cada widget
            for widget in dashboard["widgets"]:
                widget_data = {"type": widget["type"]}
                
                if widget["type"] == "kpi_card":
                    kpi_name = widget["kpi"]
                    if kpi_name in self._kpis:
                        kpi = self._kpis[kpi_name]
                        widget_data["data"] = {
                            "name": kpi.name,
                            "value": kpi.value,
                            "unit": kpi.unit,
                            "target": kpi.target,
                            "change_percentage": kpi.change_percentage,
                            "trend": kpi.trend
                        }
                
                elif widget["type"] == "chart":
                    chart_type = widget["chart_type"]
                    data_source = widget["data_source"]
                    
                    # Simular datos de gráfico
                    if data_source == "revenue_trend":
                        widget_data["data"] = {
                            "labels": ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
                            "values": [random.uniform(80000, 120000) for _ in range(6)]
                        }
                    elif data_source == "costs_breakdown":
                        widget_data["data"] = {
                            "labels": ["Personal", "Marketing", "Operaciones", "Otros"],
                            "values": [random.uniform(30000, 50000) for _ in range(4)]
                        }
                
                dashboard_data["widgets"].append(widget_data)
            
            self.logger.info(f"Dashboard cargado: {dashboard_name}")
            
            return AnalyticsResponse(
                success=True,
                report_id=dashboard_name,
                action="get_dashboard_data",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                analytics_type=AnalyticsType.OPERATIONAL,
                details=dashboard_data
            )
            
        except Exception as e:
            self.logger.error(f"Error cargando dashboard: {str(e)}")
            return AnalyticsResponse(
                success=False,
                report_id="",
                action="get_dashboard_data",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                analytics_type=AnalyticsType.OPERATIONAL,
                error=str(e)
            )
    
    async def process_request(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesar request de analíticas
        
        Formatos soportados:
        - generate_financial_report: {"action": "generate_financial_report", "start_date": "2024-01-01", "end_date": "2024-12-31"}
        - track_kpi: {"action": "track_kpi", "kpi_name": "Ingresos", "value": 125000, "unit": "€"}
        - generate_forecast: {"action": "generate_forecast", "metric_name": "revenue", "periods": 6}
        - get_dashboard_data: {"action": "get_dashboard_data", "dashboard_name": "executive"}
        """
        try:
            await self.ensure_initialized()
            
            action = request.get("action", "").lower()
            
            if action == "generate_financial_report":
                start_date = request.get("start_date", "2024-01-01")
                end_date = request.get("end_date", "2024-12-31")
                include_forecasts = request.get("include_forecasts", True)
                
                try:
                    start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                    end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                except:
                    # Fallback para fechas simples
                    from datetime import datetime
                    try:
                        start = datetime.strptime(start_date, "%Y-%m-%d")
                        end = datetime.strptime(end_date, "%Y-%m-%d")
                    except:
                        start = datetime.now() - timedelta(days=30)
                        end = datetime.now()
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="generate_financial_report",
                        capability=AgentCapability.REPORT_GENERATION,
                        operation_func=self.generate_financial_report,
                        date_range=(start, end),
                        include_forecasts=include_forecasts
                    )
                else:
                    response = await self.generate_financial_report((start, end), include_forecasts)
                
                return {
                    "success": response.success,
                    "report_id": response.report_id if response.success else None,
                    "financial_metrics": response.details.get("financial_metrics", {}) if response.success else {},
                    "insights": response.details.get("insights", []) if response.success else [],
                    "recommendations": response.details.get("recommendations", []) if response.success else [],
                    "error": response.error
                }
            
            elif action == "track_kpi":
                kpi_name = request.get("kpi_name")
                value = request.get("value")
                unit = request.get("unit", "")
                target = request.get("target")
                
                if kpi_name is None or value is None:
                    raise ValueError("kpi_name y value son requeridos")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="track_kpi",
                        capability=AgentCapability.KPI_TRACKING,
                        operation_func=self.track_kpi,
                        kpi_name=kpi_name,
                        value=float(value),
                        unit=unit,
                        target=float(target) if target else None
                    )
                else:
                    response = await self.track_kpi(
                        kpi_name, float(value), unit, 
                        float(target) if target else None
                    )
                
                return {
                    "success": response.success,
                    "kpi": response.details.get("kpi", {}) if response.success else {},
                    "alerts": response.details.get("alerts", []) if response.success else [],
                    "error": response.error
                }
            
            elif action == "generate_forecast":
                metric_name = request.get("metric_name", "revenue")
                periods = request.get("periods", 6)
                forecast_type = request.get("forecast_type", "linear")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="generate_forecast",
                        capability=AgentCapability.PREDICTIVE_ANALYTICS,
                        operation_func=self.generate_forecast,
                        metric_name=metric_name,
                        periods=int(periods),
                        forecast_type=forecast_type
                    )
                else:
                    response = await self.generate_forecast(
                        metric_name, int(periods), forecast_type
                    )
                
                return {
                    "success": response.success,
                    "forecasts": response.details.get("forecasts", []) if response.success else [],
                    "accuracy_metrics": response.details.get("accuracy_metrics", {}) if response.success else {},
                    "forecast_horizon": response.details.get("forecast_horizon", 0) if response.success else 0,
                    "error": response.error
                }
            
            elif action == "get_dashboard_data":
                dashboard_name = request.get("dashboard_name", "executive")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="get_dashboard_data",
                        capability=AgentCapability.DATA_ANALYSIS,
                        operation_func=self.get_dashboard_data,
                        dashboard_name=dashboard_name
                    )
                else:
                    response = await self.get_dashboard_data(dashboard_name)
                
                return {
                    "success": response.success,
                    "dashboard_data": response.details if response.success else {},
                    "error": response.error
                }
            
            else:
                raise ValueError(f"Acción no soportada: {action}")
                
        except Exception as e:
            self.logger.error(f"Error procesando request de analíticas: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del agente"""
        return {
            "total_kpis": len(self._kpis),
            "total_reports": len(self._reports),
            "available_dashboards": list(self._dashboards.keys()),
            "agent_name": "AnalyticsAgent",
            "analytics_types": [atype.value for atype in AnalyticsType],
            "metric_types": [mtype.value for mtype in MetricType],
            "available_actions": [
                "generate_financial_report",
                "track_kpi",
                "generate_forecast",
                "get_dashboard_data"
            ]
        }