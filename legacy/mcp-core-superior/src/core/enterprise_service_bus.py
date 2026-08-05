"""
Enterprise Service Bus (ESB) para MCP Core Superior
Maneja comunicación asíncrona entre servicios enterprise
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta
import aioredis
from fastmcp import FastMCP
import uuid
from concurrent.futures import ThreadPoolExecutor
import logging


class MessagePriority(Enum):
    """Prioridad de mensajes en el ESB"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class MessageStatus(Enum):
    """Estados de mensajes en el ESB"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    RETRY = "retry"


@dataclass
class ServiceMessage:
    """Estructura de mensaje para el ESB"""
    id: str
    sender: str
    recipient: str
    message_type: str
    priority: MessagePriority
    payload: Dict[str, Any]
    timestamp: datetime
    expires_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    status: MessageStatus = MessageStatus.PENDING
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['expires_at'] = self.expires_at.isoformat() if self.expires_at else None
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceMessage':
        """Crear desde diccionario"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        if data.get('expires_at'):
            data['expires_at'] = datetime.fromisoformat(data['expires_at'])
        data['priority'] = MessagePriority(data['priority'])
        data['status'] = MessageStatus(data['status'])
        return cls(**data)


@dataclass
class ServiceEndpoint:
    """Endpoint de servicio en el ESB"""
    service_name: str
    service_type: str
    host: str
    port: int
    protocols: List[str]
    version: str = "1.0.0"
    health_check_url: Optional[str] = None
    capabilities: List[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_active: bool = True
    last_health_check: Optional[datetime] = None
    load_weight: int = 100  # Peso para load balancing

    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []
        if self.metadata is None:
            self.metadata = {}


class EnterpriseServiceBus:
    """Enterprise Service Bus principal"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.redis = None
        self.services: Dict[str, ServiceEndpoint] = {}
        self.message_handlers: Dict[str, Callable] = {}
        self.message_queue: List[ServiceMessage] = []
        self.priority_queues: Dict[MessagePriority, List[ServiceMessage]] = {
            priority: [] for priority in MessagePriority
        }
        self.dead_letter_queue: List[ServiceMessage] = []
        self.is_running = False
        self.message_processor_task = None
        self.health_check_task = None
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Métricas
        self.metrics = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_failed": 0,
            "messages_retried": 0,
            "services_registered": 0,
            "health_checks": 0,
            "average_processing_time": 0.0
        }
    
    async def initialize(self) -> None:
        """Inicializar el ESB"""
        try:
            # Conectar a Redis para mensajería
            redis_config = self.config.get("redis", {})
            self.redis = await aioredis.from_url(
                redis_config.get("url", "redis://localhost:6379"),
                **redis_config.get("connection", {})
            )
            
            # Registrar servicios locales
            await self._register_local_services()
            
            # Iniciar procesadores
            await self.start_processors()
            
            self.logger.info("Enterprise Service Bus inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error inicializando ESB: {e}")
            raise
    
    async def register_service(self, endpoint: ServiceEndpoint) -> None:
        """Registrar un servicio en el ESB"""
        try:
            self.services[endpoint.service_name] = endpoint
            self.metrics["services_registered"] += 1
            
            # Almacenar en Redis para distribución
            if self.redis:
                await self.redis.setex(
                    f"esb:service:{endpoint.service_name}",
                    3600,  # TTL de 1 hora
                    json.dumps(asdict(endpoint), default=str)
                )
            
            self.logger.info(f"Servicio registrado: {endpoint.service_name}")
            
        except Exception as e:
            self.logger.error(f"Error registrando servicio {endpoint.service_name}: {e}")
            raise
    
    async def unregister_service(self, service_name: str) -> None:
        """Desregistrar un servicio"""
        try:
            if service_name in self.services:
                del self.services[service_name]
                
                if self.redis:
                    await self.redis.delete(f"esb:service:{service_name}")
                
                self.logger.info(f"Servicio desregistrado: {service_name}")
                
        except Exception as e:
            self.logger.error(f"Error desregistrando servicio {service_name}: {e}")
            raise
    
    async def send_message(
        self, 
        sender: str, 
        recipient: str, 
        message_type: str, 
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        timeout_seconds: int = 30,
        reply_to: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None
    ) -> str:
        """Enviar mensaje a través del ESB"""
        try:
            message_id = str(uuid.uuid4())
            expires_at = datetime.utcnow() + timedelta(seconds=timeout_seconds)
            
            message = ServiceMessage(
                id=message_id,
                sender=sender,
                recipient=recipient,
                message_type=message_type,
                priority=priority,
                payload=payload,
                timestamp=datetime.utcnow(),
                expires_at=expires_at,
                correlation_id=f"{sender}:{int(time.time())}",
                reply_to=reply_to,
                headers=headers or {}
            )
            
            # Agregar a cola de prioridad
            self.priority_queues[priority].append(message)
            
            # Almacenar en Redis para persistencia
            if self.redis:
                await self.redis.lpush(
                    "esb:queue",
                    json.dumps(message.to_dict(), default=str)
                )
            
            self.metrics["messages_sent"] += 1
            self.logger.debug(f"Mensaje enviado: {message_id} -> {recipient}")
            
            return message_id
            
        except Exception as e:
            self.logger.error(f"Error enviando mensaje: {e}")
            self.metrics["messages_failed"] += 1
            raise
    
    async def publish_message(
        self,
        sender: str,
        topic: str,
        message_type: str,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        headers: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publicar mensaje a un topic (pub/sub)"""
        try:
            message_id = str(uuid.uuid4())
            message = ServiceMessage(
                id=message_id,
                sender=sender,
                recipient=f"topic:{topic}",
                message_type=message_type,
                priority=priority,
                payload=payload,
                timestamp=datetime.utcnow(),
                correlation_id=f"pub:{int(time.time())}",
                headers=headers or {}
            )
            
            # Publicar via Redis
            if self.redis:
                await self.redis.publish(
                    f"esb:topic:{topic}",
                    json.dumps(message.to_dict(), default=str)
                )
            
            self.metrics["messages_sent"] += 1
            self.logger.debug(f"Mensaje publicado: {message_id} -> topic:{topic}")
            
            return message_id
            
        except Exception as e:
            self.logger.error(f"Error publicando mensaje: {e}")
            self.metrics["messages_failed"] += 1
            raise
    
    async def subscribe_to_topic(
        self, 
        topic: str, 
        handler: Callable[[ServiceMessage], None]
    ) -> None:
        """Suscribirse a un topic"""
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(f"esb:topic:{topic}")
            
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        service_message = ServiceMessage.from_dict(data)
                        await handler(service_message)
                    except Exception as e:
                        self.logger.error(f"Error procesando mensaje de topic {topic}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error en suscripción a topic {topic}: {e}")
            raise
    
    async def register_message_handler(
        self, 
        message_type: str, 
        handler: Callable[[ServiceMessage], None]
    ) -> None:
        """Registrar handler para tipo de mensaje"""
        self.message_handlers[message_type] = handler
        self.logger.info(f"Handler registrado para tipo: {message_type}")
    
    async def start_processors(self) -> None:
        """Iniciar procesadores de mensajes"""
        if not self.is_running:
            self.is_running = True
            self.message_processor_task = asyncio.create_task(self._process_messages())
            self.health_check_task = asyncio.create_task(self._health_check_services())
            self.logger.info("Procesadores de ESB iniciados")
    
    async def stop_processors(self) -> None:
        """Detener procesadores"""
        self.is_running = False
        
        if self.message_processor_task:
            self.message_processor_task.cancel()
            
        if self.health_check_task:
            self.health_check_task.cancel()
            
        self.logger.info("Procesadores de ESB detenidos")
    
    async def _process_messages(self) -> None:
        """Procesar mensajes en colas de prioridad"""
        while self.is_running:
            try:
                await asyncio.sleep(0.1)  # Evitar busy-waiting
                
                # Procesar mensajes por prioridad
                for priority in reversed(list(MessagePriority)):
                    queue = self.priority_queues[priority]
                    
                    while queue:
                        message = queue.pop(0)
                        
                        # Verificar expiración
                        if message.expires_at and message.expires_at < datetime.utcnow():
                            message.status = MessageStatus.EXPIRED
                            self.dead_letter_queue.append(message)
                            continue
                        
                        # Procesar mensaje
                        await self._handle_message(message)
                        
                # Procesar mensajes de Redis
                if self.redis:
                    await self._process_redis_messages()
                    
            except Exception as e:
                self.logger.error(f"Error en procesador de mensajes: {e}")
                await asyncio.sleep(1)
    
    async def _handle_message(self, message: ServiceMessage) -> None:
        """Procesar un mensaje individual"""
        start_time = time.time()
        
        try:
            message.status = MessageStatus.PROCESSING
            self.metrics["messages_received"] += 1
            
            # Buscar handler
            handler = self.message_handlers.get(message.message_type)
            
            if handler:
                # Ejecutar handler en thread pool para CPU-bound
                await asyncio.get_event_loop().run_in_executor(
                    self.executor,
                    handler,
                    message
                )
            else:
                self.logger.warning(f"No hay handler para tipo: {message.message_type}")
                message.status = MessageStatus.FAILED
            
            # Actualizar métricas
            processing_time = time.time() - start_time
            self._update_processing_metrics(processing_time)
            
            if message.status == MessageStatus.PROCESSING:
                message.status = MessageStatus.COMPLETED
                
        except Exception as e:
            self.logger.error(f"Error procesando mensaje {message.id}: {e}")
            message.status = MessageStatus.FAILED
            self.metrics["messages_failed"] += 1
            
            # Manejar retry
            if message.retry_count < message.max_retries:
                message.retry_count += 1
                message.status = MessageStatus.RETRY
                self.priority_queues[message.priority].append(message)
                self.metrics["messages_retried"] += 1
            else:
                self.dead_letter_queue.append(message)
    
    async def _process_redis_messages(self) -> None:
        """Procesar mensajes desde Redis"""
        try:
            # Obtener mensajes de la cola con timeout
            messages = await self.redis.brpop("esb:queue", timeout=1)
            
            if messages:
                _, data = messages
                message_dict = json.loads(data)
                message = ServiceMessage.from_dict(message_dict)
                
                # Agregar a cola de prioridad
                self.priority_queues[message.priority].append(message)
                
        except Exception as e:
            self.logger.error(f"Error procesando mensajes de Redis: {e}")
    
    async def _health_check_services(self) -> None:
        """Verificar salud de servicios registrados"""
        while self.is_running:
            try:
                for service_name, endpoint in list(self.services.items()):
                    await self._check_service_health(endpoint)
                    self.metrics["health_checks"] += 1
                
                await asyncio.sleep(30)  # Health check cada 30 segundos
                
            except Exception as e:
                self.logger.error(f"Error en health check: {e}")
                await asyncio.sleep(30)
    
    async def _check_service_health(self, endpoint: ServiceEndpoint) -> None:
        """Verificar salud de un servicio específico"""
        try:
            # Realizar health check (implementación específica del servicio)
            # Por ahora, marcar como saludable
            endpoint.last_health_check = datetime.utcnow()
            endpoint.is_active = True
            
            self.logger.debug(f"Health check OK: {endpoint.service_name}")
            
        except Exception as e:
            self.logger.warning(f"Health check failed: {endpoint.service_name}: {e}")
            endpoint.is_active = False
    
    async def _register_local_services(self) -> None:
        """Registrar servicios locales del MCP Core"""
        local_services = [
            ServiceEndpoint(
                service_name="mcp_core_superior",
                service_type="orchestrator",
                host="localhost",
                port=8080,
                protocols=["http", "fastmcp"],
                version="1.0.0",
                capabilities=["multitask", "streaming", "agents"],
                metadata={"description": "MCP Core Superior Orchestrator"}
            ),
            ServiceEndpoint(
                service_name="reasoner_agent",
                service_type="agent",
                host="localhost",
                port=8081,
                protocols=["fastmcp"],
                version="1.0.0",
                capabilities=["analysis", "reasoning"],
                metadata={"description": "Reasoner Agent"}
            ),
            ServiceEndpoint(
                service_name="planner_agent",
                service_type="agent",
                host="localhost",
                port=8082,
                protocols=["fastmcp"],
                version="1.0.0",
                capabilities=["planning", "task_decomposition"],
                metadata={"description": "Planner Agent"}
            ),
            ServiceEndpoint(
                service_name="executor_agent",
                service_type="agent",
                host="localhost",
                port=8083,
                protocols=["fastmcp"],
                version="1.0.0",
                capabilities=["execution", "tool_invocation"],
                metadata={"description": "Executor Agent"}
            ),
            ServiceEndpoint(
                service_name="verifier_agent",
                service_type="agent",
                host="localhost",
                port=8084,
                protocols=["fastmcp"],
                version="1.0.0",
                capabilities=["validation", "verification"],
                metadata={"description": "Verifier Agent"}
            ),
        ]
        
        for service in local_services:
            await self.register_service(service)
    
    def _update_processing_metrics(self, processing_time: float) -> None:
        """Actualizar métricas de procesamiento"""
        # Promedio móvil
        current_avg = self.metrics["average_processing_time"]
        count = self.metrics["messages_received"]
        
        if count > 1:
            new_avg = ((current_avg * (count - 1)) + processing_time) / count
            self.metrics["average_processing_time"] = new_avg
        else:
            self.metrics["average_processing_time"] = processing_time
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtener métricas del ESB"""
        return {
            **self.metrics,
            "active_services": len([s for s in self.services.values() if s.is_active]),
            "queue_sizes": {
                priority.name: len(queue) 
                for priority, queue in self.priority_queues.items()
            },
            "dead_letter_count": len(self.dead_letter_queue),
            "is_running": self.is_running
        }
    
    async def cleanup(self) -> None:
        """Limpiar recursos"""
        await self.stop_processors()
        
        if self.redis:
            await self.redis.close()
        
        self.executor.shutdown(wait=True)
        
        self.logger.info("Enterprise Service Bus limpiado")


# Instancia global del ESB
enterprise_esb: Optional[EnterpriseServiceBus] = None


async def initialize_enterprise_esb(config: Dict[str, Any]) -> EnterpriseServiceBus:
    """Inicializar ESB enterprise"""
    global enterprise_esb
    
    enterprise_esb = EnterpriseServiceBus(config)
    await enterprise_esb.initialize()
    
    return enterprise_esb


async def get_enterprise_esb() -> EnterpriseServiceBus:
    """Obtener instancia del ESB"""
    if not enterprise_esb:
        raise RuntimeError("ESB no inicializado. Llamar initialize_enterprise_esb primero.")
    return enterprise_esb