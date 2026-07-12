"""
Google Sheets Agent - Agente Especializado para Google Sheets
Proporciona capacidades avanzadas de análisis de datos, creación de reportes y automatización
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import pandas as pd
import numpy as np
from io import StringIO

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
import httpx

from .base_google_workspace_agent import (
    BaseGoogleWorkspaceAgent, 
    GoogleWorkspaceService, 
    GoogleWorkspaceConfig,
    ApiResponse
)
from ...core.exceptions import AgentException, handle_exceptions
from ...core.config import settings


class CellFormat(Enum):
    """Formatos de celda"""
    TEXT = "text"
    NUMBER = "number"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    DATE = "date"
    TIME = "time"
    BOOLEAN = "boolean"
    FORMULA = "formula"


class ChartType(Enum):
    """Tipos de gráficos"""
    COLUMN = "COLUMN"
    BAR = "BAR"
    LINE = "LINE"
    PIE = "PIE"
    SCATTER = "SCATTER"
    AREA = "AREA"
    COMBO = "COMBO"
    SPARKLINE = "SPARKLINE"


class PivotFunction(Enum):
    """Funciones para Pivot Tables"""
    SUM = "SUM"
    COUNT = "COUNT"
    AVERAGE = "AVERAGE"
    MAX = "MAX"
    MIN = "MIN"
    PRODUCT = "PRODUCT"
    STDDEV = "STDDEV"
    VAR = "VAR"


@dataclass
class CellData:
    """Datos de celda"""
    value: Any
    formula: Optional[str] = None
    format: Optional[CellFormat] = None
    style: Optional[Dict[str, Any]] = None


@dataclass
class RangeData:
    """Rango de datos"""
    start_row: int
    end_row: int
    start_column: int
    end_column: int
    values: List[List[Any]] = field(default_factory=list)
    formulas: List[List[str]] = field(default_factory=list)


@dataclass
class ChartConfig:
    """Configuración de gráfico"""
    chart_type: ChartType
    title: str
    data_range: str
    position: Dict[str, int]
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PivotConfig:
    """Configuración de tabla dinámica"""
    source_range: str
    rows: List[str]
    columns: List[str]
    values: List[str]
    function: PivotFunction = PivotFunction.SUM
    filters: Optional[List[str]] = None


@dataclass
class DataAnalysis:
    """Análisis de datos"""
    row_count: int
    column_count: int
    null_values: Dict[str, int]
    data_types: Dict[str, str]
    summary_stats: Dict[str, Dict[str, float]]
    correlations: Dict[str, float]
    outliers: List[Dict[str, Any]]


@dataclass
class ReportConfig:
    """Configuración de reporte"""
    title: str
    description: str
    data_source: str
    charts: List[ChartConfig]
    summary_table: Optional[str] = None
    filters: Optional[List[str]] = None
    format_style: str = "professional"


class GoogleSheetsAgent(BaseGoogleWorkspaceAgent):
    """
    Agente Especializado para Google Sheets
    
    Funcionalidades:
    - Crear y editar hojas de cálculo
    - Análisis estadístico de datos
    - Creación de gráficos dinámicos
    - Tablas dinámicas (Pivot Tables)
    - Importación y exportación de datos
    - Automatización con fórmulas
    - Reportes automáticos
    - Colaboración en tiempo real
    """
    
    def __init__(self, config: GoogleWorkspaceConfig):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.sheets_service = None
        
        # Configurar capacidades específicas
        self.add_capability(AgentCapability.DATA_ANALYSIS)
        self.add_capability(AgentCapability.DOCUMENT_PROCESSING)
    
    async def initialize(self):
        """Inicializar servicio de Sheets"""
        await super().authenticate()
        self.sheets_service = await self.get_service(GoogleWorkspaceService.SHEETS)
    
    @handle_exceptions
    async def create_spreadsheet(
        self, 
        title: str,
        sheets: Optional[List[str]] = None
    ) -> ApiResponse:
        """
        Crear nueva hoja de cálculo
        
        Args:
            title: Título de la hoja de cálculo
            sheets: Lista de nombres de hojas
            
        Returns:
            ApiResponse: Resultado con ID de la hoja
        """
        try:
            spreadsheet = {
                'properties': {
                    'title': title
                }
            }
            
            # Agregar hojas si se especifican
            if sheets:
                spreadsheet['sheets'] = [
                    {'properties': {'title': sheet_name}}
                    for sheet_name in sheets
                ]
            
            result = self.sheets_service.spreadsheets().create(
                body=spreadsheet
            ).execute()
            
            spreadsheet_id = result.get('properties', {}).get('spreadsheetId')
            
            self.logger.info(f"Hoja de cálculo creada: {spreadsheet_id}")
            
            return ApiResponse(
                success=True,
                data={
                    'spreadsheet_id': spreadsheet_id,
                    'title': title,
                    'url': f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit"
                }
            )
            
        except Exception as e:
            error_msg = f"Error creando hoja de cálculo: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def read_data(
        self, 
        spreadsheet_id: str, 
        range_name: str
    ) -> ApiResponse:
        """
        Leer datos de un rango específico
        
        Args:
            spreadsheet_id: ID de la hoja de cálculo
            range_name: Rango de celdas (ej: "A1:C10" o "Sheet1!A1:C10")
            
        Returns:
            ApiResponse: Datos leídos
        """
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            return ApiResponse(
                success=True,
                data={
                    'values': values,
                    'range': range_name,
                    'row_count': len(values),
                    'column_count': len(values[0]) if values else 0
                }
            )
            
        except Exception as e:
            error_msg = f"Error leyendo datos: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def write_data(
        self, 
        spreadsheet_id: str, 
        range_name: str, 
        values: List[List[Any]]
    ) -> ApiResponse:
        """
        Escribir datos en un rango
        
        Args:
            spreadsheet_id: ID de la hoja de cálculo
            range_name: Rango de destino
            values: Datos a escribir
            
        Returns:
            ApiResponse: Resultado de la operación
        """
        try:
            body = {
                'values': values
            }
            
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            return ApiResponse(
                success=True,
                data={
                    'updated_cells': result.get('updatedCells', 0),
                    'range': range_name
                }
            )
            
        except Exception as e:
            error_msg = f"Error escribiendo datos: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def import_data(
        self,
        spreadsheet_id: str,
        url: str,
        sheet_name: str = "Imported Data",
        cell_range: str = "A1"
    ) -> ApiResponse:
        """
        Importar datos desde URL (CSV, Excel, etc.)
        
        Args:
            spreadsheet_id: ID de la hoja de cálculo
            url: URL de los datos
            sheet_name: Nombre de la hoja destino
            cell_range: Celda donde empezar la importación
            
        Returns:
            ApiResponse: Resultado de la importación
        """
        try:
            # Descargar datos
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                response.raise_for_status()
            
            # Parsear según tipo de contenido
            content_type = response.headers.get('content-type', '')
            imported_data = []
            
            if 'csv' in content_type.lower():
                # Parsear CSV
                csv_text = response.text
                df = pd.read_csv(StringIO(csv_text))
                imported_data = [df.columns.tolist()] + df.values.tolist()
            
            elif 'json' in content_type.lower():
                # Parsear JSON
                data = response.json()
                if isinstance(data, list) and data:
                    if isinstance(data[0], dict):
                        keys = list(data[0].keys())
                        imported_data = [keys] + [[row[k] for k in keys] for row in data]
                    else:
                        imported_data = [[item] for item in data]
            
            # Escribir datos en la hoja
            range_name = f"{sheet_name}!{cell_range}"
            write_result = await self.write_data(spreadsheet_id, range_name, imported_data)
            
            if write_result.success:
                return ApiResponse(
                    success=True,
                    data={
                        'imported_rows': len(imported_data),
                        'imported_columns': len(imported_data[0]) if imported_data else 0,
                        'sheet_name': sheet_name,
                        'source_url': url
                    }
                )
            else:
                return write_result
            
        except Exception as e:
            error_msg = f"Error importando datos: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def create_pivot_table(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        config: PivotConfig
    ) -> ApiResponse:
        """
        Crear tabla dinámica
        
        Args:
            spreadsheet_id: ID de la hoja de cálculo
            sheet_name: Nombre de la hoja
            config: Configuración de la tabla dinámica
            
        Returns:
            ApiResponse: Resultado de la operación
        """
        try:
            # Preparar requests para crear pivot table
            requests = [
                {
                    'updateCells': {
                        'rows': [
                            {
                                'values': [
                                    {
                                        'pivotTable': {
                                            'source': {
                                                'sheetId': 0,  # Sheet ID del origen
                                                'startRowIndex': 0,
                                                'endRowIndex': 10,
                                                'startColumnIndex': 0,
                                                'endColumnIndex': 10
                                            },
                                            'rows': [
                                                {'sourceColumnOffset': 0}
                                            ],
                                            'columns': [
                                                {'sourceColumnOffset': 1}
                                            ],
                                            'values': [
                                                {
                                                    'summarizeFunction': config.function.value,
                                                    'sourceColumnOffset': 2
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        ],
                        'fields': 'pivotTable'
                    }
                }
            ]
            
            body = {'requests': requests}
            result = self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            return ApiResponse(
                success=True,
                data={'pivot_table_created': True}
            )
            
        except Exception as e:
            error_msg = f"Error creando tabla dinámica: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def create_chart(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        config: ChartConfig
    ) -> ApiResponse:
        """
        Crear gráfico en la hoja
        
        Args:
            spreadsheet_id: ID de la hoja de cálculo
            sheet_name: Nombre de la hoja
            config: Configuración del gráfico
            
        Returns:
            ApiResponse: Resultado de la operación
        """
        try:
            requests = [
                {
                    'addChart': {
                        'chart': {
                            'spec': {
                                'title': config.title,
                                'basicChart': {
                                    'chartType': config.chart_type.value,
                                    'legendPosition': 'BOTTOM_LEGEND',
                                    'axis': [
                                        {
                                            'position': 'BOTTOM_AXIS',
                                            'title': 'X Axis'
                                        },
                                        {
                                            'position': 'LEFT_AXIS',
                                            'title': 'Y Axis'
                                        }
                                    ]
                                }
                            },
                            'position': {
                                'overlayPosition': {
                                    'anchorCell': {
                                        'sheetId': sheet_name,
                                        'rowIndex': config.position.get('row', 0),
                                        'columnIndex': config.position.get('column', 0)
                                    }
                                }
                            }
                        }
                    }
                }
            ]
            
            body = {'requests': requests}
            result = self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            return ApiResponse(
                success=True,
                data={'chart_id': result.get('replies', [{}])[0].get('addChart', {}).get('chart', {}).get('chartId')}
            )
            
        except Exception as e:
            error_msg = f"Error creando gráfico: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def analyze_data(
        self,
        spreadsheet_id: str,
        range_name: str
    ) -> ApiResponse:
        """
        Analizar datos estadísticamente
        
        Args:
            spreadsheet_id: ID de la hoja de cálculo
            range_name: Rango de datos a analizar
            
        Returns:
            ApiResponse: Análisis estadístico
        """
        try:
            # Leer datos
            read_result = await self.read_data(spreadsheet_id, range_name)
            if not read_result.success:
                return read_result
            
            values = read_result.data['values']
            
            if not values:
                return ApiResponse(success=False, error="No hay datos para analizar")
            
            # Convertir a DataFrame de pandas
            df = pd.DataFrame(values[1:], columns=values[0])
            
            # Análisis estadístico
            analysis = self._perform_statistical_analysis(df)
            
            return ApiResponse(
                success=True,
                data=analysis
            )
            
        except Exception as e:
            error_msg = f"Error analizando datos: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def create_report(
        self,
        spreadsheet_id: str,
        sheet_name: str,
        config: ReportConfig
    ) -> ApiResponse:
        """
        Crear reporte automático con análisis y gráficos
        
        Args:
            spreadsheet_id: ID de la hoja de cálculo
            sheet_name: Nombre de la hoja para el reporte
            config: Configuración del reporte
            
        Returns:
            ApiResponse: Resultado de la creación del reporte
        """
        try:
            # Leer datos fuente
            data_result = await self.read_data(spreadsheet_id, config.data_source)
            if not data_result.success:
                return data_result
            
            values = data_result.data['values']
            
            if not values:
                return ApiResponse(success=False, error="No hay datos para el reporte")
            
            # Crear contenido del reporte
            report_content = self._generate_report_content(values, config)
            
            # Escribir reporte
            report_range = f"{sheet_name}!A1"
            write_result = await self.write_data(
                spreadsheet_id,
                report_range,
                report_content
            )
            
            if write_result.success:
                # Crear gráficos si se especifican
                chart_results = []
                for i, chart_config in enumerate(config.charts):
                    chart_position = {'row': len(report_content) + 2, 'column': i * 6 + 1}
                    chart_config.position = chart_position
                    
                    chart_result = await self.create_chart(
                        spreadsheet_id,
                        sheet_name,
                        chart_config
                    )
                    chart_results.append(chart_result)
                
                return ApiResponse(
                    success=True,
                    data={
                        'report_created': True,
                        'charts_created': len([r for r in chart_results if r.success]),
                        'report_sheet': sheet_name
                    }
                )
            else:
                return write_result
            
        except Exception as e:
            error_msg = f"Error creando reporte: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    @handle_exceptions
    async def export_to_csv(
        self,
        spreadsheet_id: str,
        sheet_name: str = "Sheet1"
    ) -> ApiResponse:
        """
        Exportar hoja de cálculo a CSV
        
        Args:
            spreadsheet_id: ID de la hoja de cálculo
            sheet_name: Nombre de la hoja
            
        Returns:
            ApiResponse: Datos CSV exportados
        """
        try:
            # Leer todos los datos
            range_name = f"{sheet_name}!A:Z"  # Rango amplio
            result = await self.read_data(spreadsheet_id, range_name)
            
            if result.success:
                values = result.data['values']
                
                # Convertir a CSV
                if values:
                    import csv
                    import io
                    
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerows(values)
                    csv_data = output.getvalue()
                    
                    return ApiResponse(
                        success=True,
                        data={
                            'csv_data': csv_data,
                            'row_count': len(values),
                            'column_count': len(values[0]) if values else 0
                        }
                    )
                else:
                    return ApiResponse(success=False, error="La hoja está vacía")
            else:
                return result
            
        except Exception as e:
            error_msg = f"Error exportando a CSV: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    def _perform_statistical_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Realizar análisis estadístico completo"""
        analysis = {}
        
        # Información básica
        analysis['basic_info'] = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'memory_usage': df.memory_usage(deep=True).sum(),
            'missing_values': df.isnull().sum().to_dict()
        }
        
        # Análisis por columnas
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 0:
            analysis['numeric_summary'] = df[numeric_columns].describe().to_dict()
            analysis['correlations'] = df[numeric_columns].corr().to_dict()
        
        # Análisis de texto
        text_columns = df.select_dtypes(include=['object']).columns
        if len(text_columns) > 0:
            analysis['text_analysis'] = {}
            for col in text_columns:
                analysis['text_analysis'][col] = {
                    'unique_values': df[col].nunique(),
                    'most_frequent': df[col].mode().tolist()[:5],
                    'avg_length': df[col].astype(str).str.len().mean()
                }
        
        return analysis
    
    def _generate_report_content(
        self, 
        values: List[List[Any]], 
        config: ReportConfig
    ) -> List[List[Any]]:
        """Generar contenido del reporte"""
        content = []
        
        # Título
        content.append([config.title])
        content.append([config.description])
        content.append([])
        
        # Resumen de datos
        if values:
            content.append(['Resumen de Datos'])
            content.append(['Total de filas:', len(values) - 1])  # Excluir encabezados
            content.append(['Total de columnas:', len(values[0]) if values else 0])
            content.append([])
        
        # Tabla resumen si se especifica
        if config.summary_table and values:
            content.append(['Tabla Resumen'])
            content.extend(values[:6])  # Primeras 5 filas de datos
            content.append([])
        
        # Gráficos se agregan después con API
        
        return content
    
    @handle_exceptions
    async def apply_formula(
        self,
        spreadsheet_id: str,
        range_name: str,
        formula: str
    ) -> ApiResponse:
        """
        Aplicar fórmula a un rango
        
        Args:
            spreadsheet_id: ID de la hoja de cálculo
            range_name: Rango donde aplicar la fórmula
            formula: Fórmula a aplicar
            
        Returns:
            ApiResponse: Resultado de la operación
        """
        try:
            # Crear matriz con la fórmula para todas las celdas del rango
            requests = [
                {
                    'updateCells': {
                        'range': {
                            'sheetId': 0,  # Sheet ID
                            'startRowIndex': 0,
                            'endRowIndex': 10,
                            'startColumnIndex': 0,
                            'endColumnIndex': 5
                        },
                        'rows': [
                            {
                                'values': [
                                    {
                                        'userEnteredValue': {
                                            'formulaValue': formula
                                        }
                                    }
                                ]
                            }
                        ],
                        'fields': 'userEnteredValue'
                    }
                }
            ]
            
            body = {'requests': requests}
            result = self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            return ApiResponse(
                success=True,
                data={'formula_applied': formula}
            )
            
        except Exception as e:
            error_msg = f"Error aplicando fórmula: {str(e)}"
            self.logger.error(error_msg)
            return ApiResponse(success=False, error=error_msg)
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del agente Google Sheets"""
        try:
            # Verificar servicio base
            base_health = await super().health_check()
            
            if not base_health["healthy"]:
                return base_health
            
            # Test específico de Sheets API
            test_spreadsheet = await self.create_spreadsheet(
                title="Health Check Test",
                sheets=["Test Sheet"]
            )
            
            if test_spreadsheet.success:
                spreadsheet_id = test_spreadsheet.data['spreadsheet_id']
                
                # Test de escritura
                write_result = await self.write_data(
                    spreadsheet_id,
                    "A1:C3",
                    [
                        ["Producto", "Cantidad", "Precio"],
                        ["Manzanas", 10, 1.50],
                        ["Naranjas", 15, 2.00]
                    ]
                )
                
                if write_result.success:
                    return {
                        "healthy": True,
                        "service": "Google Sheets Agent",
                        "test_creation": "passed",
                        "test_writing": "passed",
                        "details": base_health
                    }
            
            return {
                "healthy": False,
                "error": "Error en tests de Sheets API",
                "details": base_health
            }
                
        except Exception as e:
            return {
                "healthy": False,
                "error": f"Error en health check: {str(e)}",
                "service": "Google Sheets Agent"
            }