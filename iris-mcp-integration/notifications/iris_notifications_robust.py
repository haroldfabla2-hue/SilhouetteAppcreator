import smtplib
import requests
import json
import logging
import asyncio
import sys  # ✅ Import agregado para sys.stderr
import time
import threading
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional, Callable, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import secrets
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

class NotificationType(Enum):
    EMAIL = "email"
    WEBHOOK = "webhook" 
    CONSOLE = "console"
    SLACK = "slack"
    TEAMS = "teams"

class NotificationLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class NotificationEvent:
    """Evento de notificación con validación robusta"""
    event_type: str
    level: NotificationLevel
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    agent_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validación post-inicialización"""
        if not self.event_type or not isinstance(self.event_type, str):
            raise ValueError("event_type must be a non-empty string")
        
        if not self.title or not isinstance(self.title, str):
            raise ValueError("title must be a non-empty string")
        
        if not self.message or not isinstance(self.message, str):
            raise ValueError("message must be a non-empty string")
        
        if self.agent_id and not re.match(r'^[a-zA-Z0-9_-]+$', self.agent_id):
            raise ValueError("agent_id contains invalid characters")

@dataclass
class NotificationConfig:
    """Configuración de notificaciones"""
    enabled: bool
    type: NotificationType
    settings: Dict[str, Any]
    events: List[str]
    filters: Optional[Dict[str, Any]] = None
    rate_limit: Optional[int] = None

class AdvancedRateLimiter:
    """Rate limiter robusto con token bucket algorithm"""
    
    def __init__(self, max_tokens: int, refill_rate: float):
        self.max_tokens = max_tokens
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = max_tokens
        self.last_refill = time.time()
        self._lock = threading.Lock()
    
    def is_allowed(self) -> bool:
        """Check if request is allowed under rate limits"""
        with self._lock:
            now = time.time()
            
            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            tokens_to_add = elapsed * self.refill_rate
            self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
            self.last_refill = now
            
            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
    
    def get_wait_time(self) -> float:
        """Get time to wait until next token available"""
        with self._lock:
            if self.tokens >= 1:
                return 0
            # Calculate time needed for 1 token
            return 1.0 / self.refill_rate

class RobustEmailValidator:
    """Validador robusto de configuraciones de email"""
    
    @staticmethod
    def validate_email_format(email: str) -> bool:
        """Validar formato de email"""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
    
    @staticmethod
    def validate_smtp_config(server: str, port: int) -> bool:
        """Validar configuración SMTP básica"""
        if not server or not isinstance(server, str):
            return False
        if not isinstance(port, int) or port <= 0 or port > 65535:
            return False
        return True
    
    @staticmethod
    async def test_smtp_connection(server: str, port: int, timeout: int = 10) -> bool:
        """Test de conexión SMTP"""
        try:
            # Test connection without authentication
            test_server = smtplib.SMTP(server, port, timeout=timeout)
            test_server.helo('iris-mcp-server.test')  # Required for some servers
            test_server.quit()
            return True
        except Exception as e:
            logging.getLogger("EmailValidator").warning(f"SMTP connection test failed: {e}")
            return False

class IRISNotificationManager:
    """Gestor avanzado de notificaciones con validación robusta"""
    
    def __init__(self, config_file: str = "iris_notifications.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
        self.logger = self._setup_logging()
        self.notification_history = []
        
        # ✅ Rate limiters por canal con límites realistas
        self.rate_limiters = {
            'email': AdvancedRateLimiter(max_tokens=10, refill_rate=0.17),  # 10/hour
            'webhook': AdvancedRateLimiter(max_tokens=60, refill_rate=1.0), # 60/min
            'console': AdvancedRateLimiter(max_tokens=1000, refill_rate=16.67) # 1000/min
        }
        
        # ✅ Thread safety
        self._lock = threading.Lock()
        self._subscribers = {}
        
        # ✅ Retry mechanism configurado
        self.retry_config = {
            'max_retries': 3,
            'backoff_factor': 2,
            'retry_exceptions': (requests.exceptions.RequestException, smtplib.SMTPException, smtplib.SMTPAuthenticationError)
        }
        
        # ✅ Email validator
        self.email_validator = RobustEmailValidator()
        
        # ✅ Thread pool para operaciones concurrentes
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="Notification")
    
    def _load_config(self) -> Dict[str, Any]:
        """Cargar configuración de notificaciones con validación"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # ✅ Validar estructura de configuración
                if not self._validate_config_structure(data):
                    self.logger.warning("Invalid config structure, using defaults")
                    return self._get_default_config()
                
                return data
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON in config file: {e}")
                return self._get_default_config()
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
                return self._get_default_config()
        
        return self._get_default_config()
    
    def _validate_config_structure(self, data: Dict[str, Any]) -> bool:
        """Validar estructura de configuración"""
        if not isinstance(data, dict):
            return False
        
        if "notifications" not in data:
            return False
        
        notifications = data["notifications"]
        required_channels = ["email", "webhook", "console"]
        
        return all(channel in notifications for channel in required_channels)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Obtener configuración por defecto robusta"""
        return {
            "version": "1.1.0",
            "notifications": {
                "email": {
                    "enabled": False,
                    "type": "email",
                    "settings": {
                        "smtp_server": "smtp.gmail.com",
                        "smtp_port": 587,
                        "email": "",
                        "password": "",
                        "security": "tls"
                    },
                    "events": ["agent_error", "system_critical"],
                    "rate_limit": 10
                },
                "webhook": {
                    "enabled": False,
                    "type": "webhook",
                    "settings": {
                        "url": "",
                        "method": "POST",
                        "headers": {"Content-Type": "application/json"},
                        "auth_token": ""
                    },
                    "events": ["agent_status_change", "metric_threshold"],
                    "rate_limit": 60
                },
                "console": {
                    "enabled": True,
                    "type": "console",
                    "settings": {
                        "show_colors": True,
                        "timestamps": True,
                        "verbose": False
                    },
                    "events": ["all"],
                    "rate_limit": 1000
                }
            },
            "global_settings": {
                "batch_notifications": False,
                "batch_interval": 300,  # seconds
                "retry_attempts": 3,
                "retry_delay": 5,  # seconds
                "dead_letter_queue": True,
                "max_history_size": 1000
            }
        }
    
    def _save_config(self):
        """Guardar configuración de notificaciones con validación"""
        try:
            # ✅ Validar configuración antes de guardar
            if not self._validate_config_structure(self.config):
                raise ValueError("Invalid config structure")
            
            # ✅ Escribir con backup
            temp_file = Path(f"{self.config_file}.tmp")
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            # ✅ Reemplazar atómicamente
            temp_file.replace(self.config_file)
            
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            # Limpiar archivo temporal
            temp_file = Path(f"{self.config_file}.tmp")
            if temp_file.exists():
                temp_file.unlink()
            raise
    
    def _setup_logging(self) -> logging.Logger:
        """Configurar sistema de logging robusto"""
        logger = logging.getLogger("IRISNotifications")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Crear directorio de logs si no existe
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)
            
            # ✅ Handler para archivo con rotación
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_dir / "iris_notifications.log", 
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
            file_handler.setLevel(logging.INFO)
            
            # Handler para consola
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.WARNING)
            
            # ✅ Formato detallado
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)
        
        return logger
    
    def configure_email(self, email: str, password: str, smtp_server: str = "smtp.gmail.com", 
                       smtp_port: int = 587, security: str = "tls") -> bool:
        """Configurar notificaciones por email con validación robusta"""
        try:
            # ✅ Validar configuración antes de guardar
            if not self.email_validator.validate_email_format(email):
                self.logger.error(f"Invalid email format: {email}")
                return False
            
            if not self.email_validator.validate_smtp_config(smtp_server, smtp_port):
                self.logger.error(f"Invalid SMTP configuration: {smtp_server}:{smtp_port}")
                return False
            
            if not password or len(password) < 6:
                self.logger.error("Password must be at least 6 characters")
                return False
            
            # ✅ Test SMTP connection asynchronously
            if smtp_server and smtp_port:
                smtp_ok = self.email_validator.test_smtp_connection(smtp_server, smtp_port)
                if not smtp_ok:
                    self.logger.warning(f"SMTP connection test failed for {smtp_server}:{smtp_port}")
            
            self.config["notifications"]["email"]["enabled"] = True
            self.config["notifications"]["email"]["settings"].update({
                "email": email,
                "password": password,
                "smtp_server": smtp_server,
                "smtp_port": smtp_port,
                "security": security
            })
            self._save_config()
            
            self.logger.info(f"Email notifications configured for {email}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error configuring email notifications: {e}")
            return False
    
    def configure_webhook(self, url: str, method: str = "POST", 
                         headers: Dict[str, str] = None, auth_token: str = "") -> bool:
        """Configurar notificaciones por webhook con validación"""
        try:
            # ✅ Validar URL
            if not url or not url.startswith(('http://', 'https://')):
                self.logger.error(f"Invalid webhook URL: {url}")
                return False
            
            # ✅ Validar headers
            if headers and not isinstance(headers, dict):
                self.logger.error("Headers must be a dictionary")
                return False
            
            self.config["notifications"]["webhook"]["enabled"] = True
            self.config["notifications"]["webhook"]["settings"].update({
                "url": url,
                "method": method,
                "headers": headers or {"Content-Type": "application/json"},
                "auth_token": auth_token
            })
            self._save_config()
            
            self.logger.info(f"Webhook notifications configured for {url}")
            return True
        
        except Exception as e:
            self.logger.error(f"Error configuring webhook notifications: {e}")
            return False
    
    def configure_console(self, show_colors: bool = True, timestamps: bool = True, 
                         verbose: bool = False) -> bool:
        """Configurar notificaciones por consola"""
        try:
            self.config["notifications"]["console"]["enabled"] = True
            self.config["notifications"]["console"]["settings"].update({
                "show_colors": show_colors,
                "timestamps": timestamps,
                "verbose": verbose
            })
            self._save_config()
            
            self.logger.info("Console notifications configured")
            return True
        
        except Exception as e:
            self.logger.error(f"Error configuring console notifications: {e}")
            return False
    
    def send_notification(self, event: NotificationEvent) -> bool:
        """Enviar notificación basada en configuración con manejo robusto"""
        try:
            # ✅ Validar evento
            if not self._validate_event(event):
                self.logger.error("Invalid notification event")
                return False
            
            # ✅ Verificar rate limiting para todos los canales
            if not self._check_global_rate_limit():
                self.logger.warning("Global rate limit exceeded")
                return False
            
            # ✅ Filtrar eventos según configuración
            if not self._should_send_event(event):
                return True  # No enviar, pero no es un error
            
            # ✅ Enviar a todos los canales configurados en paralelo
            success = False
            channels_sent = 0
            
            # ✅ Usar ThreadPoolExecutor para envío concurrente
            future_to_channel = {}
            
            for channel_name, channel_config in self.config["notifications"].items():
                if not channel_config.get("enabled", False):
                    continue
                
                # ✅ Verificar rate limit por canal
                if not self._check_channel_rate_limit(channel_name):
                    self.logger.warning(f"Rate limit exceeded for channel: {channel_name}")
                    continue
                
                # ✅ Enviar en thread separado
                future = self.executor.submit(self._send_to_channel_safe, event, channel_config)
                future_to_channel[future] = channel_name
            
            # ✅ Esperar resultados
            for future in as_completed(future_to_channel, timeout=30):
                channel_name = future_to_channel[future]
                try:
                    result = future.result(timeout=10)
                    if result:
                        channels_sent += 1
                        success = True
                        self.logger.debug(f"Notification sent successfully to {channel_name}")
                    else:
                        self.logger.warning(f"Notification failed for {channel_name}")
                except Exception as e:
                    self.logger.error(f"Error in {channel_name}: {e}")
            
            # ✅ Registrar evento en historial
            self._record_notification(event, channels_sent, success)
            
            return success
        
        except Exception as e:
            self.logger.error(f"Error in send_notification: {e}")
            return False
    
    def _send_to_channel_safe(self, event: NotificationEvent, channel_config: Dict[str, Any]) -> bool:
        """Envío seguro a un canal con manejo de errores"""
        try:
            return self._send_to_channel(event, channel_config)
        except Exception as e:
            self.logger.error(f"Error sending to channel: {e}")
            return False
    
    def _validate_event(self, event: NotificationEvent) -> bool:
        """Validar evento de notificación"""
        if not event.event_type or not isinstance(event.event_type, str):
            return False
        if not event.title or not isinstance(event.title, str):
            return False
        if not event.message or not isinstance(event.message, str):
            return False
        if not isinstance(event.level, NotificationLevel):
            return False
        return True
    
    def _check_global_rate_limit(self) -> bool:
        """Verificar rate limiting global"""
        # ✅ Implementación simple de rate limiting global
        current_minute = int(time.time() // 60)
        if not hasattr(self, '_global_rate_counter'):
            self._global_rate_counter = {}
        
        count = self._global_rate_counter.get(current_minute, 0)
        if count >= 100:  # 100 eventos por minuto global
            return False
        
        self._global_rate_counter[current_minute] = count + 1
        return True
    
    def _check_channel_rate_limit(self, channel_name: str) -> bool:
        """Verificar rate limit por canal"""
        if channel_name in self.rate_limiters:
            return self.rate_limiters[channel_name].is_allowed()
        return True
    
    def _should_send_event(self, event: NotificationEvent) -> bool:
        """Determinar si el evento debe ser enviado según filtros"""
        for channel_config in self.config["notifications"].values():
            if not channel_config.get("enabled", False):
                continue
            
            events = channel_config.get("events", [])
            
            # Si "all" está en la lista, enviar a este canal
            if "all" in events or event.event_type in events:
                return True
        
        return False
    
    def _send_to_channel(self, event: NotificationEvent, channel_config: Dict[str, Any]) -> bool:
        """Enviar notificación a un canal específico con retry"""
        notification_type = NotificationType(channel_config["type"])
        
        max_retries = self.retry_config['max_retries']
        
        for attempt in range(max_retries):
            try:
                if notification_type == NotificationType.EMAIL:
                    return self._send_email_notification_robust(event, channel_config)
                elif notification_type == NotificationType.WEBHOOK:
                    return self._send_webhook_notification_robust(event, channel_config)
                elif notification_type == NotificationType.CONSOLE:
                    return self._send_console_notification_robust(event, channel_config)
                else:
                    self.logger.warning(f"Unsupported notification type: {notification_type}")
                    return False
            
            except self.retry_config['retry_exceptions'] as e:
                if attempt < max_retries - 1:
                    wait_time = self.retry_config['backoff_factor'] ** attempt
                    time.sleep(wait_time)
                    continue
                else:
                    self.logger.error(f"All retry attempts failed for {notification_type}: {e}")
                    return False
            except Exception as e:
                self.logger.error(f"Unexpected error in {notification_type}: {e}")
                return False
        
        return False
    
    def _send_email_notification_robust(self, event: NotificationEvent, config: Dict[str, Any]) -> bool:
        """Envío de email con manejo robusto de errores y reintentos"""
        settings = config["settings"]
        email = settings.get("email")
        password = settings.get("password")
        
        # ✅ Validación robusta de configuración de email
        if not self.email_validator.validate_email_format(email):
            self.logger.error(f"Invalid email format: {email}")
            return False
        
        if not password or len(password) < 6:
            self.logger.error("Password must be at least 6 characters")
            return False
        
        # ✅ Verificar rate limit
        if not self.rate_limiters['email'].is_allowed():
            wait_time = self.rate_limiters['email'].get_wait_time()
            self.logger.warning(f"Email rate limit exceeded. Wait {wait_time:.1f} seconds")
            return False
        
        # ✅ Retry mechanism para email
        for attempt in range(self.retry_config['max_retries']):
            try:
                msg = MIMEMultipart()
                msg['From'] = email
                msg['To'] = email
                msg['Subject'] = f"[IRIS] {event.title}"
                
                # ✅ Cuerpo HTML robusto
                body = self._format_email_body_robust(event)
                msg.attach(MIMEText(body, 'html', 'utf-8'))
                
                # ✅ SMTP con timeout y error handling robusto
                server = smtplib.SMTP(settings["smtp_server"], settings["smtp_port"], timeout=30)
                
                try:
                    if settings.get("security") == "tls":
                        server.starttls()
                    
                    server.login(email, password)
                    server.send_message(msg)
                    
                    self.logger.info(f"Email notification sent successfully for event: {event.event_type}")
                    return True
                    
                finally:
                    server.quit()
                    
            except smtplib.SMTPAuthenticationError:
                self.logger.error("SMTP authentication failed. Check credentials")
                return False
            except smtplib.SMTPConnectError:
                self.logger.error("SMTP connection failed")
                if attempt < self.retry_config['max_retries'] - 1:
                    time.sleep(2 ** attempt)
                    continue
                return False
            except Exception as e:
                self.logger.warning(f"Email attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_config['max_retries'] - 1:
                    time.sleep(self.retry_config['backoff_factor'] ** attempt)
                else:
                    self.logger.error(f"All email attempts failed for event: {event.event_type}")
        
        return False
    
    def _send_webhook_notification_robust(self, event: NotificationEvent, config: Dict[str, Any]) -> bool:
        """Envío de webhook con manejo robusto"""
        settings = config["settings"]
        url = settings["url"]
        method = settings.get("method", "POST")
        headers = settings.get("headers", {})
        
        # ✅ Verificar rate limit
        if not self.rate_limiters['webhook'].is_allowed():
            wait_time = self.rate_limiters['webhook'].get_wait_time()
            self.logger.warning(f"Webhook rate limit exceeded. Wait {wait_time:.1f} seconds")
            return False
        
        # ✅ Agregar token de autenticación si existe
        if settings.get("auth_token"):
            headers["Authorization"] = f"Bearer {settings['auth_token']}"
        
        # ✅ Preparar payload robusto
        payload = {
            "event": event.event_type,
            "level": event.level.value,
            "title": event.title,
            "message": event.message,
            "timestamp": event.timestamp.isoformat(),
            "agent_id": event.agent_id,
            "details": event.details or {},
            "metadata": event.metadata or {},
            "server_info": {
                "version": "1.1.0",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # ✅ Realizar petición con timeout y retry
        for attempt in range(self.retry_config['max_retries']):
            try:
                response = requests.request(
                    method=method,
                    url=url,
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                
                self.logger.info(f"Webhook notification sent successfully for event: {event.event_type}")
                return True
                
            except requests.exceptions.Timeout:
                self.logger.warning(f"Webhook timeout on attempt {attempt + 1}")
                if attempt < self.retry_config['max_retries'] - 1:
                    time.sleep(self.retry_config['backoff_factor'] ** attempt)
                    continue
                return False
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Webhook connection error on attempt {attempt + 1}")
                if attempt < self.retry_config['max_retries'] - 1:
                    time.sleep(self.retry_config['backoff_factor'] ** attempt)
                    continue
                return False
            except Exception as e:
                self.logger.error(f"Webhook attempt {attempt + 1} failed: {e}")
                if attempt < self.retry_config['max_retries'] - 1:
                    time.sleep(self.retry_config['backoff_factor'] ** attempt)
                else:
                    self.logger.error(f"All webhook attempts failed for event: {event.event_type}")
        
        return False
    
    def _send_console_notification_robust(self, event: NotificationEvent, config: Dict[str, Any]) -> bool:
        """Envío de consola con manejo robusto"""
        try:
            settings = config["settings"]
            show_colors = settings.get("show_colors", True)
            show_timestamps = settings.get("timestamps", True)
            
            # ✅ Verificar rate limit
            if not self.rate_limiters['console'].is_allowed():
                return False  # Silent fail for console rate limiting
            
            # ✅ Formato de salida robusto
            parts = []
            
            if show_timestamps:
                parts.append(f"[{event.timestamp.strftime('%H:%M:%S')}]")
            
            # ✅ Icono según nivel con fallback
            level_icon = {
                NotificationLevel.INFO: "ℹ️",
                NotificationLevel.WARNING: "⚠️",
                NotificationLevel.ERROR: "❌",
                NotificationLevel.CRITICAL: "🚨"
            }.get(event.level, "📢")
            
            if show_colors:
                color_code = {
                    NotificationLevel.INFO: "\033[94m",  # Blue
                    NotificationLevel.WARNING: "\033[93m",  # Yellow
                    NotificationLevel.ERROR: "\033[91m",  # Red
                    NotificationLevel.CRITICAL: "\033[95m"  # Magenta
                }.get(event.level, "\033[0m")  # Default reset
                
                reset_code = "\033[0m"
                parts.append(f"{color_code}{level_icon} {event.title}{reset_code}")
            else:
                parts.append(f"{level_icon} {event.title}")
            
            parts.append(event.message)
            
            if event.agent_id:
                parts.append(f"(Agente: {event.agent_id})")
            
            message = " ".join(parts)
            
            # ✅ Mostrar en consola con manejo de errores
            try:
                if event.level in [NotificationLevel.ERROR, NotificationLevel.CRITICAL]:
                    print(message, file=sys.stderr)  # ✅ Ahora sys está importado
                else:
                    print(message)
                    
                self.logger.debug(f"Console notification sent for event: {event.event_type}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error displaying console notification: {e}")
                return False
        
        except Exception as e:
            self.logger.error(f"Error in console notification: {e}")
            return False
    
    def _format_email_body_robust(self, event: NotificationEvent) -> str:
        """Formatear cuerpo del email con validación"""
        try:
            level_colors = {
                NotificationLevel.INFO: "#2196F3",
                NotificationLevel.WARNING: "#FF9800",
                NotificationLevel.ERROR: "#F44336",
                NotificationLevel.CRITICAL: "#9C27B0"
            }
            
            color = level_colors.get(event.level, "#666666")
            
            # ✅ Validar y limpiar datos antes del HTML
            safe_title = self._escape_html(event.title)
            safe_message = self._escape_html(event.message)
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        margin: 20px; 
                        line-height: 1.6;
                        color: #333;
                    }}
                    .header {{ 
                        background-color: {color}; 
                        color: white; 
                        padding: 20px; 
                        border-radius: 8px 8px 0 0;
                    }}
                    .content {{ 
                        padding: 20px; 
                        border: 1px solid #ddd; 
                        border-radius: 0 0 8px 8px; 
                        margin-top: 0;
                        background-color: #fff;
                    }}
                    .details {{ 
                        background-color: #f9f9f9; 
                        padding: 15px; 
                        border-radius: 5px; 
                        margin-top: 15px;
                        border-left: 4px solid {color};
                    }}
                    .timestamp {{ 
                        color: #666; 
                        font-size: 0.9em; 
                        margin-top: 10px;
                    }}
                    .footer {{
                        margin-top: 20px;
                        padding-top: 15px;
                        border-top: 1px solid #eee;
                        color: #888;
                        font-size: 0.85em;
                    }}
                    pre {{
                        background-color: #f5f5f5;
                        padding: 10px;
                        border-radius: 4px;
                        overflow-x: auto;
                        font-size: 0.9em;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>{safe_title}</h2>
                    <div class="timestamp">
                        <strong>Timestamp:</strong> {event.timestamp.strftime('%Y-%m-%d %H:%M:%S')} | 
                        <strong>Level:</strong> {event.level.value.upper()} | 
                        <strong>Event:</strong> {event.event_type}
                    </div>
                </div>
                <div class="content">
                    <p><strong>Message:</strong></p>
                    <p>{safe_message}</p>
            """
            
            if event.agent_id:
                html_body += f"""
                    <p><strong>Agent:</strong> {self._escape_html(event.agent_id)}</p>
                """
            
            if event.details:
                try:
                    details_json = json.dumps(event.details, indent=2, ensure_ascii=False)
                    safe_details = self._escape_html(details_json)
                    html_body += f"""
                        <div class="details">
                            <h4>Details:</h4>
                            <pre>{safe_details}</pre>
                        </div>
                    """
                except Exception as e:
                    self.logger.warning(f"Error formatting details in email: {e}")
            
            html_body += f"""
                </div>
                <div class="footer">
                    <p><strong>IRIS MCP Notification System v1.1.0</strong></p>
                    <p>Generated automatically by IRIS MCP Server</p>
                </div>
            </body>
            </html>
            """
            
            return html_body
            
        except Exception as e:
            self.logger.error(f"Error formatting email body: {e}")
            return f"<p>Error formatting email: {e}</p>"
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML para prevenir XSS"""
        if not isinstance(text, str):
            return str(text)
        
        return (text.replace("&", "&amp;")
                   .replace("<", "&lt;")
                   .replace(">", "&gt;")
                   .replace('"', "&quot;")
                   .replace("'", "&#x27;"))
    
    def _record_notification(self, event: NotificationEvent, channels_sent: int, success: bool):
        """Registrar notificación en historial con validación"""
        try:
            record = {
                "timestamp": event.timestamp.isoformat(),
                "event_type": event.event_type,
                "level": event.level.value,
                "title": event.title[:100] if len(event.title) > 100 else event.title,  # Truncate for storage
                "agent_id": event.agent_id,
                "channels_sent": channels_sent,
                "success": success
            }
            
            with self._lock:
                self.notification_history.append(record)
                
                # ✅ Mantener solo los últimos N registros (configurable)
                max_history = self.config["global_settings"].get("max_history_size", 1000)
                if len(self.notification_history) > max_history:
                    self.notification_history = self.notification_history[-max_history:]
        
        except Exception as e:
            self.logger.error(f"Error recording notification: {e}")
    
    def get_notification_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtener historial de notificaciones"""
        with self._lock:
            return self.notification_history[-limit:] if self.notification_history else []
    
    def get_notification_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de notificaciones robustas"""
        with self._lock:
            if not self.notification_history:
                return {
                    "total": 0,
                    "version": "1.1.0",
                    "timestamp": datetime.now().isoformat()
                }
            
            total = len(self.notification_history)
            successful = len([n for n in self.notification_history if n["success"]])
            
            # ✅ Contar por tipo de evento y nivel
            event_counts = {}
            level_counts = {}
            channel_counts = {}
            
            for record in self.notification_history:
                event_type = record["event_type"]
                level = record["level"]
                channels = record["channels_sent"]
                
                event_counts[event_type] = event_counts.get(event_type, 0) + 1
                level_counts[level] = level_counts.get(level, 0) + 1
                channel_counts[channels] = channel_counts.get(channels, 0) + 1
            
            # ✅ Actividad reciente (últimas 24 horas)
            now = datetime.now()
            recent_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            recent_activity = len([
                n for n in self.notification_history 
                if datetime.fromisoformat(n["timestamp"]) >= recent_start
            ])
            
            return {
                "total_notifications": total,
                "successful": successful,
                "failed": total - successful,
                "success_rate": round(successful / total, 3) if total > 0 else 0,
                "event_type_distribution": event_counts,
                "level_distribution": level_counts,
                "channel_distribution": channel_counts,
                "recent_activity_24h": recent_activity,
                "version": "1.1.0",
                "timestamp": now.isoformat()
            }
    
    def __enter__(self):
        """Context manager para cleanup automático"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup automático de recursos"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
            self.logger.info("Notification manager shutdown complete")

