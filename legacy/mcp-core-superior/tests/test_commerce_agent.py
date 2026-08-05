"""
Tests unitarios para Commerce Agent
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import sys
import os

# Añadir el directorio padre al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.commerce_agent import (
    CommerceAgent, Product, Order, Customer, InventoryItem,
    Payment, CommercePlatform, OrderStatus, PaymentStatus
)


class TestCommerceAgent:
    """Tests para CommerceAgent"""
    
    @pytest.fixture
    async def agent(self):
        """Fixture para crear agente de prueba"""
        agent = CommerceAgent()
        await agent._initialize()
        return agent
    
    def test_agent_initialization(self, agent):
        """Test inicialización del agente"""
        assert agent.agent_name == "CommerceAgent"
        assert agent.is_ready
        assert len(agent.capabilities) > 0
        assert len(agent._products) > 0  # Debe cargar productos de ejemplo
        assert len(agent._orders) > 0  # Debe cargar órdenes de ejemplo
        assert len(agent._customers) > 0  # Debe cargar clientes de ejemplo
    
    @pytest.mark.asyncio
    async def test_create_product_basic(self, agent):
        """Test creación básica de producto"""
        product_data = {
            "name": "Producto Test",
            "description": "Descripción del producto",
            "price": 99.99,
            "category": "Electrónicos",
            "platform": "shopify"
        }
        
        product = await agent.create_product(**product_data)
        
        assert isinstance(product, Product)
        assert product.name == product_data["name"]
        assert product.price == product_data["price"]
        assert product.platform == CommercePlatform.SHOPIFY
        assert product.status == "active"
    
    @pytest.mark.asyncio
    async def test_create_product_wrong_platform(self, agent):
        """Test creación de producto con plataforma inválida"""
        product_data = {
            "name": "Producto Test",
            "description": "Descripción",
            "price": 99.99,
            "platform": "invalid_platform"
        }
        
        with pytest.raises(ValueError, match="Plataforma no soportada"):
            await agent.create_product(**product_data)
    
    @pytest.mark.asyncio
    async def test_update_product_price(self, agent):
        """Test actualización de precio de producto"""
        # Crear producto primero
        product_data = {
            "name": "Producto Precio",
            "description": "Producto para test",
            "price": 50.00,
            "category": "Test",
            "platform": "shopify"
        }
        
        product = await agent.create_product(**product_data)
        new_price = 75.00
        
        updated_product = await agent.update_product_price(product.id, new_price)
        
        assert updated_product.price == new_price
        assert updated_product.last_updated is not None
    
    @pytest.mark.asyncio
    async def test_update_product_nonexistent(self, agent):
        """Test actualización de producto inexistente"""
        with pytest.raises(ValueError, match="Producto no encontrado"):
            await agent.update_product_price("nonexistent_id", 50.00)
    
    @pytest.mark.asyncio
    async def test_delete_product(self, agent):
        """Test eliminación de producto"""
        # Crear producto primero
        product_data = {
            "name": "Producto a Eliminar",
            "description": "Producto para eliminar",
            "price": 25.00,
            "platform": "woocommerce"
        }
        
        product = await agent.create_product(**product_data)
        product_id = product.id
        
        result = await agent.delete_product(product_id)
        assert result == True
        
        # Verificar que ya no existe
        products = await agent.search_products("Producto a Eliminar")
        assert not any(p.id == product_id for p in products)
    
    @pytest.mark.asyncio
    async def test_search_products_basic(self, agent):
        """Test búsqueda básica de productos"""
        products = await agent.search_products("laptop")
        
        assert isinstance(products, list)
        # Debe retornar productos que coincidan con la búsqueda
        if products:
            product = products[0]
            assert isinstance(product, Product)
    
    @pytest.mark.asyncio
    async def test_search_products_by_category(self, agent):
        """Test búsqueda de productos por categoría"""
        products = await agent.search_products_by_category("Electrónicos")
        
        assert isinstance(products, list)
        if products:
            product = products[0]
            assert product.category == "Electrónicos"
    
    @pytest.mark.asyncio
    async def test_get_product_details(self, agent):
        """Test obtención de detalles de producto"""
        # Usar un producto existente del setup
        first_product = agent._products[0]
        product = await agent.get_product_details(first_product.id)
        
        assert isinstance(product, Product)
        assert product.id == first_product.id
        assert product.name is not None
        assert product.price is not None
    
    @pytest.mark.asyncio
    async def test_get_product_details_nonexistent(self, agent):
        """Test obtención de detalles de producto inexistente"""
        with pytest.raises(ValueError, match="Producto no encontrado"):
            await agent.get_product_details("nonexistent_id")
    
    @pytest.mark.asyncio
    async def test_process_order_basic(self, agent):
        """Test procesamiento básico de orden"""
        order_data = {
            "customer_id": agent._customers[0].id,
            "items": [
                {
                    "product_id": agent._products[0].id,
                    "quantity": 2,
                    "price": agent._products[0].price
                }
            ],
            "total": agent._products[0].price * 2,
            "platform": "shopify"
        }
        
        order = await agent.process_order(**order_data)
        
        assert isinstance(order, Order)
        assert order.status == OrderStatus.PENDING
        assert order.total == order_data["total"]
        assert order.platform == CommercePlatform.SHOPIFY
        assert order.customer_id == order_data["customer_id"]
    
    @pytest.mark.asyncio
    async def test_process_order_invalid_customer(self, agent):
        """Test procesamiento de orden con cliente inválido"""
        order_data = {
            "customer_id": "invalid_customer_id",
            "items": [
                {
                    "product_id": agent._products[0].id,
                    "quantity": 1,
                    "price": 50.00
                }
            ],
            "total": 50.00,
            "platform": "shopify"
        }
        
        with pytest.raises(ValueError, match="Cliente no encontrado"):
            await agent.process_order(**order_data)
    
    @pytest.mark.asyncio
    async def test_update_order_status(self, agent):
        """Test actualización de estado de orden"""
        # Crear orden primero
        order_data = {
            "customer_id": agent._customers[0].id,
            "items": [
                {
                    "product_id": agent._products[0].id,
                    "quantity": 1,
                    "price": 25.00
                }
            ],
            "total": 25.00,
            "platform": "woocommerce"
        }
        
        order = await agent.process_order(**order_data)
        new_status = OrderStatus.SHIPPED
        
        updated_order = await agent.update_order_status(order.id, new_status)
        
        assert updated_order.status == new_status
        assert updated_order.updated_at is not None
    
    @pytest.mark.asyncio
    async def test_cancel_order(self, agent):
        """Test cancelación de orden"""
        # Crear orden pendiente
        order_data = {
            "customer_id": agent._customers[0].id,
            "items": [
                {
                    "product_id": agent._products[0].id,
                    "quantity": 1,
                    "price": 30.00
                }
            ],
            "total": 30.00,
            "platform": "shopify"
        }
        
        order = await agent.process_order(**order_data)
        
        result = await agent.cancel_order(order.id)
        assert result == True
        
        # Verificar que el estado cambió
        orders = await agent.get_order_status(order.id)
        assert orders.status == OrderStatus.CANCELLED
    
    @pytest.mark.asyncio
    async def test_get_order_status(self, agent):
        """Test obtención de estado de orden"""
        first_order = agent._orders[0]
        order = await agent.get_order_status(first_order.id)
        
        assert isinstance(order, Order)
        assert order.id == first_order.id
        assert order.status is not None
    
    @pytest.mark.asyncio
    async def test_get_customer_orders(self, agent):
        """Test obtención de órdenes por cliente"""
        customer_id = agent._customers[0].id
        orders = await agent.get_customer_orders(customer_id)
        
        assert isinstance(orders, list)
        # Todas las órdenes deben pertenecer al cliente
        for order in orders:
            assert order.customer_id == customer_id
    
    @pytest.mark.asyncio
    async def test_manage_inventory_add_stock(self, agent):
        """Test gestión de inventario - agregar stock"""
        # Crear producto primero
        product_data = {
            "name": "Producto Inventario",
            "description": "Producto para inventario",
            "price": 40.00,
            "platform": "shopify"
        }
        
        product = await agent.create_product(**product_data)
        additional_stock = 50
        
        result = await agent.manage_inventory(product.id, "add", additional_stock)
        
        assert result == True
        # Verificar que el stock se actualizó
        updated_product = await agent.get_product_details(product.id)
        assert updated_product.stock >= additional_stock
    
    @pytest.mark.asyncio
    async def test_manage_inventory_remove_stock(self, agent):
        """Test gestión de inventario - remover stock"""
        product_id = agent._products[0].id
        initial_stock = agent._products[0].stock
        remove_amount = 5
        
        result = await agent.manage_inventory(product_id, "remove", remove_amount)
        
        assert result == True
        # Verificar que el stock se redujo
        updated_product = await agent.get_product_details(product_id)
        assert updated_product.stock == initial_stock - remove_amount
    
    @pytest.mark.asyncio
    async def test_manage_inventory_invalid_operation(self, agent):
        """Test gestión de inventario con operación inválida"""
        product_id = agent._products[0].id
        
        with pytest.raises(ValueError, match="Operación no válida"):
            await agent.manage_inventory(product_id, "invalid_op", 10)
    
    @pytest.mark.asyncio
    async def test_process_payment_stripe_success(self, agent):
        """Test procesamiento de pago exitoso con Stripe"""
        payment_data = {
            "order_id": agent._orders[0].id,
            "amount": agent._orders[0].total,
            "currency": "USD",
            "payment_method": "stripe",
            "customer_id": agent._customers[0].id
        }
        
        payment = await agent.process_payment(**payment_data)
        
        assert isinstance(payment, Payment)
        assert payment.amount == payment_data["amount"]
        assert payment.status == PaymentStatus.COMPLETED
        assert payment.payment_method == "stripe"
    
    @pytest.mark.asyncio
    async def test_process_payment_paypal_success(self, agent):
        """Test procesamiento de pago exitoso con PayPal"""
        payment_data = {
            "order_id": agent._orders[1].id,
            "amount": agent._orders[1].total,
            "currency": "USD",
            "payment_method": "paypal",
            "customer_id": agent._customers[1].id
        }
        
        payment = await agent.process_payment(**payment_data)
        
        assert isinstance(payment, Payment)
        assert payment.payment_method == "paypal"
        assert payment.status == PaymentStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_process_payment_invalid_method(self, agent):
        """Test procesamiento de pago con método inválido"""
        payment_data = {
            "order_id": agent._orders[0].id,
            "amount": 50.00,
            "currency": "USD",
            "payment_method": "invalid_method",
            "customer_id": agent._customers[0].id
        }
        
        with pytest.raises(ValueError, match="Método de pago no soportado"):
            await agent.process_payment(**payment_data)
    
    @pytest.mark.asyncio
    async def test_get_payment_status(self, agent):
        """Test obtención de estado de pago"""
        first_order = agent._orders[0]
        payment = await agent.get_payment_status(first_order.id)
        
        assert isinstance(payment, Payment)
        assert payment.order_id == first_order.id
    
    @pytest.mark.asyncio
    async def test_get_sales_report_basic(self, agent):
        """Test obtención de reporte de ventas básico"""
        # Usar datos de ejemplo del agente
        report = await agent.get_sales_report("2024-01-01", "2024-12-31")
        
        assert "total_sales" in report
        assert "total_orders" in report
        assert "average_order_value" in report
        assert "top_products" in report
        assert "revenue_by_platform" in report
        
        assert isinstance(report["total_sales"], (int, float))
        assert isinstance(report["total_orders"], int)
        assert isinstance(report["average_order_value"], (int, float))
    
    @pytest.mark.asyncio
    async def test_get_sales_report_invalid_dates(self, agent):
        """Test reporte de ventas con fechas inválidas"""
        with pytest.raises(ValueError, match="Formato de fecha inválido"):
            await agent.get_sales_report("invalid_date", "2024-12-31")
    
    @pytest.mark.asyncio
    async def test_add_customer(self, agent):
        """Test agregar nuevo cliente"""
        customer_data = {
            "name": "Cliente Test",
            "email": "test@example.com",
            "phone": "+1234567890",
            "address": "123 Test St",
            "platform": "shopify"
        }
        
        customer = await agent.add_customer(**customer_data)
        
        assert isinstance(customer, Customer)
        assert customer.name == customer_data["name"]
        assert customer.email == customer_data["email"]
        assert customer.platform == CommercePlatform.SHOPIFY
    
    @pytest.mark.asyncio
    async def test_get_customer_profile(self, agent):
        """Test obtención de perfil de cliente"""
        first_customer = agent._customers[0]
        customer = await agent.get_customer_profile(first_customer.id)
        
        assert isinstance(customer, Customer)
        assert customer.id == first_customer.id
        assert customer.name is not None
        assert customer.email is not None
    
    @pytest.mark.asyncio
    async def test_get_low_stock_products(self, agent):
        """Test obtención de productos con stock bajo"""
        products = await agent.get_low_stock_products(threshold=10)
        
        assert isinstance(products, list)
        # Todos los productos retornados deben tener stock bajo
        for product in products:
            assert product.stock <= 10
    
    @pytest.mark.asyncio
    async def test_get_inventory_value(self, agent):
        """Test cálculo del valor total del inventario"""
        inventory_value = await agent.get_inventory_value()
        
        assert isinstance(inventory_value, (int, float))
        assert inventory_value > 0  # Debe tener algún valor de inventario
    
    @pytest.mark.asyncio
    async def test_promote_product(self, agent):
        """Test promoción de producto"""
        product_id = agent._products[0].id
        discount_percentage = 20
        
        result = await agent.promote_product(product_id, discount_percentage)
        
        assert result == True
        
        # Verificar que el producto tiene promoción activa
        product = await agent.get_product_details(product_id)
        assert product.promotion is not None
        assert product.promotion.discount_percentage == discount_percentage
    
    @pytest.mark.asyncio
    async def test_remove_product_promotion(self, agent):
        """Test remover promoción de producto"""
        product_id = agent._products[0].id
        
        # Primero agregar promoción
        await agent.promote_product(product_id, 15)
        
        # Luego removerla
        result = await agent.remove_product_promotion(product_id)
        
        assert result == True
        
        # Verificar que ya no tiene promoción
        product = await agent.get_product_details(product_id)
        assert product.promotion is None
    
    @pytest.mark.asyncio
    async def test_get_promotional_products(self, agent):
        """Test obtención de productos en promoción"""
        # Agregar promoción a algunos productos
        for i in range(min(2, len(agent._products))):
            await agent.promote_product(agent._products[i].id, 10 + i * 5)
        
        products = await agent.get_promotional_products()
        
        assert isinstance(products, list)
        # Todos los productos retornados deben tener promoción activa
        for product in products:
            assert product.promotion is not None
    
    def test_get_supported_platforms(self, agent):
        """Test obtención de plataformas soportadas"""
        platforms = agent.get_supported_platforms()
        
        assert isinstance(platforms, list)
        assert CommercePlatform.SHOPIFY in platforms
        assert CommercePlatform.WOOCOMMERCE in platforms
        assert CommercePlatform.MAGENTO in platforms
    
    @pytest.mark.asyncio
    async def test_sync_inventory(self, agent):
        """Test sincronización de inventario"""
        result = await agent.sync_inventory("shopify")
        
        assert isinstance(result, dict)
        assert "synced_products" in result
        assert "updated_stock" in result
        assert isinstance(result["synced_products"], int)
        assert isinstance(result["updated_stock"], int)
    
    @pytest.mark.asyncio
    async def test_bulk_update_prices(self, agent):
        """Test actualización masiva de precios"""
        # Seleccionar algunos productos
        product_ids = [p.id for p in agent._products[:2]]
        price_updates = {pid: 99.99 for pid in product_ids}
        
        result = await agent.bulk_update_prices(price_updates)
        
        assert result == True
        
        # Verificar que los precios se actualizaron
        for product_id in product_ids:
            product = await agent.get_product_details(product_id)
            assert product.price == 99.99
    
    @pytest.mark.asyncio
    async def test_handle_exceptions_invalid_operation(self, agent):
        """Test manejo de excepciones con operación inválida"""
        # Intentar una operación que debería generar excepción
        with pytest.raises(Exception):  # Cualquier excepción es válida para este test
            await agent.create_product(
                name="",
                description="",
                price=-10,  # Precio inválido
                platform="shopify"
            )
    
    @pytest.mark.asyncio
    async def test_handle_exceptions_network_error(self, agent):
        """Test manejo de excepciones de red"""
        # Simular un error de red mockeando requests
        with patch('agents.commerce_agent.requests.post') as mock_post:
            mock_post.side_effect = Exception("Error de red simulado")
            
            with pytest.raises(Exception):
                await agent.create_product(
                    name="Test Product",
                    description="Test Description",
                    price=50.00,
                    platform="shopify"
                )


class TestCommerceDataClasses:
    """Tests para las clases de datos del agente de comercio"""
    
    def test_product_creation(self):
        """Test creación de objeto Product"""
        product = Product(
            id="test_id",
            name="Test Product",
            description="Test Description",
            price=99.99,
            category="Test Category",
            stock=10,
            platform=CommercePlatform.SHOPIFY,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status="active"
        )
        
        assert product.id == "test_id"
        assert product.name == "Test Product"
        assert product.price == 99.99
        assert product.platform == CommercePlatform.SHOPIFY
    
    def test_order_creation(self):
        """Test creación de objeto Order"""
        order = Order(
            id="order_test",
            customer_id="customer_test",
            items=[],
            total=150.00,
            status=OrderStatus.PENDING,
            created_at=datetime.now(),
            platform=CommercePlatform.WOOCOMMERCE,
            shipping_address="123 Test St"
        )
        
        assert order.id == "order_test"
        assert order.customer_id == "customer_test"
        assert order.total == 150.00
        assert order.status == OrderStatus.PENDING
    
    def test_customer_creation(self):
        """Test creación de objeto Customer"""
        customer = Customer(
            id="customer_test",
            name="Test Customer",
            email="test@example.com",
            phone="+1234567890",
            address="123 Test St",
            platform=CommercePlatform.SHOPIFY,
            created_at=datetime.now(),
            order_history=[]
        )
        
        assert customer.id == "customer_test"
        assert customer.name == "Test Customer"
        assert customer.email == "test@example.com"
    
    def test_payment_creation(self):
        """Test creación de objeto Payment"""
        payment = Payment(
            id="payment_test",
            order_id="order_test",
            amount=99.99,
            currency="USD",
            payment_method="stripe",
            status=PaymentStatus.PENDING,
            transaction_id="txn_test",
            created_at=datetime.now()
        )
        
        assert payment.id == "payment_test"
        assert payment.order_id == "order_test"
        assert payment.amount == 99.99
        assert payment.status == PaymentStatus.PENDING


if __name__ == "__main__":
    # Ejecutar tests específicos si se ejecuta directamente
    pytest.main([__file__, "-v"])