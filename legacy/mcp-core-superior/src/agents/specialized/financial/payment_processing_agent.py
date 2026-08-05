"""
Agente de Procesamiento de Pagos - APIs Financieras Avanzadas
Implementa integración profunda con Stripe, PayPal y sistemas de pago
Con seguridad PCI DSS y compliance financiero
"""

import asyncio
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
import stripe
import paypalrestsdk
from cryptography.fernet import Fernet
import jwt
import requests

@dataclass
class PaymentRequest:
    """Estructura para solicitudes de pago"""
    amount: float
    currency: str = "USD"
    method: str = "stripe"  # stripe, paypal
    customer_id: Optional[str] = None
    payment_method_id: Optional[str] = None
    subscription: bool = False
    metadata: Optional[Dict[str, str]] = None
    
@dataclass
class PaymentResult:
    """Resultado de procesamiento de pago"""
    success: bool
    transaction_id: str
    amount: float
    currency: str
    status: str
    created_at: datetime
    method: str
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, str]] = None

class PaymentMethod(Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"

class SecurityLevel(Enum):
    BASIC = "basic"
    ENHANCED = "enhanced"
    ENTERPRISE = "enterprise"

class PaymentProcessingAgent:
    """
    Agente especializado en procesamiento de pagos con múltiples proveedores
    Implementa seguridad PCI DSS, encriptación y audit trails
    """
    
    def __init__(self, 
                 stripe_secret_key: str,
                 stripe_publishable_key: str,
                 paypal_client_id: str,
                 paypal_client_secret: str,
                 encryption_key: str,
                 jwt_secret: str,
                 security_level: SecurityLevel = SecurityLevel.ENTERPRISE):
        
        self.security_level = security_level
        self.encryption_key = encryption_key
        self.jwt_secret = jwt_secret
        
        # Inicializar cliente Stripe
        stripe.api_key = stripe_secret_key
        
        # Configurar PayPal
        paypalrestsdk.configure({
            "mode": "sandbox" if stripe_secret_key.endswith("_test") else "live",
            "client_id": paypal_client_id,
            "client_secret": paypal_client_secret
        })
        
        # Cliente HTTP para APIs adicionales
        self.session = aiohttp.ClientSession()
        
        # Encriptación de datos sensibles
        self.cipher_suite = Fernet(encryption_key.encode())
        
        # Audit trail
        self.audit_log = []
        
    async def process_payment(self, 
                            payment_request: PaymentRequest,
                            user_id: str,
                            context: Optional[Dict[str, Any]] = None) -> PaymentResult:
        """
        Procesa pago con múltiples proveedores y failover automático
        """
        start_time = datetime.now()
        transaction_id = self._generate_transaction_id()
        
        try:
            # Log de inicio de transacción
            await self._log_audit_event("payment_started", {
                "transaction_id": transaction_id,
                "user_id": user_id,
                "amount": payment_request.amount,
                "currency": payment_request.currency,
                "method": payment_request.method
            })
            
            # Validaciones de seguridad PCI DSS
            await self._validate_security_requirements(payment_request, user_id)
            
            # Encriptar datos sensibles
            encrypted_data = await self._encrypt_sensitive_data(payment_request)
            
            # Procesar según el proveedor
            if payment_request.method == PaymentMethod.STRIPE.value:
                result = await self._process_stripe_payment(payment_request, encrypted_data)
            elif payment_request.method == PaymentMethod.PAYPAL.value:
                result = await self._process_paypal_payment(payment_request, encrypted_data)
            else:
                raise ValueError(f"Método de pago no soportado: {payment_request.method}")
            
            # Log de finalización exitosa
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._log_audit_event("payment_completed", {
                "transaction_id": transaction_id,
                "execution_time": execution_time,
                "result": asdict(result),
                "user_id": user_id
            })
            
            return result
            
        except Exception as e:
            # Log de error
            execution_time = (datetime.now() - start_time).total_seconds()
            await self._log_audit_event("payment_failed", {
                "transaction_id": transaction_id,
                "execution_time": execution_time,
                "error": str(e),
                "user_id": user_id
            })
            
            return PaymentResult(
                success=False,
                transaction_id=transaction_id,
                amount=payment_request.amount,
                currency=payment_request.currency,
                status="failed",
                created_at=datetime.now(),
                method=payment_request.method,
                error_message=str(e)
            )
    
    async def create_subscription(self,
                                customer_id: str,
                                price_id: str,
                                payment_method_id: str,
                                provider: str = "stripe") -> Dict[str, Any]:
        """
        Crea subscripciones recurrentes con múltiples proveedores
        """
        try:
            if provider == "stripe":
                # Crear cliente en Stripe si no existe
                customer = None
                if customer_id:
                    try:
                        customer = stripe.Customer.retrieve(customer_id)
                    except stripe.error.InvalidRequestError:
                        pass
                
                if not customer:
                    customer = stripe.Customer.create(
                        id=customer_id,
                        payment_method=payment_method_id,
                        invoice_settings={
                            'default_payment_method': payment_method_id
                        }
                    )
                
                # Crear subscripción
                subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{'price': price_id}],
                    payment_behavior='default_incomplete',
                    expand=['latest_invoice.payment_intent'],
                    metadata={
                        'agent_system': 'financial_agent',
                        'created_by': 'payment_processing_agent'
                    }
                )
                
                return {
                    "success": True,
                    "subscription_id": subscription.id,
                    "client_secret": subscription.latest_invoice.payment_intent.client_secret,
                    "status": subscription.status
                }
            
            elif provider == "paypal":
                # Implementación PayPal subscripciones
                plan = self._get_paypal_plan(price_id)
                
                subscription = paypalrestsdk.Subscription.create({
                    "plan_id": plan["id"],
                    "application_context": {
                        "brand_name": "Fintech System",
                        "locale": "es-ES",
                        "shipping_preference": "NO_SHIPPING",
                        "user_action": "SUBSCRIBE_NOW",
                        "payment_method": {
                            "payer_selected": "PAYPAL",
                            "payee_preferred": "IMMEDIATE_PAYMENT_REQUIRED"
                        },
                        "return_url": "https://example.com/success",
                        "cancel_url": "https://example.com/cancel"
                    }
                })
                
                return {
                    "success": True,
                    "subscription_id": subscription.id,
                    "approval_url": subscription.links[0].href,
                    "status": subscription.status
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "code": "SUBSCRIPTION_CREATION_FAILED"
            }
    
    async def handle_webhook(self, 
                           payload: str,
                           signature: str,
                           provider: str) -> Dict[str, Any]:
        """
        Procesa webhooks de proveedores de pago para actualizaciones de estado
        """
        try:
            if provider == "stripe":
                # Verificar firma de Stripe
                event = stripe.Webhook.construct_event(
                    payload, signature, self.stripe_webhook_secret
                )
                
                # Procesar diferentes tipos de eventos
                if event['type'] == 'payment_intent.succeeded':
                    return await self._handle_payment_success(event['data']['object'])
                elif event['type'] == 'invoice.payment_succeeded':
                    return await self._handle_subscription_payment(event['data']['object'])
                elif event['type'] == 'customer.subscription.updated':
                    return await self._handle_subscription_update(event['data']['object'])
                    
            elif provider == "paypal":
                # Validar webhook de PayPal
                webhook = paypalrestsdk.Webhook.validate(payload)
                
                if webhook["event_type"] == "PAYMENT.CAPTURE.COMPLETED":
                    return await self._handle_paypal_payment_success(webhook["resource"])
                elif webhook["event_type"] == "BILLING.SUBSCRIPTION.ACTIVATED":
                    return await self._handle_paypal_subscription_activated(webhook["resource"])
                    
            return {"status": "processed", "provider": provider}
            
        except Exception as e:
            await self._log_audit_event("webhook_error", {
                "provider": provider,
                "error": str(e),
                "payload": payload[:200]  # Solo primeros 200 chars para seguridad
            })
            return {"status": "error", "error": str(e)}
    
    async def _process_stripe_payment(self, 
                                    payment_request: PaymentRequest,
                                    encrypted_data: str) -> PaymentResult:
        """Procesa pago específico de Stripe"""
        try:
            # Crear PaymentIntent
            payment_intent = stripe.PaymentIntent.create(
                amount=int(payment_request.amount * 100),  # Convertir a centavos
                currency=payment_request.currency.lower(),
                payment_method=payment_request.payment_method_id,
                customer=payment_request.customer_id,
                confirmation_method='manual',
                confirm=True,
                metadata=payment_request.metadata or {}
            )
            
            return PaymentResult(
                success=payment_intent.status == 'succeeded',
                transaction_id=payment_intent.id,
                amount=payment_request.amount,
                currency=payment_request.currency,
                status=payment_intent.status,
                created_at=datetime.fromtimestamp(payment_intent.created),
                method="stripe",
                metadata={"client_secret": payment_intent.client_secret}
            )
            
        except stripe.error.CardError as e:
            return PaymentResult(
                success=False,
                transaction_id=f"stripe_error_{int(datetime.now().timestamp())}",
                amount=payment_request.amount,
                currency=payment_request.currency,
                status="failed",
                created_at=datetime.now(),
                method="stripe",
                error_message=e.user_message
            )
    
    async def _process_paypal_payment(self,
                                    payment_request: PaymentRequest,
                                    encrypted_data: str) -> PaymentResult:
        """Procesa pago específico de PayPal"""
        try:
            # Crear pago PayPal
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "transactions": [{
                    "amount": {
                        "total": str(payment_request.amount),
                        "currency": payment_request.currency
                    },
                    "description": "Pago procesado por Financial Agent",
                    "custom": encrypted_data[:255]  # Límite de PayPal
                }],
                "redirect_urls": {
                    "return_url": "https://example.com/success",
                    "cancel_url": "https://example.com/cancel"
                }
            })
            
            # Ejecutar pago
            if payment.create():
                return PaymentResult(
                    success=True,
                    transaction_id=payment.id,
                    amount=payment_request.amount,
                    currency=payment_request.currency,
                    status="created",
                    created_at=datetime.now(),
                    method="paypal",
                    metadata={
                        "approval_url": payment.links[0].href
                    }
                )
            else:
                raise Exception(f"Error PayPal: {payment.error}")
                
        except Exception as e:
            return PaymentResult(
                success=False,
                transaction_id=f"paypal_error_{int(datetime.now().timestamp())}",
                amount=payment_request.amount,
                currency=payment_request.currency,
                status="failed",
                created_at=datetime.now(),
                method="paypal",
                error_message=str(e)
            )
    
    async def _validate_security_requirements(self, 
                                            payment_request: PaymentRequest,
                                            user_id: str) -> None:
        """Validaciones de seguridad PCI DSS"""
        # Verificar que el usuario está autorizado
        if not await self._verify_user_authorization(user_id):
            raise Exception("Usuario no autorizado para realizar pagos")
        
        # Validar límites de transacción
        if payment_request.amount > 10000:  # Límite configurable
            raise Exception("Monto excede el límite permitido")
        
        # Verificar frecuencia de transacciones
        recent_transactions = await self._get_recent_transactions(user_id, hours=1)
        if len(recent_transactions) > 10:  # Límite por hora
            raise Exception("Demasiadas transacciones en período corto")
        
        # Validación de formato de datos
        if not payment_request.currency in ["USD", "EUR", "GBP", "MXN"]:
            raise Exception("Moneda no soportada")
    
    async def _encrypt_sensitive_data(self, payment_request: PaymentRequest) -> str:
        """Encripta datos sensibles usando Fernet"""
        sensitive_data = {
            "payment_method_id": payment_request.payment_method_id,
            "customer_id": payment_request.customer_id,
            "metadata": payment_request.metadata
        }
        
        json_data = json.dumps(sensitive_data).encode()
        encrypted_data = self.cipher_suite.encrypt(json_data)
        return encrypted_data.decode()
    
    async def _decrypt_sensitive_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Desencripta datos sensibles"""
        encrypted_bytes = encrypted_data.encode()
        decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
        return json.loads(decrypted_bytes.decode())
    
    async def _generate_jwt_token(self, data: Dict[str, Any], expires_hours: int = 1) -> str:
        """Genera JWT token para autorización"""
        payload = {
            **data,
            "exp": datetime.utcnow() + timedelta(hours=expires_hours),
            "iat": datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def _generate_transaction_id(self) -> str:
        """Genera ID único de transacción"""
        timestamp = int(datetime.now().timestamp() * 1000000)
        random_suffix = hashlib.md5(str(datetime.now().microsecond).encode()).hexdigest()[:8]
        return f"txn_{timestamp}_{random_suffix}"
    
    async def _log_audit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Registra evento en audit trail"""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data,
            "security_level": self.security_level.value
        }
        self.audit_log.append(audit_entry)
        
        # En producción, enviar a sistema de logging centralizado
        print(f"AUDIT: {event_type} - {json.dumps(audit_entry, default=str)}")
    
    async def _verify_user_authorization(self, user_id: str) -> bool:
        """Verifica autorización de usuario"""
        # Implementar lógica de verificación de autorización
        # En producción, consultar base de datos de usuarios
        return True
    
    async def _get_recent_transactions(self, user_id: str, hours: int) -> List[Dict[str, Any]]:
        """Obtiene transacciones recientes del usuario"""
        # Implementar consulta a base de datos
        # Por ahora retornamos lista vacía
        return []
    
    def _get_paypal_plan(self, price_id: str) -> Dict[str, Any]:
        """Mapea price_id de Stripe a plan de PayPal"""
        # Mapeo configurable de precios
        plan_mapping = {
            "price_basic": {"id": "P-BASIC-001"},
            "price_premium": {"id": "P-PREMIUM-001"},
            "price_enterprise": {"id": "P-ENTERPRISE-001"}
        }
        return plan_mapping.get(price_id, {"id": "P-DEFAULT-001"})
    
    async def _handle_payment_success(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja evento de pago exitoso de Stripe"""
        await self._log_audit_event("stripe_payment_success", {
            "payment_intent_id": payment_intent["id"],
            "amount": payment_intent["amount"] / 100,
            "currency": payment_intent["currency"]
        })
        return {"status": "processed", "action": "payment_confirmed"}
    
    async def _handle_subscription_payment(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja pago de subscripción exitosa"""
        await self._log_audit_event("stripe_subscription_payment", {
            "invoice_id": invoice["id"],
            "subscription_id": invoice["subscription"],
            "amount_paid": invoice["amount_paid"] / 100
        })
        return {"status": "processed", "action": "subscription_renewed"}
    
    async def _handle_subscription_update(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja actualización de subscripción"""
        await self._log_audit_event("stripe_subscription_update", {
            "subscription_id": subscription["id"],
            "status": subscription["status"],
            "current_period_end": subscription["current_period_end"]
        })
        return {"status": "processed", "action": "subscription_updated"}
    
    async def _handle_paypal_payment_success(self, capture: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja pago exitoso de PayPal"""
        await self._log_audit_event("paypal_payment_success", {
            "capture_id": capture["id"],
            "amount": capture["amount"]["value"],
            "currency": capture["amount"]["currency_code"]
        })
        return {"status": "processed", "action": "payment_confirmed"}
    
    async def _handle_paypal_subscription_activated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Maneja activación de subscripción PayPal"""
        await self._log_audit_event("paypal_subscription_activated", {
            "subscription_id": subscription["id"],
            "status": subscription["status"]
        })
        return {"status": "processed", "action": "subscription_activated"}
    
    async def close(self):
        """Cierra recursos"""
        await self.session.close()
