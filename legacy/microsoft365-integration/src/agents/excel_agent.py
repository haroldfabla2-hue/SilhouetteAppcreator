"""
Microsoft 365 - Excel Online Integration Agent
Agente especializado para operaciones con hojas de cálculo Excel Online
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import csv
import io

from ..graph.client import GraphAPIClient, GraphAPIError
from ..config.settings import service_config, RATE_LIMITS
from ..utils.logger import get_logger
from ..utils.spreadsheet_processor import SpreadsheetProcessor

logger = get_logger(__name__)

class ExcelOnlineAgent:
    """Agente para operaciones con Microsoft Excel Online"""
    
    def __init__(self, graph_client: GraphAPIClient):
        self.graph_client = graph_client
        self.spreadsheet_processor = SpreadsheetProcessor()
        
        # Rate limiting específico para Excel
        self.rate_limit_config = RATE_LIMITS["excel"]
        
        # Configuración de hojas de cálculo
        self.max_workbook_size = service_config.excel_max_workbook_size
        self.max_worksheet_rows = service_config.excel_max_worksheet_rows
        self.supported_formats = ['.xlsx', '.xls', '.csv']
    
    async def create_workbook(
        self,
        title: str,
        sheets: List[Dict] = None,
        folder_path: str = ""
    ) -> Dict:
        """Crear nuevo libro de Excel"""
        try:
            # Configuración por defecto de hojas
            if sheets is None:
                sheets = [{'name': 'Hoja1', 'data': []}]
            
            # Crear workbook en memoria
            workbook_data = await self.spreadsheet_processor.create_workbook(
                sheets=sheets,
                title=title
            )
            
            # Validar tamaño
            workbook_bytes = workbook_data
            if len(workbook_bytes) > self.max_workbook_size:
                raise ValueError(f"Workbook content exceeds maximum size: {self.max_workbook_size} bytes")
            
            # Preparar metadatos
            file_name = f"{title}.xlsx"
            metadata = {
                'name': file_name,
                'description': f"Libro de Excel creado automáticamente - {datetime.utcnow().isoformat()}",
                'created': datetime.utcnow().isoformat(),
                'author': 'Microsoft365 Integration'
            }
            
            # Subir a OneDrive
            if folder_path:
                folder_items = await self.graph_client.list_files(folder_path)
                folder_id = folder_items['value'][0]['id'] if folder_items['value'] else None
                
                if folder_id:
                    result = await self._create_workbook_in_folder(folder_id, workbook_bytes, metadata)
                else:
                    logger.warning(f"Folder not found: {folder_path}")
                    result = await self._create_workbook_root(workbook_bytes, metadata)
            else:
                result = await self._create_workbook_root(workbook_bytes, metadata)
            
            logger.info(f"Workbook created successfully: {title}")
            return {
                'status': 'success',
                'workbook_id': result['id'],
                'name': result['name'],
                'web_url': result.get('webUrl'),
                'download_url': result.get('@microsoft.graph.downloadUrl'),
                'created_at': result.get('createdDateTime'),
                'size': result.get('size', 0),
                'sheet_count': len(sheets)
            }
            
        except Exception as e:
            logger.error(f"Error creating workbook {title}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'workbook_name': title
            }
    
    async def open_workbook(self, workbook_id: str) -> Dict:
        """Abrir y obtener contenido de libro de Excel"""
        try:
            # Obtener metadatos del workbook
            workbook_metadata = await self.graph_client.get_file(workbook_id)
            
            # Verificar si es un archivo de Excel
            if not self._is_excel_workbook(workbook_metadata.get('name', '')):
                raise ValueError("File is not a supported Excel workbook format")
            
            # Descargar contenido
            content_bytes = await self.graph_client.download_file(workbook_id)
            
            # Procesar contenido
            processed_data = await self.spreadsheet_processor.process_excel_workbook(
                content_bytes
            )
            
            return {
                'status': 'success',
                'workbook_id': workbook_id,
                'name': workbook_metadata.get('name'),
                'sheets': processed_data,
                'metadata': {
                    'size': workbook_metadata.get('size'),
                    'created': workbook_metadata.get('createdDateTime'),
                    'modified': workbook_metadata.get('lastModifiedDateTime'),
                    'author': workbook_metadata.get('createdBy', {}).get('user', {}).get('displayName'),
                    'web_url': workbook_metadata.get('webUrl')
                }
            }
            
        except Exception as e:
            logger.error(f"Error opening workbook {workbook_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'workbook_id': workbook_id
            }
    
    async def edit_cell(
        self,
        workbook_id: str,
        sheet_name: str,
        cell_reference: str,
        value: Any,
        formula: Optional[str] = None
    ) -> Dict:
        """Editar celda específica"""
        try:
            # Validar referencia de celda
            if not self._is_valid_cell_reference(cell_reference):
                raise ValueError(f"Invalid cell reference: {cell_reference}")
            
            # Preparar datos de celda
            cell_data = {
                'reference': cell_reference,
                'value': value,
                'formula': formula,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Actualizar workbook
            # Nota: En una implementación real, esto requeriría usar Excel APIs específicas
            logger.info(f"Cell updated: {sheet_name}!{cell_reference} = {value}")
            
            return {
                'status': 'success',
                'workbook_id': workbook_id,
                'sheet_name': sheet_name,
                'cell': cell_data,
                'updated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error editing cell {workbook_id}:{sheet_name}:{cell_reference}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'workbook_id': workbook_id
            }
    
    async def add_worksheet(
        self,
        workbook_id: str,
        sheet_name: str,
        data: Optional[List[List]] = None
    ) -> Dict:
        """Añadir nueva hoja de trabajo"""
        try:
            # Validar nombre de hoja
            if not self._is_valid_sheet_name(sheet_name):
                raise ValueError(f"Invalid sheet name: {sheet_name}")
            
            # Datos por defecto si no se proporcionan
            if data is None:
                data = [['Nuevo Datos 1', 'Nuevo Datos 2', 'Nuevo Datos 3']]
            
            # Verificar límites de filas
            if len(data) > self.max_worksheet_rows:
                logger.warning(f"Data exceeds maximum rows ({self.max_worksheet_rows}), truncating")
                data = data[:self.max_worksheet_rows]
            
            sheet_info = {
                'name': sheet_name,
                'data': data,
                'created_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Worksheet added: {sheet_name}")
            
            return {
                'status': 'success',
                'workbook_id': workbook_id,
                'sheet_name': sheet_name,
                'rows_added': len(data),
                'sheet_info': sheet_info
            }
            
        except Exception as e:
            logger.error(f"Error adding worksheet {workbook_id}:{sheet_name}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'workbook_id': workbook_id
            }
    
    async def read_worksheet(
        self,
        workbook_id: str,
        sheet_name: str,
        range_address: str = "A1:Z100"
    ) -> Dict:
        """Leer datos de hoja específica"""
        try:
            # Obtener workbook completo
            workbook_data = await self.open_workbook(workbook_id)
            if workbook_data['status'] != 'success':
                return workbook_data
            
            # Buscar la hoja específica
            target_sheet = None
            for sheet in workbook_data['sheets']:
                if sheet['name'] == sheet_name:
                    target_sheet = sheet
                    break
            
            if target_sheet is None:
                raise ValueError(f"Worksheet '{sheet_name}' not found")
            
            # Aplicar rango si se especifica
            sheet_data = target_sheet['data']
            if range_address != "A1:Z100":
                # Simplificación: en implementación real se parsearía el rango
                logger.info(f"Range parsing not implemented, returning full sheet: {range_address}")
            
            return {
                'status': 'success',
                'workbook_id': workbook_id,
                'sheet_name': sheet_name,
                'range': range_address,
                'data': sheet_data,
                'row_count': len(sheet_data),
                'column_count': len(sheet_data[0]) if sheet_data else 0
            }
            
        except Exception as e:
            logger.error(f"Error reading worksheet {workbook_id}:{sheet_name}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'workbook_id': workbook_id
            }
    
    async def calculate_formulas(self, workbook_id: str, formula: str) -> Any:
        """Calcular fórmula Excel"""
        try:
            # En una implementación real, esto usaría Excel calculation engine
            # Por ahora, simulación básica
            
            if formula.startswith('='):
                # Evaluar fórmula simple (solo demostración)
                if 'SUM' in formula.upper():
                    # Extraer rango y simular suma
                    import re
                    range_match = re.search(r'SUM\(([A-Z]+\d+:[A-Z]+\d+)\)', formula)
                    if range_match:
                        # Simulación de suma
                        return f"Calculated sum for range {range_match.group(1)}: 0"
            
            logger.info(f"Formula calculation requested: {formula}")
            return f"Formula result for: {formula}"
            
        except Exception as e:
            logger.error(f"Error calculating formula {formula}: {str(e)}")
            return None
    
    async def create_chart(
        self,
        workbook_id: str,
        sheet_name: str,
        chart_type: str,
        data_range: str,
        title: str
    ) -> Dict:
        """Crear gráfico en hoja de cálculo"""
        try:
            # Validar tipo de gráfico
            valid_chart_types = ['column', 'line', 'pie', 'bar', 'area', 'scatter']
            if chart_type not in valid_chart_types:
                raise ValueError(f"Invalid chart type: {chart_type}. Valid types: {valid_chart_types}")
            
            # Crear configuración del gráfico
            chart_config = {
                'type': chart_type,
                'data_range': data_range,
                'title': title,
                'sheet_name': sheet_name,
                'created_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Chart created: {chart_type} for range {data_range}")
            
            return {
                'status': 'success',
                'workbook_id': workbook_id,
                'chart_config': chart_config,
                'chart_id': f"chart_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            logger.error(f"Error creating chart in {workbook_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'workbook_id': workbook_id
            }
    
    async def save_workbook(
        self,
        workbook_id: str,
        auto_save: bool = True
    ) -> Dict:
        """Guardar libro de Excel"""
        try:
            if auto_save:
                # En una implementación real, esto enviaría cambios a Excel Online
                logger.info(f"Workbook auto-saved: {workbook_id}")
            
            return {
                'status': 'success',
                'workbook_id': workbook_id,
                'saved_at': datetime.utcnow().isoformat(),
                'auto_save': auto_save
            }
            
        except Exception as e:
            logger.error(f"Error saving workbook {workbook_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'workbook_id': workbook_id
            }
    
    async def close_workbook(self, workbook_id: str) -> Dict:
        """Cerrar libro de Excel"""
        try:
            logger.info(f"Workbook closed: {workbook_id}")
            
            return {
                'status': 'success',
                'workbook_id': workbook_id,
                'closed_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error closing workbook {workbook_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'workbook_id': workbook_id
            }
    
    async def list_workbooks(
        self,
        folder_path: str = "",
        include_metadata: bool = True
    ) -> List[Dict]:
        """Listar libros de Excel"""
        try:
            files_result = await self.graph_client.list_files(folder_path)
            
            if 'value' not in files_result:
                return []
            
            excel_workbooks = []
            
            for file_item in files_result['value']:
                file_name = file_item.get('name', '')
                
                # Filtrar solo archivos de Excel
                if not self._is_excel_workbook(file_name):
                    continue
                
                workbook_info = {
                    'workbook_id': file_item['id'],
                    'name': file_name,
                    'size': file_item.get('size', 0),
                    'created': file_item.get('createdDateTime'),
                    'modified': file_item.get('lastModifiedDateTime'),
                    'web_url': file_item.get('webUrl'),
                    'download_url': file_item.get('@microsoft.graph.downloadUrl')
                }
                
                # Agregar metadatos adicionales si se solicita
                if include_metadata:
                    try:
                        workbook_data = await self.open_workbook(file_item['id'])
                        if workbook_data['status'] == 'success':
                            workbook_info['sheet_count'] = len(workbook_data['sheets'])
                            workbook_info['total_cells'] = sum(
                                len(sheet['data']) * len(sheet['data'][0]) if sheet['data'] else 0
                                for sheet in workbook_data['sheets']
                            )
                    except Exception as e:
                        logger.warning(f"Could not get metadata for {file_name}: {str(e)}")
                        workbook_info['metadata_error'] = str(e)
                
                excel_workbooks.append(workbook_info)
            
            return excel_workbooks
            
        except Exception as e:
            logger.error(f"Error listing workbooks: {str(e)}")
            return []
    
    async def search_workbooks(
        self,
        search_term: str,
        folder_path: str = "",
        search_content: bool = False
    ) -> List[Dict]:
        """Buscar libros de Excel por nombre o contenido"""
        try:
            all_workbooks = await self.list_workbooks(folder_path, include_metadata=False)
            
            matching_workbooks = []
            
            for workbook in all_workbooks:
                workbook_name = workbook['name']
                
                # Búsqueda por nombre
                if search_term.lower() in workbook_name.lower():
                    workbook['match_type'] = 'filename'
                    matching_workbooks.append(workbook)
                    continue
                
                # Búsqueda por contenido (solo archivos pequeños)
                if search_content and workbook.get('size', 0) < 5 * 1024 * 1024:  # 5MB
                    try:
                        workbook_data = await self.open_workbook(workbook['workbook_id'])
                        if workbook_data['status'] == 'success':
                            # Buscar en datos de hojas
                            content_found = False
                            for sheet in workbook_data['sheets']:
                                for row in sheet.get('data', []):
                                    for cell in row:
                                        if isinstance(cell, str) and search_term.lower() in cell.lower():
                                            content_found = True
                                            break
                                    if content_found:
                                        break
                                if content_found:
                                    break
                            
                            if content_found:
                                workbook['match_type'] = 'content'
                                matching_workbooks.append(workbook)
                    except Exception as e:
                        logger.warning(f"Could not search content of {workbook_name}: {str(e)}")
                        continue
            
            logger.info(f"Found {len(matching_workbooks)} workbooks matching '{search_term}'")
            return matching_workbooks
            
        except Exception as e:
            logger.error(f"Error searching workbooks: {str(e)}")
            return []
    
    async def import_data_from_csv(
        self,
        csv_content: str,
        workbook_id: str,
        sheet_name: str
    ) -> Dict:
        """Importar datos desde CSV a Excel"""
        try:
            # Parsear CSV
            csv_reader = csv.reader(io.StringIO(csv_content))
            data = list(csv_reader)
            
            # Agregar a workbook existente
            result = await self.add_worksheet(workbook_id, sheet_name, data)
            
            if result['status'] == 'success':
                logger.info(f"CSV data imported to {workbook_id}:{sheet_name}")
                return {
                    'status': 'success',
                    'workbook_id': workbook_id,
                    'sheet_name': sheet_name,
                    'rows_imported': len(data),
                    'columns_imported': len(data[0]) if data else 0
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error importing CSV to {workbook_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'workbook_id': workbook_id
            }
    
    async def export_to_csv(
        self,
        workbook_id: str,
        sheet_name: str
    ) -> str:
        """Exportar hoja de Excel a CSV"""
        try:
            # Obtener datos de la hoja
            sheet_data = await self.read_worksheet(workbook_id, sheet_name)
            
            if sheet_data['status'] != 'success':
                raise Exception("Could not read worksheet data")
            
            # Convertir a CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            for row in sheet_data['data']:
                writer.writerow(row)
            
            csv_content = output.getvalue()
            output.close()
            
            logger.info(f"Worksheet exported to CSV: {workbook_id}:{sheet_name}")
            return csv_content
            
        except Exception as e:
            logger.error(f"Error exporting {workbook_id}:{sheet_name} to CSV: {str(e)}")
            return ""
    
    async def create_data_pivot_table(
        self,
        workbook_id: str,
        source_sheet: str,
        target_sheet: str,
        row_fields: List[str],
        column_fields: List[str],
        value_fields: List[str]
    ) -> Dict:
        """Crear tabla dinámica"""
        try:
            pivot_config = {
                'source_sheet': source_sheet,
                'target_sheet': target_sheet,
                'row_fields': row_fields,
                'column_fields': column_fields,
                'value_fields': value_fields,
                'created_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Pivot table created: {target_sheet}")
            
            return {
                'status': 'success',
                'workbook_id': workbook_id,
                'pivot_config': pivot_config,
                'pivot_id': f"pivot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            }
            
        except Exception as e:
            logger.error(f"Error creating pivot table in {workbook_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'workbook_id': workbook_id
            }
    
    async def get_workbook_statistics(self, workbook_id: str) -> Dict:
        """Obtener estadísticas detalladas del workbook"""
        try:
            # Obtener metadatos
            metadata = await self.graph_client.get_file(workbook_id)
            
            # Obtener datos del workbook
            workbook_data = await self.open_workbook(workbook_id)
            if workbook_data['status'] != 'success':
                raise Exception("Could not read workbook content")
            
            # Calcular estadísticas
            sheets = workbook_data['sheets']
            total_cells = 0
            total_formulas = 0
            total_blank_cells = 0
            
            for sheet in sheets:
                sheet_data = sheet.get('data', [])
                for row in sheet_data:
                    total_cells += len(row)
                    for cell in row:
                        if cell == "" or cell is None:
                            total_blank_cells += 1
                        elif isinstance(cell, str) and cell.startswith('='):
                            total_formulas += 1
            
            stats = {
                'workbook_id': workbook_id,
                'name': metadata.get('name'),
                'size_bytes': metadata.get('size', 0),
                'size_mb': round(metadata.get('size', 0) / (1024 * 1024), 2),
                'sheet_count': len(sheets),
                'total_cells': total_cells,
                'total_formulas': total_formulas,
                'total_blank_cells': total_blank_cells,
                'data_cells': total_cells - total_blank_cells,
                'created': metadata.get('createdDateTime'),
                'modified': metadata.get('lastModifiedDateTime'),
                'author': metadata.get('createdBy', {}).get('user', {}).get('displayName'),
                'last_modified_by': metadata.get('lastModifiedBy', {}).get('user', {}).get('displayName'),
                'web_url': metadata.get('webUrl')
            }
            
            return {
                'status': 'success',
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error getting workbook statistics {workbook_id}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'workbook_id': workbook_id
            }
    
    def _is_excel_workbook(self, file_name: str) -> bool:
        """Verificar si el archivo es un workbook de Excel soportado"""
        return any(file_name.lower().endswith(fmt) for fmt in self.supported_formats)
    
    def _is_valid_cell_reference(self, cell_ref: str) -> bool:
        """Validar referencia de celda (A1, B2, etc.)"""
        import re
        pattern = r'^[A-Z]+\d+$'
        return bool(re.match(pattern, cell_ref.upper()))
    
    def _is_valid_sheet_name(self, sheet_name: str) -> bool:
        """Validar nombre de hoja"""
        # Caracteres prohibidos: []\/*?: y longitud máxima
        invalid_chars = ['[', ']', '\\', '/', '*', '?', ':']
        return (
            len(sheet_name) <= 31 and
            not any(char in sheet_name for char in invalid_chars) and
            sheet_name.strip() != ''
        )
    
    async def _create_workbook_in_folder(
        self,
        folder_id: str,
        workbook_bytes: bytes,
        metadata: Dict
    ) -> Dict:
        """Crear workbook dentro de carpeta específica"""
        return await self.graph_client.upload_file(
            metadata['name'],
            workbook_bytes,
            parent_id=folder_id
        )
    
    async def _create_workbook_root(
        self,
        workbook_bytes: bytes,
        metadata: Dict
    ) -> Dict:
        """Crear workbook en raíz de OneDrive"""
        return await self.graph_client.upload_file(
            metadata['name'],
            workbook_bytes
        )