"""
Microsoft 365 - Graph API Integration Core
Cliente principal para interactuar con Microsoft Graph API
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

import aiohttp
from asyncio_throttle import Throttler

from ..auth.azure_ad import auth_client
from ..config.settings import settings, SERVICE_ENDPOINTS, RATE_LIMITS
from ..utils.logger import get_logger
from ..utils.retry_handler import RetryHandler
from ..utils.rate_limiter import RateLimiter

logger = get_logger(__name__)

class GraphAPIClient:
    """Cliente principal para Microsoft Graph API"""
    
    def __init__(self):
        self.base_url = SERVICE_ENDPOINTS["graph"]
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Rate limiters por servicio
        self.rate_limiter = RateLimiter(
            requests_per_minute=RATE_LIMITS["graph"]["requests_per_minute"],
            requests_per_day=RATE_LIMITS["graph"]["requests_per_day"]
        )
        
        # Retry handler
        self.retry_handler = RetryHandler(
            max_retries=settings.max_retries,
            base_delay=settings.retry_delay
        )
        
        # Throttler para control de velocidad
        self.throttler = Throttler(
            rate_limit=RATE_LIMITS["graph"]["requests_per_minute"],
            period=60
        )
        
        # Configuración de headers por defecto
        self.default_headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'Microsoft365-Integration/1.0'
        }
    
    async def __aenter__(self):
        """Context manager entry"""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close_session()
    
    async def start_session(self):
        """Iniciar sesión HTTP"""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=settings.request_timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers=self.default_headers
            )
            logger.info("Graph API client session started")
    
    async def close_session(self):
        """Cerrar sesión HTTP"""
        if self.session and not self.session.closed:
            await self.session.close()
            logger.info("Graph API client session closed")
    
    async def authenticate(self) -> str:
        """Obtener token de autenticación"""
        try:
            token = await auth_client.authenticate_application()
            self.default_headers['Authorization'] = f'Bearer {token}'
            return token
        except Exception as e:
            logger.error(f"Error autenticando con Graph API: {str(e)}")
            raise GraphAPIError(f"Authentication failed: {str(e)}")
    
    async def make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> Dict:
        """Realizar request a Graph API con reintentos automáticos"""
        
        # Asegurar autenticación
        await self.authenticate()
        
        # Construir URL completa
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Merge headers
        request_headers = {**self.default_headers}
        if headers:
            request_headers.update(headers)
        
        # Aplicar rate limiting
        async with self.rate_limiter:
            pass
        
        # Aplicar throttling
        async with self.throttler:
            pass
        
        # Realizar request con retry
        async def _request():
            async with self.session.request(
                method=method,
                url=url,
                params=params,
                json=data if data else None,
                headers=request_headers,
                **kwargs
            ) as response:
                
                response_data = await response.json()
                
                # Verificar errores HTTP
                if response.status >= 400:
                    error_msg = f"Graph API error {response.status}: {response_data}"
                    logger.error(error_msg)
                    
                    if response.status == 401:
                        # Token expirado, intentar renovar
                        await self.authenticate()
                        raise RetryableError("Token expired, retrying...")
                    elif response.status == 429:
                        # Rate limit excedido
                        retry_after = response.headers.get('Retry-After', '60')
                        logger.warning(f"Rate limit exceeded, waiting {retry_after} seconds")
                        await asyncio.sleep(int(retry_after))
                        raise RetryableError("Rate limit exceeded, retrying...")
                    
                    raise GraphAPIError(error_msg)
                
                logger.debug(f"Graph API request successful: {method} {endpoint}")
                return response_data
        
        try:
            return await self.retry_handler.execute_with_retry(_request)
        except Exception as e:
            logger.error(f"Request failed after retries: {str(e)}")
            raise GraphAPIError(f"Request failed: {str(e)}")
    
    # ==================== USER OPERATIONS ====================
    
    async def get_current_user(self) -> Dict:
        """Obtener información del usuario actual"""
        return await self.make_request("GET", "/me")
    
    async def get_user(self, user_id: str) -> Dict:
        """Obtener información de un usuario específico"""
        return await self.make_request("GET", f"/users/{user_id}")
    
    async def list_users(
        self,
        top: int = 25,
        skip: int = 0,
        filter_str: Optional[str] = None,
        order_by: Optional[str] = None
    ) -> Dict:
        """Listar usuarios con paginación y filtros"""
        params = {'$top': top, '$skip': skip}
        
        if filter_str:
            params['$filter'] = filter_str
        if order_by:
            params['$orderby'] = order_by
        
        return await self.make_request("GET", "/users", params=params)
    
    async def search_users(self, search_term: str) -> Dict:
        """Buscar usuarios por término"""
        return await self.make_request(
            "GET", 
            f"/users?$search=\"{search_term}\"&$count=true"
        )
    
    # ==================== FILE OPERATIONS ====================
    
    async def list_files(
        self,
        path: str = "",
        top: int = 25,
        next_link: Optional[str] = None
    ) -> Dict:
        """Listar archivos en OneDrive"""
        if next_link:
            return await self.make_request("GET", next_link.replace(self.base_url, ""))
        else:
            endpoint = f"/me/drive/root/children" if not path else f"/me/drive/root:/{path}:/children"
            return await self.make_request("GET", endpoint, params={'$top': top})
    
    async def get_file(self, file_id: str) -> Dict:
        """Obtener metadatos de archivo"""
        return await self.make_request("GET", f"/me/drive/items/{file_id}")
    
    async def download_file(self, file_id: str) -> bytes:
        """Descargar contenido de archivo"""
        token = await auth_client.authenticate_application()
        headers = {'Authorization': f'Bearer {token}'}
        
        url = f"{self.base_url}/me/drive/items/{file_id}/content"
        async with self.session.get(url, headers=headers) as response:
            return await response.read()
    
    async def upload_file(
        self,
        file_path: str,
        content: bytes,
        parent_id: Optional[str] = None
    ) -> Dict:
        """Subir archivo a OneDrive"""
        if parent_id:
            endpoint = f"/me/drive/items/{parent_id}:/{file_path}:/content"
        else:
            endpoint = f"/me/drive/root:/{file_path}:/content"
        
        headers = {'Content-Type': 'application/octet-stream'}
        return await self.make_request("PUT", endpoint, data=content, headers=headers)
    
    async def delete_file(self, file_id: str) -> bool:
        """Eliminar archivo"""
        try:
            await self.make_request("DELETE", f"/me/drive/items/{file_id}")
            return True
        except GraphAPIError:
            return False
    
    # ==================== SHAREPOINT OPERATIONS ====================
    
    async def get_sharepoint_sites(self) -> Dict:
        """Obtener sitios de SharePoint"""
        return await self.make_request("GET", "/sites")
    
    async def get_sharepoint_site(self, site_id: str) -> Dict:
        """Obtener sitio específico de SharePoint"""
        return await self.make_request("GET", f"/sites/{site_id}")
    
    async def list_sharepoint_libraries(self, site_id: str) -> Dict:
        """Listar bibliotecas de documentos de un sitio"""
        return await self.make_request("GET", f"/sites/{site_id}/drive/root/children")
    
    # ==================== EMAIL OPERATIONS ====================
    
    async def list_messages(
        self,
        folder: str = "inbox",
        top: int = 25,
        skip: int = 0,
        filter_str: Optional[str] = None
    ) -> Dict:
        """Listar mensajes de correo"""
        endpoint = f"/me/mailFolders/{folder}/messages"
        params = {'$top': top, '$skip': skip}
        
        if filter_str:
            params['$filter'] = filter_str
        
        return await self.make_request("GET", endpoint, params=params)
    
    async def send_email(self, message: Dict) -> Dict:
        """Enviar correo electrónico"""
        return await self.make_request("POST", "/me/sendMail", data=message)
    
    async def get_message(self, message_id: str) -> Dict:
        """Obtener mensaje específico"""
        return await self.make_request("GET", f"/me/messages/{message_id}")
    
    async def delete_message(self, message_id: str) -> bool:
        """Eliminar mensaje"""
        try:
            await self.make_request("DELETE", f"/me/messages/{message_id}")
            return True
        except GraphAPIError:
            return False
    
    # ==================== CALENDAR OPERATIONS ====================
    
    async def list_events(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        top: int = 25
    ) -> Dict:
        """Listar eventos del calendario"""
        endpoint = "/me/calendarView"
        params = {'$top': top}
        
        if start_time and end_time:
            params['startDateTime'] = start_time
            params['endDateTime'] = end_time
        
        return await self.make_request("GET", endpoint, params=params)
    
    async def create_event(self, event_data: Dict) -> Dict:
        """Crear evento en calendario"""
        return await self.make_request("POST", "/me/events", data=event_data)
    
    async def update_event(self, event_id: str, event_data: Dict) -> Dict:
        """Actualizar evento"""
        return await self.make_request("PATCH", f"/me/events/{event_id}", data=event_data)
    
    async def delete_event(self, event_id: str) -> bool:
        """Eliminar evento"""
        try:
            await self.make_request("DELETE", f"/me/events/{event_id}")
            return True
        except GraphAPIError:
            return False
    
    # ==================== GROUPS & TEAMS OPERATIONS ====================
    
    async def list_groups(self, top: int = 25) -> Dict:
        """Listar grupos"""
        return await self.make_request("GET", "/groups", params={'$top': top})
    
    async def get_group(self, group_id: str) -> Dict:
        """Obtener información de grupo"""
        return await self.make_request("GET", f"/groups/{group_id}")
    
    async def list_teams(self, group_id: str) -> Dict:
        """Listar equipos de un grupo"""
        return await self.make_request("GET", f"/groups/{group_id}/team")
    
    # ==================== BATCH OPERATIONS ====================
    
    async def batch_request(self, requests: List[Dict]) -> Dict:
        """Realizar múltiples requests en una sola llamada"""
        batch_data = {
            'requests': requests
        }
        return await self.make_request("POST", "$batch", data=batch_data)
    
    async def batch_get_users(self, user_ids: List[str]) -> Dict:
        """Obtener múltiples usuarios en batch"""
        requests = []
        for i, user_id in enumerate(user_ids):
            requests.append({
                'id': str(i),
                'method': 'GET',
                'url': f'/users/{user_id}'
            })
        
        return await self.batch_request(requests)
    
    # ==================== WEBHOOK OPERATIONS ====================
    
    async def create_subscription(
        self,
        resource: str,
        notification_url: str,
        expiration_date_time: str,
        client_state: str = "ms365_integration"
    ) -> Dict:
        """Crear suscripción para notificaciones"""
        subscription_data = {
            'changeType': 'created,updated,deleted',
            'notificationUrl': notification_url,
            'resource': resource,
            'expirationDateTime': expiration_date_time,
            'clientState': client_state
        }
        
        return await self.make_request("POST", "/subscriptions", data=subscription_data)
    
    async def list_subscriptions(self) -> Dict:
        """Listar suscripciones activas"""
        return await self.make_request("GET", "/subscriptions")
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """Eliminar suscripción"""
        try:
            await self.make_request("DELETE", f"/subscriptions/{subscription_id}")
            return True
        except GraphAPIError:
            return False
    
    # ==================== UTILITY METHODS ====================
    
    async def health_check(self) -> Dict:
        """Verificar estado de la conexión con Graph API"""
        try:
            start_time = datetime.utcnow()
            user_info = await self.get_current_user()
            end_time = datetime.utcnow()
            
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                'status': 'healthy',
                'response_time_ms': response_time,
                'user_info': user_info.get('displayName', 'Unknown'),
                'timestamp': end_time.isoformat()
            }
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def get_api_quota(self) -> Dict:
        """Obtener información de cuotas de API"""
        try:
            # Información de rate limits desde headers de respuesta
            await self.make_request("GET", "/me")
            
            return {
                'rate_limit_minute': RATE_LIMITS["graph"]["requests_per_minute"],
                'rate_limit_day': RATE_LIMITS["graph"]["requests_per_day"],
                'current_usage': 'implementation_needed',  # Requiere tracking personalizado
                'reset_time': 'implementation_needed'
            }
        except Exception as e:
            logger.error(f"Error obteniendo cuota de API: {str(e)}")
            return {'error': str(e)}
    
    async def export_user_data(self, user_id: str, format_type: str = "json") -> Dict:
        """Exportar datos de usuario para cumplimiento GDPR"""
        try:
            user_data = {}
            
            # Información básica del usuario
            user_data['user'] = await self.get_user(user_id)
            
            # Archivos del usuario
            files_response = await self.list_files(top=1000)
            user_data['files'] = files_response.get('value', [])
            
            # Mensajes de correo
            messages_response = await self.list_messages(top=1000)
            user_data['messages'] = messages_response.get('value', [])
            
            # Eventos del calendario
            events_response = await self.list_events(top=1000)
            user_data['events'] = events_response.get('value', [])
            
            logger.info(f"Data export completed for user {user_id}")
            return {
                'status': 'completed',
                'user_id': user_id,
                'export_format': format_type,
                'data': user_data,
                'exported_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error exporting user data for {user_id}: {str(e)}")
            return {
                'status': 'failed',
                'user_id': user_id,
                'error': str(e),
                'exported_at': datetime.utcnow().isoformat()
            }


class GraphAPIError(Exception):
    """Excepción para errores de Graph API"""
    pass


class RetryableError(Exception):
    """Excepción para errores que permiten retry"""
    pass