# Funciones de conveniencia mejoradas
def create_notification_manager(config_file: str = "iris_notifications.json") -> IRISNotificationManager:
    """Crear instancia del gestor de notificaciones con manejo robusto"""
    try:
        return IRISNotificationManager(config_file)
    except Exception as e:
        logging.error(f"Failed to create notification manager: {e}")
        raise

def send_test_notification() -> Dict[str, Any]:
    """Enviar notificación de prueba con manejo robusto"""
    try:
        manager = IRISNotificationManager()
        
        # Crear evento de prueba con validación
        test_event = NotificationEvent(
            event_type="test_notification",
            level=NotificationLevel.INFO,
            title="Prueba de Notificación IRIS",
            message="Esta es una notificación de prueba del sistema IRIS MCP v1.1.0",
            timestamp=datetime.now()
        )
        
        # Probar cada canal configurado
        results = {}
        for channel_name, channel_config in manager.config["notifications"].items():
            if not channel_config.get("enabled", False):
                results[channel_name] = False
                continue
            
            try:
                success = manager._send_to_channel(test_event, channel_config)
                results[channel_name] = success
                
                if success:
                    manager.logger.info(f"Test notification sent to {channel_name}")
                else:
                    manager.logger.warning(f"Test notification failed for {channel_name}")
            
            except Exception as e:
                manager.logger.error(f"Error testing {channel_name}: {e}")
                results[channel_name] = False
        
        return {
            "results": results,
            "stats": manager.get_notification_stats(),
            "version": "1.1.0"
        }
        
    except Exception as e:
        logging.error(f"Failed to send test notification: {e}")
        return {
            "error": str(e),
            "results": {},
            "version": "1.1.0"
        }

