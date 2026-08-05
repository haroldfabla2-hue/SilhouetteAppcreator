"""
Tests unitarios para Excel Agent.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from typing import Dict, Any

from src.agents.excel_agent import ExcelAgent
from src.graph.client import GraphAPIClient
from src.auth.azure_ad import AzureADAuthenticator


@pytest.mark.unit
@pytest.mark.excel
class TestExcelAgent:
    """Tests para ExcelAgent."""

    @pytest.fixture
    def excel_agent(self, mock_graph_client, mock_authenticator):
        """Fixture para crear instancia de ExcelAgent."""
        return ExcelAgent(
            graph_client=mock_graph_client,
            authenticator=mock_authenticator
        )

    @pytest.mark.asyncio
    async def test_init(self, excel_agent):
        """Test inicialización de ExcelAgent."""
        assert excel_agent.graph_client is not None
        assert excel_agent.authenticator is not None
        assert excel_agent.base_url == "https://graph.microsoft.com/v1.0"

    @pytest.mark.asyncio
    async def test_create_workbook(self, excel_agent, sample_xlsx_content, mock_graph_client):
        """Test creación de libro de trabajo."""
        mock_response = {
            "id": "test-workbook-id",
            "name": "Test Workbook.xlsx",
            "webUrl": "https://excel.com/edit/test-workbook-id"
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await excel_agent.create_workbook(
            title=sample_xlsx_content["worksheets"][0]["name"],
            content=sample_xlsx_content
        )
        
        assert result["id"] == "test-workbook-id"
        assert result["name"] == "Test Workbook.xlsx"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_workbook(self, excel_agent, mock_graph_client):
        """Test obtención de libro de trabajo."""
        workbook_id = "test-workbook-id"
        mock_response = {
            "id": workbook_id,
            "name": "Test Workbook.xlsx",
            "worksheets": [{"name": "Sheet1"}]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await excel_agent.get_workbook(workbook_id)
        
        assert result["id"] == workbook_id
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_worksheet(self, excel_agent, mock_graph_client):
        """Test adición de hoja de trabajo."""
        workbook_id = "test-workbook-id"
        sheet_name = "New Sheet"
        
        mock_response = {
            "id": "sheet-id",
            "name": sheet_name,
            "position": 2
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await excel_agent.add_worksheet(
            workbook_id=workbook_id,
            sheet_name=sheet_name
        )
        
        assert result["name"] == sheet_name
        assert result["position"] == 2
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_worksheet(self, excel_agent, mock_graph_client):
        """Test eliminación de hoja de trabajo."""
        workbook_id = "test-workbook-id"
        sheet_id = "sheet-id"
        
        mock_response = {"status": "204"}
        mock_graph_client.delete.return_value = mock_response
        
        result = await excel_agent.delete_worksheet(
            workbook_id=workbook_id,
            sheet_id=sheet_id
        )
        
        assert result["status"] == "204"
        mock_graph_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_cell_value(self, excel_agent, mock_graph_client):
        """Test actualización de valor de celda."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        cell_address = "A1"
        value = "Test Value"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await excel_agent.update_cell_value(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            cell_address=cell_address,
            value=value
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cell_value(self, excel_agent, mock_graph_client):
        """Test obtención de valor de celda."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        cell_address = "A1"
        
        mock_response = {
            "value": "Test Value",
            "type": "String"
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await excel_agent.get_cell_value(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            cell_address=cell_address
        )
        
        assert result["value"] == "Test Value"
        assert result["type"] == "String"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_range_values(self, excel_agent, mock_graph_client):
        """Test actualización de rango de valores."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        range_address = "A1:C3"
        values = [
            ["Product", "Price", "Quantity"],
            ["Widget A", 10.99, 100],
            ["Widget B", 15.99, 50]
        ]
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await excel_agent.update_range_values(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            range_address=range_address,
            values=values
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_range_values(self, excel_agent, mock_graph_client):
        """Test obtención de rango de valores."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        range_address = "A1:C3"
        
        mock_response = {
            "value": [
                ["Product", "Price", "Quantity"],
                ["Widget A", 10.99, 100],
                ["Widget B", 15.99, 50]
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await excel_agent.get_range_values(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            range_address=range_address
        )
        
        assert len(result["value"]) == 3
        assert result["value"][0][0] == "Product"
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_formula(self, excel_agent, mock_graph_client):
        """Test adición de fórmula."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        cell_address = "D2"
        formula = "=B2*C2"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await excel_agent.add_formula(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            cell_address=cell_address,
            formula=formula
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_formula(self, excel_agent, mock_graph_client):
        """Test obtención de fórmula."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        cell_address = "D2"
        
        mock_response = {
            "formula": "=B2*C2",
            "value": 1099.0
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await excel_agent.get_formula(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            cell_address=cell_address
        )
        
        assert result["formula"] == "=B2*C2"
        assert result["value"] == 1099.0
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_format_cells(self, excel_agent, mock_graph_client):
        """Test formato de celdas."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        range_address = "A1:C3"
        format_options = {
            "number_format": "$#,##0.00",
            "font_color": "red",
            "background_color": "yellow",
            "bold": True,
            "italic": True
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await excel_agent.format_cells(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            range_address=range_address,
            **format_options
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_chart(self, excel_agent, mock_graph_client):
        """Test creación de gráfico."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        chart_data = {
            "type": "column",
            "data_range": "A1:C3",
            "title": "Product Sales",
            "position": "E2"
        }
        
        mock_response = {
            "id": "chart-1",
            "chartType": "columnChart",
            "name": "Product Sales"
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await excel_agent.create_chart(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            **chart_data
        )
        
        assert result["id"] == "chart-1"
        assert result["chartType"] == "columnChart"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_pivot_table(self, excel_agent, mock_graph_client):
        """Test creación de tabla dinámica."""
        workbook_id = "test-workbook-id"
        source_sheet = "Data"
        pivot_data = {
            "destination_range": "F2",
            "rows": ["Product"],
            "columns": ["Region"],
            "values": ["Sales"],
            "filters": ["Year"]
        }
        
        mock_response = {
            "id": "pivot-1",
            "name": "Sales Pivot Table"
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await excel_agent.create_pivot_table(
            workbook_id=workbook_id,
            source_sheet=source_sheet,
            **pivot_data
        )
        
        assert result["id"] == "pivot-1"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_data_validation(self, excel_agent, mock_graph_client):
        """Test adición de validación de datos."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        range_address = "A1:A10"
        validation_rule = {
            "type": "list",
            "formula1": "List1"
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await excel_agent.add_data_validation(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            range_address=range_address,
            validation_rule=validation_rule
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_protect_worksheet(self, excel_agent, mock_graph_client):
        """Test protección de hoja de trabajo."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        password = "sheet-password"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await excel_agent.protect_worksheet(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            password=password
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_unprotect_worksheet(self, excel_agent, mock_graph_client):
        """Test desprotección de hoja de trabajo."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        password = "sheet-password"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await excel_agent.unprotect_worksheet(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            password=password
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_conditional_formatting(self, excel_agent, mock_graph_client):
        """Test adición de formato condicional."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        range_address = "B2:B10"
        conditional_format = {
            "type": "colorScale",
            "criteria": {
                "min": {"type": "num", "value": 0},
                "max": {"type": "num", "value": 100}
            }
        }
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await excel_agent.add_conditional_formatting(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            range_address=range_address,
            conditional_format=conditional_format
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_workbook_statistics(self, excel_agent, mock_graph_client):
        """Test obtención de estadísticas del libro."""
        workbook_id = "test-workbook-id"
        mock_response = {
            "worksheets_count": 3,
            "total_cells": 1048576,
            "used_cells": 156,
            "formulas_count": 25,
            "charts_count": 2,
            "pivot_tables_count": 1
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await excel_agent.get_workbook_statistics(workbook_id)
        
        assert result["worksheets_count"] == 3
        assert result["used_cells"] == 156
        assert result["formulas_count"] == 25

    @pytest.mark.asyncio
    async def test_freeze_panes(self, excel_agent, mock_graph_client):
        """Test congelar paneles."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        freeze_range = "B2"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await excel_agent.freeze_panes(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            freeze_range=freeze_range
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_unfreeze_panes(self, excel_agent, mock_graph_client):
        """Test descongelar paneles."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await excel_agent.unfreeze_panes(
            workbook_id=workbook_id,
            sheet_name=sheet_name
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_merge_cells(self, excel_agent, mock_graph_client):
        """Test combinación de celdas."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        range_address = "A1:C1"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await excel_agent.merge_cells(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            range_address=range_address
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_unmerge_cells(self, excel_agent, mock_graph_client):
        """Test separación de celdas combinadas."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        range_address = "A1:C1"
        
        mock_response = {"status": "204"}
        mock_graph_client.patch.return_value = mock_response
        
        result = await excel_agent.unmerge_cells(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            range_address=range_address
        )
        
        assert result["status"] == "204"
        mock_graph_client.patch.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_comment(self, excel_agent, mock_graph_client):
        """Test adición de comentario."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        cell_address = "A1"
        comment_text = "This cell needs review"
        
        mock_response = {"status": "201"}
        mock_graph_client.post.return_value = mock_response
        
        result = await excel_agent.add_comment(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            cell_address=cell_address,
            comment_text=comment_text
        )
        
        assert result["status"] == "201"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_in_workbook(self, excel_agent, mock_graph_client):
        """Test búsqueda en libro de trabajo."""
        workbook_id = "test-workbook-id"
        search_term = "Total"
        
        mock_response = {
            "matches": [
                {
                    "address": "D5",
                    "value": "Total Sales",
                    "sheet": "Summary"
                },
                {
                    "address": "F10",
                    "value": "Monthly Total",
                    "sheet": "Details"
                }
            ]
        }
        mock_graph_client.get.return_value = mock_response
        
        result = await excel_agent.search_in_workbook(
            workbook_id=workbook_id,
            search_term=search_term
        )
        
        assert len(result["matches"]) == 2
        assert all("address" in match for match in result["matches"])

    @pytest.mark.asyncio
    async def test_export_to_pdf(self, excel_agent, mock_graph_client):
        """Test exportación a PDF."""
        workbook_id = "test-workbook-id"
        
        mock_response = {"@microsoft.graph.downloadUrl": "https://download-url.pdf"}
        mock_graph_client.get.return_value = mock_response
        
        result = await excel_agent.export_to_pdf(workbook_id)
        
        assert "@microsoft.graph.downloadUrl" in result
        mock_graph_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_share_workbook(self, excel_agent, mock_graph_client):
        """Test compartir libro de trabajo."""
        workbook_id = "test-workbook-id"
        user_email = "user@example.com"
        permission = "read"
        
        mock_response = {"status": "201"}
        mock_graph_client.post.return_value = mock_response
        
        result = await excel_agent.share_workbook(
            workbook_id=workbook_id,
            user_email=user_email,
            permission=permission
        )
        
        assert result["status"] == "201"
        mock_graph_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_network_error(self, excel_agent, error_scenarios):
        """Test manejo de errores de red."""
        excel_agent.graph_client.get.side_effect = error_scenarios["network_error"]
        
        with pytest.raises(Exception) as exc_info:
            await excel_agent.get_workbook("test-workbook-id")
        
        assert "Network error" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_error_handling_invalid_formula(self, excel_agent, mock_graph_client):
        """Test manejo de fórmulas inválidas."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        invalid_formula = "=INVALID_FORMULA"
        
        mock_graph_client.patch.side_effect = Exception("Invalid formula")
        
        with pytest.raises(Exception) as exc_info:
            await excel_agent.add_formula(
                workbook_id=workbook_id,
                sheet_name=sheet_name,
                cell_address="A1",
                formula=invalid_formula
            )
        
        assert "Invalid formula" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, excel_agent, rate_limit_responses):
        """Test manejo de rate limiting."""
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return rate_limit_responses["rate_limited"]
            return rate_limit_responses["success"]
        
        excel_agent.graph_client.get.side_effect = side_effect
        
        with patch.object(excel_agent, '_retry_with_backoff') as mock_retry:
            mock_retry.return_value = rate_limit_responses["success"]
            
            result = await excel_agent.get_workbook("test-workbook-id")
            
            assert mock_retry.called

    @pytest.mark.asyncio
    async def test_batch_cell_updates(self, excel_agent, mock_graph_client):
        """Test actualización de celdas en lote."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        updates = [
            {"cell": "A1", "value": "Product"},
            {"cell": "B1", "value": "Price"},
            {"cell": "C1", "value": "Quantity"}
        ]
        
        mock_responses = [
            {"status": "204"},
            {"status": "204"},
            {"status": "204"}
        ]
        mock_graph_client.batch_request.return_value = mock_responses
        
        results = await excel_agent.batch_cell_updates(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            updates=updates
        )
        
        assert len(results) == 3
        assert all(r["status"] == "204" for r in results)

    @pytest.mark.asyncio
    async def test_data_analysis_functions(self, excel_agent, mock_graph_client):
        """Test funciones de análisis de datos."""
        workbook_id = "test-workbook-id"
        sheet_name = "Sheet1"
        data_range = "A1:C10"
        
        # Test SUM function
        mock_graph_client.post.return_value = {"result": 1500}
        
        result = await excel_agent.apply_function(
            workbook_id=workbook_id,
            sheet_name=sheet_name,
            function="SUM",
            range_address=data_range,
            output_cell="D1"
        )
        
        assert "result" in result

    @pytest.mark.asyncio
    async def test_import_external_data(self, excel_agent, mock_graph_client):
        """Test importación de datos externos."""
        workbook_id = "test-workbook-id"
        data_source = {
            "type": "web",
            "url": "https://api.example.com/data"
        }
        
        mock_response = {
            "id": "import-1",
            "status": "completed",
            "rows_imported": 100
        }
        mock_graph_client.post.return_value = mock_response
        
        result = await excel_agent.import_external_data(
            workbook_id=workbook_id,
            data_source=data_source
        )
        
        assert result["status"] == "completed"
        assert result["rows_imported"] == 100
        mock_graph_client.post.assert_called_once()