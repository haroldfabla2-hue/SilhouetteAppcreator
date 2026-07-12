"""
Middleware para integración del sistema de protección DDoS con frameworks web
"""

import asyncio
import time
import logging
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.middleware.base import RequestResponseEndpoint
from starlette.responses import Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS, HTTP_403_FORBIDDEN

from .ddos_protection import DDoSProtectionSystem, ThreatLevel


class DDoSMiddleware(BaseHTTPMiddleware):
    """
    Middleware para FastAPI que integra el sistema de protección DDoS
    """
    
    def __init__(
        self,
        app,
        ddos_system: DDoSProtectionSystem,
        exclude_paths: Optional[list] = None,
        custom_get_ip: Optional[Callable] = None,
        custom_get_user_id: Optional[Callable] = None
    ):
        super().__init__(app)
        self.ddos_system = ddos_system
        self.exclude_paths = exclude_paths or []
        self.custom_get_ip = custom_get_ip
        self.custom_get_user_id = custom_get_user_id
        
        self.logger = logging.getLogger(__name__)
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Skip excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Extract request information
        ip = self._extract_client_ip(request)
        user_agent = request.headers.get("user-agent", "unknown")
        endpoint = str(request.url.path)
        method = request.method
        
        # Extract user ID if available
        user_id = None
        if self.custom_get_user_id:
            try:
                user_id = await self.custom_get_user_id(request)
            except Exception as e:
                self.logger.warning(f"Error extracting user ID: {e}")
        
        # Get request body for analysis (limited size)
        payload = await self._extract_payload(request)
        
        # Check with DDoS protection system
        try:
            allowed, reason, details = self.ddos_system.check_request(
                ip=ip,
                user_agent=user_agent,
                endpoint=endpoint,
                method=method,
                user_id=user_id,
                headers=dict(request.headers),
                payload=payload
            )
            
            if not allowed:
                return self._create_blocked_response(reason, details)
            
            # Process request
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log request for monitoring
            self.logger.info(
                f"Request processed: {method} {endpoint} "
                f"- IP: {ip} - Time: {process_time:.3f}s"
            )
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            
            # Add rate limiting info headers
            response.headers["X-RateLimit-Remaining"] = str(details.get('remaining_tokens', 'unknown'))
            response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in DDoS middleware: {e}")
            # Fail open on error to avoid blocking legitimate traffic
            return await call_next(request)
    
    def _extract_client_ip(self, request: Request) -> str:
        """Extrae la IP real del cliente"""
        if self.custom_get_ip:
            return self.custom_get_ip(request)
        
        # FastIP detection (check common proxy headers)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # X-Forwarded-For can contain multiple IPs, get the first one
            ip = forwarded_for.split(",")[0].strip()
            return ip
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        client_ip = request.client.host if request.client else "unknown"
        return client_ip
    
    async def _extract_payload(self, request: Request, max_size: int = 1024) -> str:
        """Extrae payload para análisis (limitado por tamaño)"""
        try:
            # Only for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                body = await request.body()
                if len(body) <= max_size:
                    return body.decode('utf-8', errors='ignore')
                else:
                    return f"[BODY_TOO_LARGE:{len(body)}_BYTES]"
            return ""
        except Exception:
            return ""
    
    def _create_blocked_response(self, reason: str, details: Dict[str, Any]) -> Response:
        """Crea respuesta para request bloqueada"""
        if "blacklist" in reason.lower():
            status_code = HTTP_403_FORBIDDEN
            detail = "Access denied"
        else:
            status_code = HTTP_429_TOO_MANY_REQUESTS
            detail = "Rate limit exceeded"
        
        response_data = {
            "error": detail,
            "message": reason,
            "details": details,
            "timestamp": int(time.time())
        }
        
        return Response(
            content=response_data,
            status_code=status_code,
            media_type="application/json",
            headers={
                "Retry-After": "60",  # Retry after 1 minute
                "X-RateLimit-Limit": details.get('limit', 'unknown')
            }
        )


def create_ddos_middleware(
    app,
    ddos_system: DDoSProtectionSystem,
    exclude_paths: Optional[list] = None,
    get_user_from_token: Optional[Callable] = None
) -> DDoSMiddleware:
    """
    Factory function para crear middleware DDoS con configuración común
    """
    
    def get_user_id(request: Request) -> Optional[str]:
        """Extrae user ID del JWT token si está disponible"""
        if get_user_from_token:
            return get_user_from_token(request)
        return None
    
    def get_ip(request: Request) -> str:
        """Extrae IP real del cliente"""
        # Lógica personalizada para extracción de IP
        return request.client.host if request.client else "unknown"
    
    return DDoSMiddleware(
        app=app,
        ddos_system=ddos_system,
        exclude_paths=exclude_paths or [
            "/health",
            "/metrics", 
            "/docs",
            "/redoc",
            "/openapi.json"
        ],
        custom_get_ip=get_ip,
        custom_get_user_id=get_user_id
    )


class FlaskDDoSMiddleware:
    """
    Middleware para Flask que integra el sistema de protección DDoS
    """
    
    def __init__(
        self,
        app,
        ddos_system: DDoSProtectionSystem,
        exclude_paths: Optional[list] = None
    ):
        self.app = app
        self.ddos_system = ddos_system
        self.exclude_paths = exclude_paths or []
        
        # Wrap Flask app
        self.app.before_request(self._before_request)
    
    def _before_request(self):
        """Hook ejecutado antes de cada request"""
        from flask import request, g, jsonify
        
        # Skip excluded paths
        if request.path in self.exclude_paths:
            return
        
        # Extract request info
        ip = self._extract_client_ip()
        user_agent = request.headers.get('User-Agent', 'unknown')
        endpoint = request.path
        method = request.method
        
        # Extract payload for analysis
        payload = self._extract_payload()
        
        # Check with DDoS system
        allowed, reason, details = self.ddos_system.check_request(
            ip=ip,
            user_agent=user_agent,
            endpoint=endpoint,
            method=method,
            headers=dict(request.headers),
            payload=payload
        )
        
        if not allowed:
            g.blocked_response = {
                'error': 'Request blocked',
                'message': reason,
                'details': details
            }
            # Return blocked response immediately
            return jsonify(g.blocked_response), 429
    
    def _extract_client_ip(self) -> str:
        """Extrae la IP real del cliente"""
        from flask import request
        
        # Check proxy headers
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        return request.remote_addr or 'unknown'
    
    def _extract_payload(self, max_size: int = 1024) -> str:
        """Extrae payload para análisis"""
        from flask import request
        
        try:
            if request.method in ['POST', 'PUT', 'PATCH']:
                data = request.get_data()
                if len(data) <= max_size:
                    return data.decode('utf-8', errors='ignore')
                else:
                    return f"[BODY_TOO_LARGE:{len(data)}_BYTES]"
            return ""
        except Exception:
            return ""


class ASGIDDoSMiddleware:
    """
    Middleware genérico para ASGI applications
    """
    
    def __init__(
        self,
        app,
        ddos_system: DDoSProtectionSystem,
        exclude_paths: Optional[list] = None
    ):
        self.app = app
        self.ddos_system = ddos_system
        self.exclude_paths = exclude_paths or []
    
    async def __call__(self, scope, receive, send):
        """
        Handle ASGI request
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract request info from scope
        path = scope.get("path", "")
        method = scope.get("method", "GET")
        
        # Skip excluded paths
        if path in self.exclude_paths:
            await self.app(scope, receive, send)
            return
        
        # Extract headers
        headers_dict = {}
        for header_name, header_value in scope.get("headers", []):
            headers_dict[header_name.decode().lower()] = header_value.decode()
        
        # Get client IP
        client = scope.get("client")
        ip = client[0] if client else "unknown"
        
        user_agent = headers_dict.get("user-agent", "unknown")
        
        # Check with DDoS system
        allowed, reason, details = self.ddos_system.check_request(
            ip=ip,
            user_agent=user_agent,
            endpoint=path,
            method=method,
            headers=headers_dict
        )
        
        if not allowed:
            # Send blocked response
            response_body = f'{{"error": "{reason}"}}'.encode()
            response_headers = [
                (b"content-type", b"application/json"),
                (b"retry-after", b"60")
            ]
            
            await send({
                "type": "http.response.start",
                "status": 429,
                "headers": response_headers
            })
            
            await send({
                "type": "http.response.body",
                "body": response_body
            })
            return
        
        # Process normally
        await self.app(scope, receive, send)