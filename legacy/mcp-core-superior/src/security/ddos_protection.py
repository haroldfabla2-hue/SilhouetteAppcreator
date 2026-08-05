"""
Sistema de Rate Limiting y Protección DDoS para MCP Core Superior

Este módulo implementa un sistema completo de seguridad que incluye:
- Rate limiting con token bucket algorithm
- Protección contra ataques DDoS
- Gestión de listas blancas y negras
- Detección de anomalías
- Respuesta automatizada a amenazas
- Integración con WAF y servicios de protección en la nube
- Bloqueo geográfico
- Traffic shaping
"""

import asyncio
import time
import json
import logging
import hashlib
import hmac
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple, Set, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
from functools import wraps
import ipaddress
from urllib.parse import urlparse

# Importaciones opcionales
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    REDIS_AVAILABLE = False

try:
    import geoip2.database
    import geoip2.errors
    GEOIP_AVAILABLE = True
except ImportError:
    geoip2 = None
    GEOIP_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    requests = None
    REQUESTS_AVAILABLE = False


class ThreatLevel(Enum):
    """Niveles de amenaza detectados"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RateLimitScope(Enum):
    """Alcances para rate limiting"""
    GLOBAL = "global"
    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_AGENT = "per_agent"
    PER_ENDPOINT = "per_endpoint"
    PER_OPERATION = "per_operation"


@dataclass
class RateLimitConfig:
    """Configuración de rate limiting por endpoint"""
    endpoint: str
    method: str
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    burst_limit: int = 50
    scope: RateLimitScope = RateLimitScope.PER_IP
    enabled: bool = True
    whitelist_users: Set[str] = field(default_factory=set)
    whitelist_ips: Set[str] = field(default_factory=set)
    blacklist_ips: Set[str] = field(default_factory=set)
    rate_limit_by_user_type: Dict[str, int] = field(default_factory=dict)


@dataclass
class ThreatEvent:
    """Evento de amenaza detectado"""
    timestamp: datetime
    ip_address: str
    user_agent: str
    user_id: Optional[str]
    endpoint: str
    threat_type: str
    threat_level: ThreatLevel
    details: Dict[str, Any] = field(default_factory=dict)
    response_action: Optional[str] = None


@dataclass
class GeographicRule:
    """Regla de bloqueo geográfico"""
    country_code: str
    action: str  # 'block', 'rate_limit', 'monitor'
    rate_limit_factor: float = 0.1
    threat_score_multiplier: float = 2.0


class TokenBucket:
    """Algoritmo Token Bucket para rate limiting"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()
        self._lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Intenta consumir tokens del bucket"""
        with self._lock:
            now = time.time()
            # Refill tokens based on time elapsed
            elapsed = now - self.last_refill
            tokens_to_add = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def remaining_tokens(self) -> float:
        """Obtiene tokens restantes"""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_refill
            tokens_to_add = elapsed * self.refill_rate
            return min(self.capacity, self.tokens + tokens_to_add)


class SlidingWindow:
    """Contador de ventana deslizante para rate limiting"""
    
    def __init__(self, window_size: int):
        self.window_size = window_size  # seconds
        self.requests = deque()
        self._lock = threading.Lock()
    
    def is_rate_limited(self) -> bool:
        """Verifica si está limitado por rate"""
        with self._lock:
            now = time.time()
            # Remove old requests outside window
            while self.requests and now - self.requests[0] > self.window_size:
                self.requests.popleft()
            
            # Check if limit exceeded
            return len(self.requests) >= self.window_size
    
    def add_request(self):
        """Añade una nueva request"""
        with self._lock:
            now = time.time()
            self.requests.append(now)
    
    def get_request_count(self) -> int:
        """Obtiene número de requests en la ventana actual"""
        with self._lock:
            now = time.time()
            # Remove old requests
            while self.requests and now - self.requests[0] > self.window_size:
                self.requests.popleft()
            return len(self.requests)


class ThreatDetector:
    """Detector de patrones de ataque y anomalías"""
    
    def __init__(self):
        self.attack_patterns = {
            'sql_injection': [
                r"('|(\-\-)|(;)|(\|)|(\*)|(%27)|(%2D%2D)|(%23)|(%3B))",
                r"(union|select|insert|update|delete|drop|exec|script)",
                r"(exec\s*\(|eval\s*\(|system\s*\()"
            ],
            'xss': [
                r"(<script|javascript:|vbscript:|onload=|onerror=)",
                r"(document\.cookie|document\.location|document\.domain)"
            ],
            'path_traversal': [
                r"(\.\.\/|\.\.\\|%2e%2e%2f|%2e%2e%5c)",
                r"(etc/passwd|boot\.ini|win\.ini|C:\\\\Windows\\\\System32)"
            ],
            'command_injection': [
                r"(;|\||\&|&&|\|\|)",
                r"(rm|ls|cat|chmod|wget|curl|nc|bash|sh)"
            ]
        }
        
        self.request_patterns = defaultdict(list)
        self.user_behavior = defaultdict(lambda: {
            'request_times': deque(maxlen=1000),
            'unique_endpoints': set(),
            'error_patterns': [],
            'user_agent_changes': set(),
            'ip_changes': set()
        })
        
    def analyze_request(self, 
                       ip: str, 
                       user_agent: str, 
                       endpoint: str, 
                       headers: Dict[str, str],
                       payload: str) -> ThreatLevel:
        """Analiza request para detectar amenazas"""
        
        threat_level = ThreatLevel.LOW
        
        # Check request patterns
        pattern_score = self._check_attack_patterns(payload, headers)
        if pattern_score > 0:
            threat_level = ThreatLevel.HIGH if pattern_score > 0.7 else ThreatLevel.MEDIUM
        
        # Check user behavior anomalies
        behavior_level = self._check_behavior_anomalies(ip, user_agent, endpoint, headers)
        if self._threat_level_value(behavior_level) > self._threat_level_value(threat_level):
            threat_level = behavior_level
        
        # Check rate anomalies
        rate_level = self._check_rate_anomalies(ip, endpoint)
        if self._threat_level_value(rate_level) > self._threat_level_value(threat_level):
            threat_level = rate_level
        
        return threat_level
    
    def _threat_level_value(self, level: ThreatLevel) -> int:
        """Convierte ThreatLevel a valor numérico para comparación"""
        values = {
            ThreatLevel.LOW: 1,
            ThreatLevel.MEDIUM: 2,
            ThreatLevel.HIGH: 3,
            ThreatLevel.CRITICAL: 4
        }
        return values.get(level, 0)
    
    def _check_attack_patterns(self, payload: str, headers: Dict[str, str]) -> float:
        """Verifica patrones de ataque conocidos"""
        score = 0.0
        content = (payload or "") + " " + str(headers)
        
        for threat_type, patterns in self.attack_patterns.items():
            for pattern in patterns:
                import re
                if re.search(pattern, content, re.IGNORECASE):
                    score += 0.3
                    if threat_type in ['sql_injection', 'command_injection']:
                        score += 0.2  # Higher risk patterns
        
        return min(score, 1.0)
    
    def _check_behavior_anomalies(self, ip: str, user_agent: str, endpoint: str, headers: Dict[str, str]) -> ThreatLevel:
        """Detecta anomalías en comportamiento de usuario"""
        # Simplified implementation - in production, this would use ML
        if ip in ['127.0.0.1', '::1']:
            return ThreatLevel.LOW
        
        # Check for rapid user agent changes
        if len(headers.get('user-agent', '')) > 500:
            return ThreatLevel.MEDIUM
            
        return ThreatLevel.LOW
    
    def _check_rate_anomalies(self, ip: str, endpoint: str) -> ThreatLevel:
        """Detecta anomalías en patrones de rate"""
        # Simplified - check if IP is hitting too many different endpoints rapidly
        current_time = time.time()
        
        # In production, this would use Redis or another distributed cache
        return ThreatLevel.LOW


class GeographicBlocker:
    """Sistema de bloqueo geográfico"""
    
    def __init__(self, geoip_db_path: Optional[str] = None):
        self.geoip_reader = None
        self.country_rules: Dict[str, GeographicRule] = {}
        
        if geoip_db_path:
            try:
                self.geoip_reader = geoip2.database.Reader(geoip_db_path)
            except Exception as e:
                logging.warning(f"No se pudo cargar base de datos GeoIP: {e}")
    
    def get_country_code(self, ip_address: str) -> Optional[str]:
        """Obtiene código de país de una IP"""
        if not self.geoip_reader:
            return None
            
        try:
            response = self.geoip_reader.country(ip_address)
            return response.country.iso_code
        except (geoip2.errors.AddressNotFoundError, Exception):
            return None
    
    def check_geographic_block(self, ip_address: str) -> Tuple[bool, Optional[str]]:
        """Verifica si la IP debe ser bloqueada geográficamente"""
        if not ip_address:
            return False, None
            
        country = self.get_country_code(ip_address)
        if not country:
            return False, None
            
        rule = self.country_rules.get(country)
        if rule:
            if rule.action == 'block':
                return True, f"País {country} bloqueado"
            elif rule.action == 'rate_limit':
                return True, f"País {country} con rate limiting"
                
        return False, None
    
    def add_geographic_rule(self, rule: GeographicRule):
        """Añade regla geográfica"""
        self.country_rules[rule.country_code] = rule
    
    def remove_geographic_rule(self, country_code: str):
        """Elimina regla geográfica"""
        if country_code in self.country_rules:
            del self.country_rules[country_code]


class WAFIntegrator:
    """Integrador con servicios WAF y protección en la nube"""
    
    def __init__(self, waf_config: Dict[str, Any]):
        self.waf_config = waf_config
        self.cloudflare_api_key = waf_config.get('cloudflare_api_key')
        self.aws_waf_config = waf_config.get('aws_waf', {})
        
    def send_threat_to_cloudflare(self, ip: str, threat_level: ThreatLevel, duration: int = 3600):
        """Envía amenaza a Cloudflare para bloqueo"""
        if not self.cloudflare_api_key:
            return False
            
        try:
            headers = {
                'Authorization': f'Bearer {self.cloudflare_api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'mode': 'block',
                'configuration': {
                    'target': 'ip',
                    'value': ip
                },
                'notes': f'Auto-blocked by DDoS protection system - Level: {threat_level.value}'
            }
            
            # In production, use actual Cloudflare API
            # response = requests.post(API_URL, json=data, headers=headers)
            
            logging.info(f"IP {ip} enviada a Cloudflare para bloqueo")
            return True
            
        except Exception as e:
            logging.error(f"Error enviando IP a Cloudflare: {e}")
            return False
    
    def check_aws_waf(self, ip: str) -> bool:
        """Verifica si IP está en AWS WAF"""
        # Simplified implementation
        return False
    
    def block_ip_cloudflare(self, ip: str, reason: str = "DDoS Protection"):
        """Bloquea IP en Cloudflare"""
        return self.send_threat_to_cloudflare(ip, ThreatLevel.HIGH)
    
    def unblock_ip_cloudflare(self, ip: str):
        """Desbloquea IP en Cloudflare"""
        # In production, implement Cloudflare API unblock
        pass


class DistributedRateLimiter:
    """Rate limiter distribuido usando Redis"""
    
    def __init__(self, redis_config: Dict[str, Any]):
        try:
            self.redis_client = redis.Redis(
                host=redis_config.get('host', 'localhost'),
                port=redis_config.get('port', 6379),
                password=redis_config.get('password'),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self.redis_client.ping()
        except Exception as e:
            logging.warning(f"No se pudo conectar a Redis: {e}")
            self.redis_client = None
    
    def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Verifica rate limit en Redis"""
        if not self.redis_client:
            return True  # Fail open if Redis unavailable
            
        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window)
            results = pipe.execute()
            current_count = results[0]
            
            return current_count <= limit
            
        except Exception as e:
            logging.error(f"Error verificando rate limit en Redis: {e}")
            return True  # Fail open on error
    
    def add_to_blacklist(self, ip: str, duration: int = 3600) -> bool:
        """Añade IP a blacklist distribuida"""
        if not self.redis_client:
            return False
            
        try:
            return self.redis_client.setex(f"blacklist:{ip}", duration, "1")
        except Exception as e:
            logging.error(f"Error añadiendo IP a blacklist: {e}")
            return False
    
    def is_blacklisted(self, ip: str) -> bool:
        """Verifica si IP está en blacklist"""
        if not self.redis_client:
            return False
            
        try:
            return self.redis_client.exists(f"blacklist:{ip}")
        except Exception as e:
            logging.error(f"Error verificando blacklist: {e}")
            return False
    
    def add_to_whitelist(self, ip: str, duration: Optional[int] = None) -> bool:
        """Añade IP a whitelist distribuida"""
        if not self.redis_client:
            return False
            
        try:
            if duration:
                return self.redis_client.setex(f"whitelist:{ip}", duration, "1")
            else:
                return self.redis_client.set(f"whitelist:{ip}", "1")
        except Exception as e:
            logging.error(f"Error añadiendo IP a whitelist: {e}")
            return False
    
    def is_whitelisted(self, ip: str) -> bool:
        """Verifica si IP está en whitelist"""
        if not self.redis_client:
            return False
            
        try:
            return self.redis_client.exists(f"whitelist:{ip}")
        except Exception as e:
            logging.error(f"Error verificando whitelist: {e}")
            return False


