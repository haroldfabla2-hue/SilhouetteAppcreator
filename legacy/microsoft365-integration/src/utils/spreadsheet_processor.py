"""
Microsoft 365 - Spreadsheet Processor
Procesador especializado para hojas de cálculo Excel
"""

import logging
import csv
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class SpreadsheetProcessor:
    """Procesador para hojas de cálculo Excel y CSV"""
    
    def __init__(self):
        self.supported_formats = ['.xlsx', '.xls', '.csv']
        self.max_rows = 1048576  # Límite de Excel
        self.max_columns = 16384
        self.max_processing_size = 50 * 1024 * 1024  # 50MB
    
    async def create_workbook(
        self,
        sheets: List[Dict],
        title: str = "Workbook"
    ) -> bytes:
        """Crear nuevo workbook Excel"""
        try:
            # En implementación real, esto usaría openpyxl o similar
            # Por ahora, simulamos la creación
            
            workbook_data = {
                'title': title,
                'sheets': sheets,
                'created_at': datetime.utcnow().isoformat(),
                'metadata': {
                    'version': '1.0',
                    'created_by': 'Microsoft365 Integration',
                    'sheet_count': len(sheets)
                }
            }
            
            # Convertir a bytes (en implementación real sería archivo Excel)
            workbook_bytes = json.dumps(workbook_data, ensure_ascii=False).encode('utf-8')
            
            logger.info(f"Workbook created: {title} with {len(sheets)} sheets")
            return workbook_bytes
            
        except Exception as e:
            logger.error(f"Error creating workbook: {str(e)}")
            raise
    
    async def process_excel_workbook(self, content_bytes: bytes) -> List[Dict]:
        """Procesar contenido de workbook Excel"""
        try:
            if len(content_bytes) > self.max_processing_size:
                raise ValueError(f"Workbook too large: {len(content_bytes)} bytes")
            
            # En implementación real, esto procesaría el archivo Excel
            # Por ahora, simulamos el procesamiento
            
            # Simular datos de hojas
            sheets_data = [
                {
                    'name': 'Hoja1',
                    'data': [
                        ['Producto', 'Cantidad', 'Precio', 'Total'],
                        ['Producto A', '10', '$25.00', '$250.00'],
                        ['Producto B', '5', '$30.00', '$150.00'],
                        ['Producto C', '8', '$20.00', '$160.00']
                    ],
                    'row_count': 4,
                    'column_count': 4
                },
                {
                    'name': 'Resumen',
                    'data': [
                        ['Total Items', '560.00'],
                        ['Total Productos', '3'],
                        ['Promedio Precio', '$25.00']
                    ],
                    'row_count': 3,
                    'column_count': 2
                }
            ]
            
            # Post-procesar datos
            for sheet in sheets_data:
                sheet['analyzed'] = await self._analyze_sheet_data(sheet['data'])
            
            logger.info(f"Excel workbook processed: {len(sheets_data)} sheets")
            return sheets_data
            
        except Exception as e:
            logger.error(f"Error processing Excel workbook: {str(e)}")
            raise
    
    async def analyze_formulas(self, sheet_data: List[List]) -> Dict:
        """Analizar fórmulas en la hoja de cálculo"""
        try:
            formulas_found = []
            calculation_results = {}
            
            for row_idx, row in enumerate(sheet_data):
                for col_idx, cell in enumerate(row):
                    if isinstance(cell, str) and cell.startswith('='):
                        formulas_found.append({
                            'cell_reference': f"{self._get_column_name(col_idx)}{row_idx + 1}",
                            'formula': cell,
                            'row': row_idx + 1,
                            'column': col_idx + 1
                        })
                        
                        # Simular cálculo de fórmula
                        calculation_results[f"{self._get_column_name(col_idx)}{row_idx + 1}"] = self._simulate_formula_calculation(cell)
            
            analysis = {
                'total_formulas': len(formulas_found),
                'formulas': formulas_found,
                'calculated_values': calculation_results,
                'formula_types': self._categorize_formulas(formulas_found),
                'complexity_score': self._calculate_complexity_score(formulas_found),
                'analyzed_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Formula analysis completed: {len(formulas_found)} formulas found")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing formulas: {str(e)}")
            raise
    
    async def create_pivot_table(
        self,
        source_data: List[List],
        row_fields: List[str],
        column_fields: List[str],
        value_fields: List[str],
        aggregation: str = "sum"
    ) -> Dict:
        """Crear tabla dinámica"""
        try:
            # Simular creación de tabla dinámica
            pivot_data = {
                'source_sheet': 'Source',
                'row_fields': row_fields,
                'column_fields': column_fields,
                'value_fields': value_fields,
                'aggregation': aggregation,
                'created_at': datetime.utcnow().isoformat(),
                'row_count': len(source_data),
                'column_count': len(source_data[0]) if source_data else 0
            }
            
            # Generar datos de tabla dinámica simulados
            pivot_table_data = self._generate_pivot_table_data(source_data, row_fields, value_fields, aggregation)
            pivot_data['pivot_data'] = pivot_table_data
            
            logger.info(f"Pivot table created with aggregation: {aggregation}")
            return pivot_data
            
        except Exception as e:
            logger.error(f"Error creating pivot table: {str(e)}")
            raise
    
    async def validate_data(self, sheet_data: List[List]) -> Dict:
        """Validar datos en la hoja de cálculo"""
        try:
            validation_results = {
                'total_cells': 0,
                'valid_cells': 0,
                'invalid_cells': 0,
                'errors': [],
                'warnings': [],
                'data_quality_score': 0.0,
                'validated_at': datetime.utcnow().isoformat()
            }
            
            if not sheet_data:
                return validation_results
            
            for row_idx, row in enumerate(sheet_data):
                for col_idx, cell in enumerate(row):
                    validation_results['total_cells'] += 1
                    
                    # Validar celda
                    cell_validation = self._validate_cell(cell, row_idx + 1, col_idx + 1)
                    
                    if cell_validation['is_valid']:
                        validation_results['valid_cells'] += 1
                    else:
                        validation_results['invalid_cells'] += 1
                        validation_results['errors'].append(cell_validation)
                    
                    if cell_validation.get('warning'):
                        validation_results['warnings'].append(cell_validation)
            
            # Calcular puntuación de calidad
            total_cells = validation_results['total_cells']
            validation_results['data_quality_score'] = (
                validation_results['valid_cells'] / total_cells * 100
            ) if total_cells > 0 else 0
            
            logger.info(f"Data validation completed: {validation_results['valid_cells']}/{total_cells} valid cells")
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating data: {str(e)}")
            raise
    
    async def optimize_worksheet(self, sheet_data: List[List]) -> List[List]:
        """Optimizar hoja de cálculo para mejor rendimiento"""
        try:
            optimized_data = []
            
            # Eliminar filas y columnas vacías
            optimized_data = self._remove_empty_rows_and_columns(sheet_data)
            
            # Normalizar tipos de datos
            optimized_data = await self._normalize_data_types(optimized_data)
            
            # Optimizar fórmulas (simulado)
            optimized_data = self._optimize_formulas(optimized_data)
            
            logger.info(f"Worksheet optimized: {len(optimized_data)} rows")
            return optimized_data
            
        except Exception as e:
            logger.error(f"Error optimizing worksheet: {str(e)}")
            raise
    
    async def convert_to_csv(self, sheet_data: List[List]) -> str:
        """Convertir datos de hoja a formato CSV"""
        try:
            import io
            output = io.StringIO()
            writer = csv.writer(output)
            
            for row in sheet_data:
                writer.writerow(row)
            
            csv_content = output.getvalue()
            output.close()
            
            logger.info(f"Data converted to CSV: {len(sheet_data)} rows")
            return csv_content
            
        except Exception as e:
            logger.error(f"Error converting to CSV: {str(e)}")
            raise
    
    async def import_csv_data(self, csv_content: str) -> List[List]:
        """Importar datos desde contenido CSV"""
        try:
            import io
            input_data = io.StringIO(csv_content)
            reader = csv.reader(input_data)
            
            data = []
            for row in reader:
                data.append(row)
            
            input_data.close()
            
            logger.info(f"CSV data imported: {len(data)} rows")
            return data
            
        except Exception as e:
            logger.error(f"Error importing CSV data: {str(e)}")
            raise
    
    def _analyze_sheet_data(self, data: List[List]) -> Dict:
        """Analizar estructura de datos de una hoja"""
        if not data:
            return {'empty': True}
        
        analysis = {
            'total_rows': len(data),
            'total_columns': len(data[0]) if data else 0,
            'data_types': {},
            'empty_cells': 0,
            'formula_cells': 0,
            'numeric_cells': 0,
            'text_cells': 0,
            'date_cells': 0
        }
        
        for row in data:
            for cell in row:
                if not cell or cell == '':
                    analysis['empty_cells'] += 1
                elif isinstance(cell, str) and cell.startswith('='):
                    analysis['formula_cells'] += 1
                elif self._is_numeric(cell):
                    analysis['numeric_cells'] += 1
                elif self._is_date(cell):
                    analysis['date_cells'] += 1
                else:
                    analysis['text_cells'] += 1
        
        # Calcular tipos de datos predominantes
        total_filled_cells = analysis['total_rows'] * analysis['total_columns'] - analysis['empty_cells']
        if total_filled_cells > 0:
            analysis['data_types']['numeric_percentage'] = (analysis['numeric_cells'] / total_filled_cells) * 100
            analysis['data_types']['text_percentage'] = (analysis['text_cells'] / total_filled_cells) * 100
            analysis['data_types']['formula_percentage'] = (analysis['formula_cells'] / total_filled_cells) * 100
        
        return analysis
    
    def _simulate_formula_calculation(self, formula: str) -> Any:
        """Simular cálculo de fórmula"""
        # Simulación muy básica
        if 'SUM' in formula.upper():
            return "calculated_sum"
        elif 'AVERAGE' in formula.upper():
            return "calculated_average"
        elif 'COUNT' in formula.upper():
            return "calculated_count"
        else:
            return "calculated_value"
    
    def _categorize_formulas(self, formulas: List[Dict]) -> Dict:
        """Categorizar tipos de fórmulas encontradas"""
        categories = {
            'mathematical': 0,
            'logical': 0,
            'text': 0,
            'lookup': 0,
            'date': 0,
            'financial': 0
        }
        
        for formula_info in formulas:
            formula = formula_info['formula'].upper()
            
            if any(func in formula for func in ['SUM', 'AVERAGE', 'MAX', 'MIN', 'ROUND']):
                categories['mathematical'] += 1
            elif any(func in formula for func in ['IF', 'AND', 'OR', 'NOT']):
                categories['logical'] += 1
            elif any(func in formula for func in ['CONCATENATE', 'LEFT', 'RIGHT', 'MID']):
                categories['text'] += 1
            elif any(func in formula for func in ['VLOOKUP', 'HLOOKUP', 'INDEX', 'MATCH']):
                categories['lookup'] += 1
            elif any(func in formula for func in ['DATE', 'TODAY', 'NOW']):
                categories['date'] += 1
            elif any(func in formula for func in ['PV', 'FV', 'PMT']):
                categories['financial'] += 1
        
        return categories
    
    def _calculate_complexity_score(self, formulas: List[Dict]) -> float:
        """Calcular puntuación de complejidad de fórmulas"""
        if not formulas:
            return 0.0
        
        total_complexity = 0
        for formula_info in formulas:
            formula = formula_info['formula']
            
            # Puntuación básica basada en longitud y funciones
            complexity = len(formula) * 0.1
            
            # Bonus por funciones anidadas
            nested_functions = formula.count('(')
            complexity += nested_functions * 0.5
            
            # Bonus por operadores complejos
            complex_operators = formula.count('&') + formula.count('*') + formula.count('/')
            complexity += complex_operators * 0.2
            
            total_complexity += complexity
        
        return round(total_complexity / len(formulas), 2)
    
    def _generate_pivot_table_data(self, source_data: List[List], row_fields: List[str], value_fields: List[str], aggregation: str) -> List[List]:
        """Generar datos simulados para tabla dinámica"""
        # Simulación básica de tabla dinámica
        headers = row_fields + value_fields
        pivot_data = [headers]
        
        # Simular datos agrupados
        sample_data = [
            ['Categoría A', '50'],
            ['Categoría B', '75'],
            ['Categoría C', '25']
        ]
        
        return pivot_data + sample_data
    
    def _validate_cell(self, cell: Any, row: int, column: int) -> Dict:
        """Validar celda individual"""
        validation = {
            'cell_reference': f"{self._get_column_name(column - 1)}{row}",
            'row': row,
            'column': column,
            'value': cell,
            'is_valid': True,
            'error': None,
            'warning': None
        }
        
        # Validaciones básicas
        if cell is None or cell == '':
            validation['is_valid'] = False
            validation['error'] = "Cell is empty"
        
        elif isinstance(cell, str) and cell.startswith('='):
            # Validar fórmula básica
            if not self._is_valid_formula(cell):
                validation['warning'] = "Formula may be invalid"
        
        elif self._is_numeric(cell):
            # Validar rango numérico
            try:
                num_value = float(cell)
                if num_value < 0:
                    validation['warning'] = "Negative number detected"
            except ValueError:
                validation['is_valid'] = False
                validation['error'] = "Invalid numeric format"
        
        return validation
    
    def _is_numeric(self, cell: Any) -> bool:
        """Verificar si el valor es numérico"""
        try:
            float(cell)
            return True
        except (ValueError, TypeError):
            return False
    
    def _is_date(self, cell: Any) -> bool:
        """Verificar si el valor es una fecha"""
        if not isinstance(cell, str):
            return False
        
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',  # MM/DD/YYYY
            r'\d{4}[/-]\d{1,2}[/-]\d{1,2}',  # YYYY/MM/DD
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}'
        ]
        
        return any(re.search(pattern, cell, re.IGNORECASE) for pattern in date_patterns)
    
    def _is_valid_formula(self, formula: str) -> bool:
        """Validar fórmula básica"""
        if not formula.startswith('='):
            return False
        
        # Verificar balance de paréntesis
        if formula.count('(') != formula.count(')'):
            return False
        
        # Verificar caracteres válidos básicos
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-*/()=.,:<>"& ')
        return all(char in valid_chars for char in formula[1:])
    
    def _get_column_name(self, column_index: int) -> str:
        """Convertir índice numérico a nombre de columna Excel"""
        result = ""
        index = column_index
        while index >= 0:
            result = chr(index % 26 + ord('A')) + result
            index = index // 26 - 1
        return result
    
    def _remove_empty_rows_and_columns(self, data: List[List]) -> List[List]:
        """Eliminar filas y columnas completamente vacías"""
        if not data:
            return data
        
        # Identificar filas vacías
        non_empty_rows = []
        for row in data:
            if any(cell and cell != '' for cell in row):
                non_empty_rows.append(row)
        
        if not non_empty_rows:
            return []
        
        # Identificar columnas vacías
        max_cols = max(len(row) for row in non_empty_rows)
        non_empty_columns = []
        
        for col_idx in range(max_cols):
            if any(col_idx < len(row) and row[col_idx] and row[col_idx] != '' for row in non_empty_rows):
                non_empty_columns.append(col_idx)
        
        # Filtrar datos
        filtered_data = []
        for row in non_empty_rows:
            new_row = [row[col_idx] for col_idx in non_empty_columns if col_idx < len(row)]
            filtered_data.append(new_row)
        
        return filtered_data
    
    async def _normalize_data_types(self, data: List[List]) -> List[List]:
        """Normalizar tipos de datos"""
        if not data:
            return data
        
        normalized_data = []
        
        for row in data:
            normalized_row = []
            for cell in row:
                if cell is None or cell == '':
                    normalized_row.append('')
                elif isinstance(cell, str):
                    # Detectar y convertir tipos
                    if self._is_numeric(cell):
                        try:
                            normalized_row.append(float(cell))
                        except ValueError:
                            normalized_row.append(cell)
                    elif self._is_date(cell):
                        normalized_row.append(cell)  # Mantener como string por ahora
                    else:
                        normalized_row.append(cell)
                else:
                    normalized_row.append(cell)
            
            normalized_data.append(normalized_row)
        
        return normalized_data
    
    def _optimize_formulas(self, data: List[List]) -> List[List]:
        """Optimizar fórmulas en los datos"""
        # En implementación real, esto optimizaría las fórmulas
        # Por ahora, solo identifica y marca las fórmulas
        return data