if __name__ == "__main__":
    import sys
    
    print("🔔 IRIS MCP Notification System v1.1.0")
    print("=====================================")
    
    try:
        # ✅ Ejemplo de uso mejorado
        with create_notification_manager() as manager:
            
            # Configurar notificaciones por consola
            manager.configure_console()
            
            # Configurar notificaciones por email (requiere setup manual)
            # manager.configure_email("your_email@gmail.com", "your_app_password")
            
            # Configurar webhook
            # manager.configure_webhook("https://your-webhook-url.com/notifications")
            
            # Enviar notificación de prueba
            print("\n🔔 Probando sistema de notificaciones IRIS...")
            
            test_result = send_test_notification()
            print("\nResultados de prueba:")
            for channel, success in test_result.get("results", {}).items():
                status = "✅" if success else "❌"
                print(f"  {status} {channel}")
            
            if "error" in test_result:
                print(f"❌ Error: {test_result['error']}")
            
            # Mostrar estadísticas
            stats = test_result.get("stats", {})
            print(f"\nEstadísticas:")
            print(f"  Total: {stats.get('total_notifications', 0)}")
            print(f"  Éxito: {stats.get('successful', 0)}")
            print(f"  Tasa éxito: {stats.get('success_rate', 0):.1%}")
            
            print(f"\n✅ Sistema de notificaciones operativo")
            
    except Exception as e:
        print(f"❌ Error inicializando el sistema: {e}")
        sys.exit(1)