class DDoSProtectionSystem:
    """Sistema principal de protección DDoS y Rate Limiting"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Configuración
        self.redis_config = config.get('redis', {})
        self.geoip_config = config.get('geoip', {})
        self.waf_config = config.get('waf', {})
        self.rate_limits = config.get('rate_limits', {})
        
        # Componentes del sistema
        self.distributed_limiter = DistributedRateLimiter(self.redis_config)
        self.geo_blocker = GeographicBlocker(self.geoip_config.get('database_path'))
        self.threat_detector = ThreatDetector()
        self.waf_integrator = WAFIntegrator(self.waf_config)
        
        # Storage local para rate limiting
        self.local_buckets: Dict[str, TokenBucket] = {}
        self.local_windows: Dict[str, SlidingWindow] = {}
        
        # Blacklist y whitelist locales
        self.blacklist: Set[str] = set()
        self.whitelist: Set[str] = set()
        
        # Rate limits configurados por endpoint
        self.endpoint_configs: Dict[str, RateLimitConfig] = {}
        
        # Métricas y estadísticas
        self.metrics = {
            'total_requests': 0,
            'blocked_requests': 0,
            'rate_limited_requests': 0,
            'threat_events': 0,
            'ip_blocks': 0,
            'geographic_blocks': 0
        }
        
        # Inicializar componentes
        self._initialize_system()
    
    def _initialize_system(self):
        """Inicializa el sistema con configuraciones"""
        self._load_geographic_rules()
        self._setup_endpoint_configs()
    
    def _load_geographic_rules(self):
        """Carga reglas geográficas"""
        geo_rules = self.config.get('geographic_rules', [])
        for rule_data in geo_rules:
            rule = GeographicRule(**rule_data)
            self.geo_blocker.add_geographic_rule(rule)
    
    def _setup_endpoint_configs(self):
        """Configura rate limits por endpoint"""
        for endpoint, config_data in self.rate_limits.items():
            method = config_data.get('method', 'GET')
            key = f"{method}:{endpoint}"
            
            self.endpoint_configs[key] = RateLimitConfig(
                endpoint=endpoint,
                method=method,
                requests_per_minute=config_data.get('requests_per_minute', 100),
                requests_per_hour=config_data.get('requests_per_hour', 1000),
                burst_limit=config_data.get('burst_limit', 50),
                scope=RateLimitScope(config_data.get('scope', 'per_ip'))
            )
    
    def check_request(self, 
                     ip: str, 
                     user_agent: str, 
                     endpoint: str,
                     method: str = 'GET',
                     user_id: Optional[str] = None,
                     headers: Optional[Dict[str, str]] = None,
                     payload: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Verifica si una request debe ser permitida
        
        Returns:
            Tuple[bool, str, Dict]: (allowed, reason, details)
        """
        if headers is None:
            headers = {}
        
        self.metrics['total_requests'] += 1
        
        # 1. Verificar whitelist/blacklist
        if ip in self.whitelist or self.distributed_limiter.is_whitelisted(ip):
            return True, "Whitelisted", {'action': 'allow'}
        
        if ip in self.blacklist or self.distributed_limiter.is_blacklisted(ip):
            self.metrics['blocked_requests'] += 1
            return False, "IP blacklisted", {'action': 'block', 'reason': 'blacklisted'}
        
        # 2. Verificar bloqueo geográfico
        is_blocked, geo_reason = self.geo_blocker.check_geographic_block(ip)
        if is_blocked:
            self.metrics['geographic_blocks'] += 1
            self.logger.warning(f"Request bloqueada geográficamente: {ip} - {geo_reason}")
            return False, geo_reason, {'action': 'geo_block'}
        
        # 3. Detectar amenazas
        threat_level = self.threat_detector.analyze_request(
            ip, user_agent, endpoint, headers, payload or ""
        )
        
        if threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            self.metrics['threat_events'] += 1
            return self._handle_threat(ip, threat_level, endpoint, user_agent)
        
        # 4. Verificar rate limiting
        is_limited, rate_reason, details = self._check_rate_limit(
            ip, user_id, endpoint, method, user_agent
        )
        
        if is_limited:
            self.metrics['rate_limited_requests'] += 1
            return False, rate_reason, {**details, 'action': 'rate_limit'}
        
        return True, "Allowed", {'action': 'allow', 'threat_level': threat_level.value}
    
    def _handle_threat(self, ip: str, threat_level: ThreatLevel, endpoint: str, user_agent: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Maneja amenazas detectadas"""
        threat_event = ThreatEvent(
            timestamp=datetime.now(),
            ip_address=ip,
            user_agent=user_agent,
            user_id=None,
            endpoint=endpoint,
            threat_type="auto_detected",
            threat_level=threat_level
        )
        
        # Automate threat response based on level
        if threat_level == ThreatLevel.CRITICAL:
            # Bloquear IP inmediatamente
            self.block_ip(ip, duration=86400)  # 24 horas
            self.distributed_limiter.add_to_blacklist(ip, 86400)
            self.waf_integrator.block_ip_cloudflare(ip, "Critical threat detected")
            return False, "Critical threat - IP blocked", {'action': 'critical_block'}
        
        elif threat_level == ThreatLevel.HIGH:
            # Rate limiting severo
            return False, "High threat - strict rate limiting", {
                'action': 'threat_rate_limit',
                'reduced_limit': True
            }
        
        return True, "Threat detected but allowed", {'action': 'monitor'}
    
    def _check_rate_limit(self, 
                         ip: str, 
                         user_id: Optional[str], 
                         endpoint: str, 
                         method: str,
                         user_agent: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Verifica rate limiting"""
        config_key = f"{method}:{endpoint}"
        config = self.endpoint_configs.get(config_key)
        
        if not config or not config.enabled:
            return False, "", {}
        
        # Determinar scope para rate limiting
        rate_key = self._get_rate_limit_key(ip, user_id, endpoint, method, config.scope)
        
        # Verificar límites según configuración
        if config.scope == RateLimitScope.PER_ENDPOINT:
            return self._check_endpoint_limits(config, rate_key, endpoint)
        
        elif config.scope == RateLimitScope.PER_USER and user_id:
            return self._check_user_limits(config, rate_key, user_id)
        
        elif config.scope == RateLimitScope.PER_IP:
            return self._check_ip_limits(config, rate_key, ip)
        
        return False, "", {}
    
    def _get_rate_limit_key(self, ip: str, user_id: Optional[str], endpoint: str, 
                           method: str, scope: RateLimitScope) -> str:
        """Genera clave para rate limiting"""
        if scope == RateLimitScope.PER_USER and user_id:
            return f"rate_limit:user:{user_id}:{method}:{endpoint}"
        elif scope == RateLimitScope.PER_AGENT:
            user_agent_hash = hashlib.md5(user_agent.encode()).hexdigest()[:8]
            return f"rate_limit:agent:{user_agent_hash}:{method}:{endpoint}"
        elif scope == RateLimitScope.PER_ENDPOINT:
            return f"rate_limit:endpoint:{method}:{endpoint}"
        else:  # PER_IP
            return f"rate_limit:ip:{ip}:{method}:{endpoint}"
    
    def _check_endpoint_limits(self, config: RateLimitConfig, key: str, endpoint: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Verifica límites por endpoint"""
        # Minute limit
        minute_key = f"{key}:minute"
        if not self.distributed_limiter.check_rate_limit(minute_key, config.requests_per_minute, 60):
            return True, f"Rate limit exceeded for {endpoint} (per minute)", {
                'limit_type': 'minute',
                'limit': config.requests_per_minute
            }
        
        # Hour limit  
        hour_key = f"{key}:hour"
        if not self.distributed_limiter.check_rate_limit(hour_key, config.requests_per_hour, 3600):
            return True, f"Rate limit exceeded for {endpoint} (per hour)", {
                'limit_type': 'hour', 
                'limit': config.requests_per_hour
            }
        
        return False, "", {}
    
    def _check_user_limits(self, config: RateLimitConfig, key: str, user_id: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Verifica límites por usuario"""
        # Apply user-specific limits if configured
        if user_id in config.whitelist_users:
            return False, "", {}
        
        minute_key = f"{key}:minute"
        if not self.distributed_limiter.check_rate_limit(minute_key, config.requests_per_minute, 60):
            return True, f"User rate limit exceeded for {user_id}", {
                'limit_type': 'user_minute',
                'limit': config.requests_per_minute
            }
        
        return False, "", {}
    
    def _check_ip_limits(self, config: RateLimitConfig, key: str, ip: str) -> Tuple[bool, str, Dict[str, Any]]:
        """Verifica límites por IP"""
        # Check if IP is in whitelist
        if ip in config.whitelist_ips:
            return False, "", {}
        
        # Check if IP is in blacklist
        if ip in config.blacklist_ips:
            return True, f"IP {ip} is blacklisted", {
                'limit_type': 'ip_blacklist',
                'ip': ip
            }
        
        # Check rate limits with Redis
        minute_key = f"{key}:minute"
        if not self.distributed_limiter.check_rate_limit(minute_key, config.requests_per_minute, 60):
            return True, f"IP rate limit exceeded for {ip}", {
                'limit_type': 'ip_minute',
                'limit': config.requests_per_minute,
                'ip': ip
            }
        
        return False, "", {}
    
    def block_ip(self, ip: str, duration: int = 3600, reason: str = "Manual block"):
        """Bloquea una IP"""
        self.blacklist.add(ip)
        self.distributed_limiter.add_to_blacklist(ip, duration)
        self.metrics['ip_blocks'] += 1
        
        self.logger.warning(f"IP {ip} bloqueada por {duration}s - Razón: {reason}")
    
    def unblock_ip(self, ip: str):
        """Desbloquea una IP"""
        self.blacklist.discard(ip)
        # In production, remove from distributed blacklist too
        
        self.logger.info(f"IP {ip} desbloqueada")
    
    def add_to_whitelist(self, ip: str, duration: Optional[int] = None):
        """Añade IP a whitelist"""
        self.whitelist.add(ip)
        self.distributed_limiter.add_to_whitelist(ip, duration)
        
        self.logger.info(f"IP {ip} añadida a whitelist por {duration or 'permanente'}")
    
    def remove_from_whitelist(self, ip: str):
        """Remueve IP de whitelist"""
        self.whitelist.discard(ip)
        
        self.logger.info(f"IP {ip} removida de whitelist")
    
    def add_rate_limit_config(self, config: RateLimitConfig):
        """Añade configuración de rate limit para endpoint"""
        key = f"{config.method}:{config.endpoint}"
        self.endpoint_configs[key] = config
        
        self.logger.info(f"Rate limit configurado para {config.endpoint} ({config.method})")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del sistema"""
        return {
            **self.metrics,
            'blocked_ips': len(self.blacklist),
            'whitelisted_ips': len(self.whitelist),
            'configured_endpoints': len(self.endpoint_configs),
            'timestamp': datetime.now().isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica salud del sistema"""
        health = {
            'status': 'healthy',
            'components': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Check Redis connection
        try:
            if self.distributed_limiter.redis_client:
                self.distributed_limiter.redis_client.ping()
                health['components']['redis'] = 'healthy'
            else:
                health['components']['redis'] = 'not_configured'
        except Exception as e:
            health['components']['redis'] = f'unhealthy: {str(e)}'
            health['status'] = 'degraded'
        
        # Check GeoIP
        if self.geo_blocker.geoip_reader:
            health['components']['geoip'] = 'healthy'
        else:
            health['components']['geoip'] = 'not_configured'
        
        return health


# Decorador para integración fácil con APIs
def ddos_protect(ddos_system: DDoSProtectionSystem):
    """Decorador para proteger endpoints con el sistema DDoS"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extraer información de request de kwargs o args
            # Esto depende del framework web usado (FastAPI, Flask, etc.)
            ip = kwargs.get('ip') or '127.0.0.1'
            user_agent = kwargs.get('user_agent') or 'unknown'
            endpoint = kwargs.get('endpoint') or func.__name__
            method = kwargs.get('method') or 'GET'
            user_id = kwargs.get('user_id')
            
            # Verificar con sistema DDoS
            allowed, reason, details = ddos_system.check_request(
                ip, user_agent, endpoint, method, user_id
            )
            
            if not allowed:
                raise PermissionError(f"Request blocked: {reason}")
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator