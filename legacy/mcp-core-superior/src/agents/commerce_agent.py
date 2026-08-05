"""
Commerce Agent MCP - Agente de Comercio Electrónico
Integra con plataformas de e-commerce para búsqueda de productos,
comparación de precios, gestión de carritos y procesamiento de checkout.

Autor: Commerce Agent
Versión: 1.0.0
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Set
from dataclasses import dataclass, field
from enum import Enum
import random
import uuid

# Importar la estructura base del agente MCP
try:
    from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
except ImportError:
    BaseAgentWrapper = object
    AgentCapability = None


class EcommercePlatform(Enum):
    """Plataformas de e-commerce soportadas"""
    AMAZON = "amazon"
    EBAY = "ebay"
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    MAGENTO = "magento"
    ETSY = "etsy"
    ALIEXPRESS = "aliexpress"
    WALMART = "walmart"


class ProductCategory(Enum):
    """Categorías de productos"""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    HOME_GARDEN = "home_garden"
    SPORTS = "sports"
    BOOKS = "books"
    BEAUTY = "beauty"
    AUTOMOTIVE = "automotive"
    TOYS = "toys"
    FOOD_BEVERAGE = "food_beverage"
    HEALTH = "health"


class CartStatus(Enum):
    """Estados del carrito"""
    ACTIVE = "active"
    ABANDONED = "abandoned"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class Product:
    """Estructura de datos para productos"""
    id: str
    name: str
    description: str
    category: ProductCategory
    price: float
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    currency: str = "EUR"
    availability: str = "in_stock"
    rating: Optional[float] = None
    review_count: int = 0
    brand: Optional[str] = None
    images: List[str] = field(default_factory=list)
    specifications: Dict[str, Any] = field(default_factory=dict)
    seller_info: Dict[str, str] = field(default_factory=dict)
    shipping_info: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class CartItem:
    """Elemento del carrito"""
    product: Product
    quantity: int
    added_at: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None


@dataclass
class ShoppingCart:
    """Carrito de compras"""
    id: str
    items: List[CartItem] = field(default_factory=list)
    status: CartStatus = CartStatus.ACTIVE
    subtotal: float = 0.0
    shipping_cost: float = 0.0
    tax_amount: float = 0.0
    total: float = 0.0
    discount_code: Optional[str] = None
    discount_amount: float = 0.0
    customer_info: Dict[str, str] = field(default_factory=dict)
    shipping_address: Dict[str, str] = field(default_factory=dict)
    payment_method: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Order:
    """Orden de compra"""
    id: str
    cart_id: str
    customer_info: Dict[str, str]
    items: List[Dict[str, Any]] = field(default_factory=list)
    subtotal: float
    shipping_cost: float
    tax_amount: float
    total: float
    status: str = "pending"
    payment_status: str = "pending"
    payment_method: str = ""
    shipping_address: Dict[str, str]
    tracking_number: Optional[str] = None
    estimated_delivery: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


@dataclass
class CommerceResponse:
    """Respuesta consolidada de comercio"""
    success: bool
    transaction_id: str
    action: str
    timestamp: float
    execution_time: float
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class CommerceAgent(BaseAgentWrapper if BaseAgentWrapper else object):
    """
    Agente de Comercio Electrónico que maneja búsqueda de productos,
    comparación de precios, gestión de carritos y procesamiento de órdenes.
    """
    
    def __init__(self):
        if BaseAgentWrapper:
            super().__init__(
                agent_name="CommerceAgent",
                capabilities=[
                    AgentCapability.PRODUCT_SEARCH if AgentCapability else "product_search",
                    AgentCapability.PRICE_COMPARISON if AgentCapability else "price_comparison",
                    AgentCapability.ECOMMERCE_INTEGRATION if AgentCapability else "ecommerce_integration",
                    AgentCapability.CART_MANAGEMENT if AgentCapability else "cart_management",
                    AgentCapability.CHECKOUT_PROCESSING if AgentCapability else "checkout_processing",
                ],
                max_concurrent=6,
                timeout_seconds=45,
                retry_attempts=2
            )
        
        self.logger = logging.getLogger(__name__)
        self._products: Dict[str, Product] = {}
        self._carts: Dict[str, ShoppingCart] = {}
        self._orders: Dict[str, Order] = {}
        self._price_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # APIs simuladas
        self.platform_apis = {
            EcommercePlatform.AMAZON: {"api_key": "***", "base_url": "https://api.amazon.com"},
            EcommercePlatform.EBAY: {"api_key": "***", "base_url": "https://api.ebay.com"},
            EcommercePlatform.SHOPIFY: {"api_key": "***", "base_url": "https://api.shopify.com"},
        }
        
        # Cargar productos de ejemplo
        self._load_sample_products()
    
    async def _initialize(self):
        """Inicialización específica del agente"""
        await asyncio.sleep(0.1)
        self.logger.info("Commerce Agent inicializado")
    
    def _load_sample_products(self):
        """Cargar productos de ejemplo"""
        sample_products = [
            Product(
                id="prod_1",
                name="iPhone 15 Pro",
                description="Último smartphone de Apple con chip A17 Pro",
                category=ProductCategory.ELECTRONICS,
                price=1199.99,
                original_price=1299.99,
                discount_percentage=7.7,
                rating=4.8,
                review_count=2847,
                brand="Apple",
                images=["https://example.com/iphone15pro.jpg"],
                specifications={"screen": "6.1 pulgadas", "storage": "256GB", "camera": "48MP"},
                seller_info={"name": "Apple Store", "rating": 4.9},
                shipping_info={"free_shipping": True, "delivery_days": "1-2"},
                tags=["smartphone", "apple", "premium"]
            ),
            Product(
                id="prod_2",
                name="Samsung Galaxy S24 Ultra",
                description="Smartphone Android premium con S Pen integrado",
                category=ProductCategory.ELECTRONICS,
                price=1299.99,
                rating=4.7,
                review_count=1923,
                brand="Samsung",
                images=["https://example.com/galaxyS24.jpg"],
                specifications={"screen": "6.8 pulgadas", "storage": "512GB", "camera": "200MP"},
                seller_info={"name": "Samsung Official", "rating": 4.8},
                shipping_info={"free_shipping": True, "delivery_days": "1-3"},
                tags=["smartphone", "samsung", "android", "spen"]
            ),
            Product(
                id="prod_3",
                name="Zapatillas Nike Air Max",
                description="Zapatillas deportivas con tecnología Air Max",
                category=ProductCategory.CLOTHING,
                price=129.99,
                original_price=159.99,
                discount_percentage=18.8,
                rating=4.5,
                review_count=854,
                brand="Nike",
                images=["https://example.com/nike-airmax.jpg"],
                specifications={"size": "36-46", "color": "Varios", "material": "Mesh/Synthetic"},
                seller_info={"name": "Nike Official", "rating": 4.7},
                shipping_info={"free_shipping": True, "delivery_days": "2-5"},
                tags=["zapatillas", "nike", "deportivas"]
            ),
            Product(
                id="prod_4",
                name="Laptop Dell XPS 13",
                description="Laptop ultradelgada con procesador Intel Core i7",
                category=ProductCategory.ELECTRONICS,
                price=999.99,
                rating=4.6,
                review_count=1247,
                brand="Dell",
                images=["https://example.com/dell-xps13.jpg"],
                specifications={"processor": "Intel i7", "ram": "16GB", "storage": "512GB SSD"},
                seller_info={"name": "Dell Official", "rating": 4.5},
                shipping_info={"free_shipping": True, "delivery_days": "3-5"},
                tags=["laptop", "dell", "ultrabook", "intel"]
            )
        ]
        
        for product in sample_products:
            self._products[product.id] = product
            
            # Simular historial de precios
            self._price_history[product.id] = []
            for i in range(30):
                price_variation = random.uniform(-0.1, 0.1)
                historical_price = product.price * (1 + price_variation)
                self._price_history[product.id].append({
                    "date": (datetime.now() - timedelta(days=i)).isoformat(),
                    "price": round(historical_price, 2),
                    "currency": product.currency
                })
    
    async def search_products(
        self,
        query: str,
        category: Optional[ProductCategory] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        brands: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        platform: Optional[EcommercePlatform] = None,
        limit: int = 20
    ) -> CommerceResponse:
        """Buscar productos"""
        start_time = time.time()
        
        try:
            results = []
            
            for product in self._products.values():
                # Aplicar filtros
                if category and product.category != category:
                    continue
                
                if min_price and product.price < min_price:
                    continue
                
                if max_price and product.price > max_price:
                    continue
                
                if brands and product.brand not in brands:
                    continue
                
                if min_rating and (not product.rating or product.rating < min_rating):
                    continue
                
                # Buscar en nombre, descripción y tags
                searchable_text = f"{product.name} {product.description} {' '.join(product.tags)}".lower()
                if query.lower() in searchable_text:
                    results.append(product)
                
                # Limitar resultados
                if len(results) >= limit:
                    break
            
            self.logger.info(f"Búsqueda completada: {len(results)} productos encontrados")
            
            return CommerceResponse(
                success=True,
                transaction_id="search_results",
                action="search_products",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                details={
                    "query": query,
                    "products_found": len(results),
                    "filters_applied": {
                        "category": category.value if category else None,
                        "price_range": [min_price, max_price],
                        "brands": brands,
                        "min_rating": min_rating
                    },
                    "products": [self._product_to_dict(p) for p in results]
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error buscando productos: {str(e)}")
            return CommerceResponse(
                success=False,
                transaction_id="",
                action="search_products",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def compare_prices(
        self,
        product_query: str,
        platforms: Optional[List[EcommercePlatform]] = None
    ) -> CommerceResponse:
        """Comparar precios en múltiples plataformas"""
        start_time = time.time()
        
        try:
            if not platforms:
                platforms = list(EcommercePlatform)
            
            comparison_results = []
            
            # Simular búsqueda en diferentes plataformas
            for platform in platforms:
                # Buscar producto similar en la plataforma
                found_products = []
                for product in self._products.values():
                    searchable_text = f"{product.name} {product.description}".lower()
                    if product_query.lower() in searchable_text:
                        found_products.append(product)
                
                if found_products:
                    # Tomar el primer producto como referencia
                    base_product = found_products[0]
                    
                    # Simular variación de precio por plataforma
                    price_variation = random.uniform(-0.15, 0.25)
                    platform_price = base_product.price * (1 + price_variation)
                    
                    comparison_results.append({
                        "platform": platform.value,
                        "product_name": base_product.name,
                        "price": round(platform_price, 2),
                        "original_price": round(base_product.original_price * (1 + price_variation), 2) if base_product.original_price else None,
                        "currency": base_product.currency,
                        "availability": base_product.availability,
                        "shipping": f"Envío {'gratis' if random.choice([True, False]) else 'pago'}",
                        "delivery_time": f"{random.randint(1, 7)} días",
                        "seller_rating": round(random.uniform(3.5, 5.0), 1)
                    })
            
            # Ordenar por precio
            comparison_results.sort(key=lambda x: x["price"])
            
            # Calcular estadísticas
            prices = [r["price"] for r in comparison_results]
            price_stats = {
                "lowest_price": min(prices),
                "highest_price": max(prices),
                "average_price": round(sum(prices) / len(prices), 2),
                "price_spread": round(max(prices) - min(prices), 2)
            }
            
            return CommerceResponse(
                success=True,
                transaction_id="price_comparison",
                action="compare_prices",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                details={
                    "product_query": product_query,
                    "platforms_compared": len(comparison_results),
                    "comparison_results": comparison_results,
                    "price_statistics": price_stats,
                    "best_deal": comparison_results[0] if comparison_results else None
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error comparando precios: {str(e)}")
            return CommerceResponse(
                success=False,
                transaction_id="",
                action="compare_prices",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def create_cart(self, customer_info: Dict[str, str]) -> CommerceResponse:
        """Crear nuevo carrito de compras"""
        start_time = time.time()
        
        try:
            cart_id = f"cart_{str(uuid.uuid4())[:8]}"
            
            cart = ShoppingCart(
                id=cart_id,
                customer_info=customer_info
            )
            
            self._carts[cart_id] = cart
            
            self.logger.info(f"Carrito creado: {cart_id}")
            
            return CommerceResponse(
                success=True,
                transaction_id=cart_id,
                action="create_cart",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                details={
                    "cart_id": cart_id,
                    "customer_email": customer_info.get("email", "N/A"),
                    "items_count": len(cart.items)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error creando carrito: {str(e)}")
            return CommerceResponse(
                success=False,
                transaction_id="",
                action="create_cart",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def add_to_cart(
        self,
        cart_id: str,
        product_id: str,
        quantity: int = 1,
        notes: Optional[str] = None
    ) -> CommerceResponse:
        """Agregar producto al carrito"""
        start_time = time.time()
        
        try:
            if cart_id not in self._carts:
                raise ValueError(f"Carrito no encontrado: {cart_id}")
            
            if product_id not in self._products:
                raise ValueError(f"Producto no encontrado: {product_id}")
            
            cart = self._carts[cart_id]
            product = self._products[product_id]
            
            # Verificar si el producto ya está en el carrito
            existing_item = None
            for item in cart.items:
                if item.product.id == product_id:
                    existing_item = item
                    break
            
            if existing_item:
                # Incrementar cantidad
                existing_item.quantity += quantity
            else:
                # Agregar nuevo item
                cart_item = CartItem(
                    product=product,
                    quantity=quantity,
                    notes=notes
                )
                cart.items.append(cart_item)
            
            # Recalcular totales
            self._update_cart_totals(cart)
            cart.updated_at = datetime.now()
            
            self.logger.info(f"Producto agregado al carrito: {product_id}")
            
            return CommerceResponse(
                success=True,
                transaction_id=cart_id,
                action="add_to_cart",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                details={
                    "product_name": product.name,
                    "quantity": quantity,
                    "cart_total": cart.total,
                    "items_count": len(cart.items)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error agregando al carrito: {str(e)}")
            return CommerceResponse(
                success=False,
                transaction_id=cart_id,
                action="add_to_cart",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def _update_cart_totals(self, cart: ShoppingCart):
        """Actualizar totales del carrito"""
        cart.subtotal = sum(item.product.price * item.quantity for item in cart.items)
        
        # Simular cálculo de envío
        cart.shipping_cost = 0.0 if cart.subtotal > 50 else 5.99
        
        # Simular cálculo de impuestos (21% IVA)
        cart.tax_amount = cart.subtotal * 0.21
        
        # Aplicar descuento si existe
        cart.discount_amount = 0.0
        if cart.discount_code:
            if cart.discount_code == "DESCUENTO10":
                cart.discount_amount = cart.subtotal * 0.10
            elif cart.discount_code == "ENVIOGRATIS":
                cart.shipping_cost = 0.0
        
        cart.total = cart.subtotal + cart.shipping_cost + cart.tax_amount - cart.discount_amount
    
    async def checkout_cart(
        self,
        cart_id: str,
        shipping_address: Dict[str, str],
        payment_method: str = "credit_card",
        discount_code: Optional[str] = None
    ) -> CommerceResponse:
        """Procesar checkout del carrito"""
        start_time = time.time()
        
        try:
            if cart_id not in self._carts:
                raise ValueError(f"Carrito no encontrado: {cart_id}")
            
            cart = self._carts[cart_id]
            
            if not cart.items:
                raise ValueError("Carrito vacío")
            
            # Aplicar código de descuento
            if discount_code:
                cart.discount_code = discount_code
                self._update_cart_totals(cart)
            
            # Crear orden
            order_id = f"order_{str(uuid.uuid4())[:8]}"
            
            # Simular procesamiento de pago
            await asyncio.sleep(0.5)
            
            order = Order(
                id=order_id,
                cart_id=cart_id,
                customer_info=cart.customer_info,
                items=[{
                    "product_id": item.product.id,
                    "product_name": item.product.name,
                    "quantity": item.quantity,
                    "unit_price": item.product.price,
                    "total_price": item.product.price * item.quantity
                } for item in cart.items],
                subtotal=cart.subtotal,
                shipping_cost=cart.shipping_cost,
                tax_amount=cart.tax_amount,
                total=cart.total,
                payment_method=payment_method,
                shipping_address=shipping_address,
                status="processing",
                payment_status="paid",
                estimated_delivery=datetime.now() + timedelta(days=random.randint(3, 7))
            )
            
            # Simular generación de número de seguimiento
            order.tracking_number = f"TRK{random.randint(100000, 999999)}"
            
            # Actualizar carrito
            cart.status = CartStatus.COMPLETED
            cart.shipping_address = shipping_address
            cart.payment_method = payment_method
            
            # Guardar orden
            self._orders[order_id] = order
            
            self.logger.info(f"Checkout completado: {order_id}")
            
            return CommerceResponse(
                success=True,
                transaction_id=order_id,
                action="checkout_cart",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                details={
                    "order_id": order_id,
                    "total_amount": cart.total,
                    "payment_status": order.payment_status,
                    "estimated_delivery": order.estimated_delivery.isoformat(),
                    "tracking_number": order.tracking_number,
                    "items_count": len(cart.items)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Error procesando checkout: {str(e)}")
            return CommerceResponse(
                success=False,
                transaction_id=cart_id,
                action="checkout_cart",
                timestamp=time.time(),
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    def _product_to_dict(self, product: Product) -> Dict[str, Any]:
        """Convertir producto a diccionario"""
        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "category": product.category.value,
            "price": product.price,
            "original_price": product.original_price,
            "discount_percentage": product.discount_percentage,
            "currency": product.currency,
            "availability": product.availability,
            "rating": product.rating,
            "review_count": product.review_count,
            "brand": product.brand,
            "images": product.images,
            "specifications": product.specifications,
            "seller_info": product.seller_info,
            "shipping_info": product.shipping_info,
            "tags": product.tags
        }
    
    async def process_request(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesar request de comercio
        
        Formatos soportados:
        - search_products: {"action": "search_products", "query": "iPhone", "category": "electronics"}
        - compare_prices: {"action": "compare_prices", "product_query": "iPhone 15", "platforms": ["amazon", "ebay"]}
        - create_cart: {"action": "create_cart", "customer_info": {"email": "test@example.com"}}
        - add_to_cart: {"action": "add_to_cart", "cart_id": "cart_123", "product_id": "prod_1", "quantity": 2}
        - checkout_cart: {"action": "checkout_cart", "cart_id": "cart_123", "shipping_address": {...}}
        """
        try:
            await self.ensure_initialized()
            
            action = request.get("action", "").lower()
            
            if action == "search_products":
                query = request.get("query", "")
                category_str = request.get("category")
                min_price = request.get("min_price")
                max_price = request.get("max_price")
                brands = request.get("brands", [])
                min_rating = request.get("min_rating")
                limit = request.get("limit", 20)
                
                category = None
                if category_str:
                    try:
                        category = ProductCategory(category_str)
                    except ValueError:
                        pass
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="search_products",
                        capability=AgentCapability.PRODUCT_SEARCH,
                        operation_func=self.search_products,
                        query=query,
                        category=category,
                        min_price=min_price,
                        max_price=max_price,
                        brands=brands,
                        min_rating=min_rating,
                        limit=limit
                    )
                else:
                    response = await self.search_products(query, category, min_price, max_price, brands, min_rating, limit=limit)
                
                return {
                    "success": response.success,
                    "products": response.details.get("products", []) if response.success else [],
                    "count": response.details.get("products_found", 0) if response.success else 0,
                    "error": response.error
                }
            
            elif action == "compare_prices":
                product_query = request.get("product_query", "")
                platforms_str = request.get("platforms", [])
                
                platforms = []
                for platform_str in platforms_str:
                    try:
                        platforms.append(EcommercePlatform(platform_str))
                    except ValueError:
                        continue
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="compare_prices",
                        capability=AgentCapability.PRICE_COMPARISON,
                        operation_func=self.compare_prices,
                        product_query=product_query,
                        platforms=platforms if platforms else None
                    )
                else:
                    response = await self.compare_prices(product_query, platforms if platforms else None)
                
                return {
                    "success": response.success,
                    "comparison_results": response.details.get("comparison_results", []) if response.success else [],
                    "best_deal": response.details.get("best_deal") if response.success else None,
                    "price_stats": response.details.get("price_statistics", {}) if response.success else {},
                    "error": response.error
                }
            
            elif action == "create_cart":
                customer_info = request.get("customer_info", {})
                
                if not customer_info:
                    customer_info = {"email": "guest@example.com"}
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="create_cart",
                        capability=AgentCapability.CART_MANAGEMENT,
                        operation_func=self.create_cart,
                        customer_info=customer_info
                    )
                else:
                    response = await self.create_cart(customer_info)
                
                return {
                    "success": response.success,
                    "cart_id": response.transaction_id if response.success else None,
                    "details": response.details,
                    "error": response.error
                }
            
            elif action == "add_to_cart":
                cart_id = request.get("cart_id")
                product_id = request.get("product_id")
                quantity = request.get("quantity", 1)
                notes = request.get("notes")
                
                if not cart_id or not product_id:
                    raise ValueError("cart_id y product_id son requeridos")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="add_to_cart",
                        capability=AgentCapability.CART_MANAGEMENT,
                        operation_func=self.add_to_cart,
                        cart_id=cart_id,
                        product_id=product_id,
                        quantity=quantity,
                        notes=notes
                    )
                else:
                    response = await self.add_to_cart(cart_id, product_id, quantity, notes)
                
                return {
                    "success": response.success,
                    "cart_id": response.transaction_id if response.success else None,
                    "details": response.details,
                    "error": response.error
                }
            
            elif action == "checkout_cart":
                cart_id = request.get("cart_id")
                shipping_address = request.get("shipping_address", {})
                payment_method = request.get("payment_method", "credit_card")
                discount_code = request.get("discount_code")
                
                if not cart_id:
                    raise ValueError("cart_id requerido")
                
                if AgentCapability:
                    response = await self.execute_operation(
                        operation_name="checkout_cart",
                        capability=AgentCapability.CHECKOUT_PROCESSING,
                        operation_func=self.checkout_cart,
                        cart_id=cart_id,
                        shipping_address=shipping_address,
                        payment_method=payment_method,
                        discount_code=discount_code
                    )
                else:
                    response = await self.checkout_cart(cart_id, shipping_address, payment_method, discount_code)
                
                return {
                    "success": response.success,
                    "order_id": response.transaction_id if response.success else None,
                    "details": response.details,
                    "error": response.error
                }
            
            else:
                raise ValueError(f"Acción no soportada: {action}")
                
        except Exception as e:
            self.logger.error(f"Error procesando request de comercio: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del agente"""
        return {
            "total_products": len(self._products),
            "active_carts": len([c for c in self._carts.values() if c.status == CartStatus.ACTIVE]),
            "completed_orders": len(self._orders),
            "agent_name": "CommerceAgent",
            "supported_platforms": [platform.value for platform in EcommercePlatform],
            "product_categories": [category.value for category in ProductCategory],
            "available_actions": [
                "search_products",
                "compare_prices",
                "create_cart",
                "add_to_cart", 
                "checkout_cart"
            ]
        }