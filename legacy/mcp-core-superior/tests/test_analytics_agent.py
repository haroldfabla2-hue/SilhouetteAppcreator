"""
Tests unitarios para Analytics Agent
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Añadir el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.analytics_agent import (
    AnalyticsAgent, KPI, FinancialMetric, Report, AnalyticsType, MetricType
)


class TestAnalyticsAgent:
    """Tests para AnalyticsAgent"""
    
    @pytest.fixture
    async def agent(self):
        """Fixture para crear agente de prueba"""
        agent = AnalyticsAgent()
        await agent._initialize()
        return agent
    
    def test_agent_initialization(self, agent):
        """Test inicialización del agente"""
        assert agent.agent_name == "AnalyticsAgent"
        assert agent.is_ready
        assert len(agent.capabilities) > 0
        assert len(agent._kpis) > 0  # Debe cargar KPIs de ejemplo
        assert len(agent._financial_data) > 0  # Debe cargar datos financieros
    
    @pytest.mark.asyncio
    async def test_generate_financial_report(self, agent):
        """Test generación de reporte financiero"""
        fecha_inicio = datetime.now() - timedelta(days=30)
        fecha_fin = datetime.now()
        
        response = await agent.generate_financial_report(
            date_range=(fecha_inicio, fecha_fin),
            include_forecasts=True
        )
        
        assert response.success
        assert response.action == "generate_financial_report"
        assert response.analytics_type == AnalyticsType.FINANCIAL
        assert response.report_id is not None
        
        details = response.details
        assert "financial_metrics" in details
        assert "insights" in details
        assert "recommendations" in details
        
        # Verificar estructura de métricas financieras
        financial_metrics = details["financial_metrics"]
        assert "revenue" in financial_metrics
        assert "costs" in financial_metrics
        assert "profit" in financial_metrics
        assert "gross_margin" in financial_metrics
        assert "roi" in financial_metrics
    
    @pytest.mark.asyncio
    async def test_track_kpi_new(self, agent):
        """Test registrar nuevo KPI"""
        initial_count = len(agent._kpis)
        
        response = await agent.track_kpi(
            kpi_name="Test KPI",
            value=100.0,
            unit="€",
            target=120.0
        )
        
        assert response.success
        assert response.action == "track_kpi"
        assert len(agent._kpis) == initial_count + 1
        
        # Verificar que el KPI fue creado correctamente
        kpi = agent._kpis["Test KPI"]
        assert kpi.name == "Test KPI"
        assert kpi.value == 100.0
        assert kpi.unit == "€"
        assert kpi.target == 120.0
        assert kpi.previous_value is None
        assert kpi.change_percentage is None
    
    @pytest.mark.asyncio
    async def test_track_kpi_existing_update(self, agent):
        """Test actualizar KPI existente"""
        # Primero registrar un KPI
        await agent.track_kpi("Ingresos Mensuales", 100000.0, "€")
        
        # Luego actualizarlo
        response = await agent.track_kpi("Ingresos Mensuales", 110000.0, "€")
        
        assert response.success
        kpi = agent._kpis["Ingresos Mensuales"]
        assert kpi.value == 110000.0
        assert kpi.previous_value == 100000.0
        assert kpi.change_percentage == 10.0  # 10% de aumento
        assert kpi.trend == "up"
    
    @pytest.mark.asyncio
    async def test_track_kpi_with_decline(self, agent):
        """Test tracking de KPI con disminución"""
        await agent.track_kpi("Test KPI Down", 100.0, "€")
        response = await agent.track_kpi("Test KPI Down", 90.0, "€")
        
        assert response.success
        kpi = agent._kpis["Test KPI Down"]
        assert kpi.change_percentage == -10.0
        assert kpi.trend == "down"
    
    @pytest.mark.asyncio
    async def test_generate_forecast(self, agent):
        """Test generación de predicción"""
        response = await agent.generate_forecast(
            metric_name="revenue",
            periods=6,
            forecast_type="linear"
        )
        
        assert response.success
        assert response.action == "generate_forecast"
        assert response.analytics_type == AnalyticsType.PREDICTIVE
        
        details = response.details
        assert "metric_name" in details
        assert "forecasts" in details
        assert "accuracy_metrics" in details
        assert "forecast_horizon" in details
        
        # Verificar estructura de predicciones
        forecasts = details["forecasts"]
        assert len(forecasts) == 6
        
        forecast = forecasts[0]
        assert "period" in forecast
        assert "predicted_value" in forecast
        assert "confidence_interval" in forecast
        assert "date" in forecast
    
    @pytest.mark.asyncio
    async def test_generate_forecast_different_types(self, agent):
        """Test generación de predicciones con diferentes tipos"""
        forecast_types = ["linear", "seasonal"]
        
        for forecast_type in forecast_types:
            response = await agent.generate_forecast(
                metric_name="revenue",
                periods=3,
                forecast_type=forecast_type
            )
            
            assert response.success
            assert forecast_type in response.details["forecast_type"]
    
    @pytest.mark.asyncio
    async def test_get_dashboard_data(self, agent):
        """Test obtención de datos de dashboard"""
        response = await agent.get_dashboard_data("executive")
        
        assert response.success
        assert response.action == "get_dashboard_data"
        assert response.analytics_type == AnalyticsType.OPERATIONAL
        
        details = response.details
        assert "title" in details
        assert "widgets" in details
        
        # Verificar estructura de widgets
        widgets = details["widgets"]
        assert len(widgets) > 0
        
        for widget in widgets:
            assert "type" in widget
            assert "data" in widget
    
    @pytest.mark.asyncio
    async def test_get_dashboard_data_invalid_name(self, agent):
        """Test obtener datos de dashboard inexistente"""
        response = await agent.get_dashboard_data("nonexistent_dashboard")
        
        assert not response.success
        assert "no encontrado" in response.error
    
    @pytest.mark.asyncio
    async def test_process_request_generate_financial_report(self, agent):
        """Test procesamiento de request de reporte financiero"""
        request = {
            "action": "generate_financial_report",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "include_forecasts": True
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "report_id" in response
        assert "financial_metrics" in response
        assert "insights" in response
        assert "recommendations" in response
    
    @pytest.mark.asyncio
    async def test_process_request_track_kpi(self, agent):
        """Test procesamiento de request de tracking de KPI"""
        request = {
            "action": "track_kpi",
            "kpi_name": "Test Revenue",
            "value": 50000.0,
            "unit": "€",
            "target": 60000.0
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "kpi" in response
        assert response["kpi"]["name"] == "Test Revenue"
        assert response["kpi"]["value"] == 50000.0
    
    @pytest.mark.asyncio
    async def test_process_request_generate_forecast(self, agent):
        """Test procesamiento de request de predicción"""
        request = {
            "action": "generate_forecast",
            "metric_name": "sales",
            "periods": 4,
            "forecast_type": "linear"
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "forecasts" in response
        assert "accuracy_metrics" in response
        assert response["forecast_horizon"] == 4
    
    @pytest.mark.asyncio
    async def test_process_request_get_dashboard(self, agent):
        """Test procesamiento de request de dashboard"""
        request = {
            "action": "get_dashboard_data",
            "dashboard_name": "executive"
        }
        
        response = await agent.process_request(request)
        
        assert response["success"]
        assert "dashboard_data" in response
        assert "total_events" in response  # O alguna métrica del dashboard
    
    def test_get_stats(self, agent):
        """Test obtención de estadísticas"""
        stats = agent.get_stats()
        
        assert "agent_name" in stats
        assert "total_kpis" in stats
        assert "total_reports" in stats
        assert "available_dashboards" in stats
        assert "analytics_types" in stats
        assert "available_actions" in stats
        
        # Verificar acciones disponibles
        actions = stats["available_actions"]
        assert "generate_financial_report" in actions
        assert "track_kpi" in actions
        assert "generate_forecast" in actions
        assert "get_dashboard_data" in actions


class TestKPI:
    """Tests para KPI"""
    
    def test_kpi_creation(self):
        """Test creación de KPI"""
        kpi = KPI(
            name="Revenue",
            value=100000.0,
            unit="€",
            target=120000.0,
            previous_value=95000.0
        )
        
        assert kpi.name == "Revenue"
        assert kpi.value == 100000.0
        assert kpi.unit == "€"
        assert kpi.target == 120000.0
        assert kpi.previous_value == 95000.0
        assert kpi.change_percentage == 5.26  # Aproximadamente 5.26% de aumento
        assert kpi.trend == "up"
        assert kpi.period == "current"
        assert kpi.updated_at is not None


class TestFinancialMetric:
    """Tests para FinancialMetric"""
    
    def test_financial_metric_creation(self):
        """Test creación de métricas financieras"""
        metric = FinancialMetric(
            revenue=1000000.0,
            costs=700000.0,
            profit=300000.0,
            gross_margin=0.30,
            roi=0.15,
            cash_flow=50000.0
        )
        
        assert metric.revenue == 1000000.0
        assert metric.costs == 700000.0
        assert metric.profit == 300000.0
        assert metric.gross_margin == 0.30
        assert metric.roi == 0.15
        assert metric.cash_flow == 50000.0


class TestReport:
    """Tests para Report"""
    
    def test_report_creation(self):
        """Test creación de reporte"""
        date_range = (datetime.now(), datetime.now() + timedelta(days=30))
        
        report = Report(
            id="report_123",
            title="Monthly Financial Report",
            report_type=AnalyticsType.FINANCIAL,
            date_range=date_range
        )
        
        assert report.id == "report_123"
        assert report.title == "Monthly Financial Report"
        assert report.report_type == AnalyticsType.FINANCIAL
        assert report.date_range == date_range
        assert report.kpis == []
        assert report.metrics == []
        assert report.insights == []
        assert report.recommendations == []


if __name__ == "__main__":
    # Ejecutar tests
    pytest.main([__file__, "-v"])