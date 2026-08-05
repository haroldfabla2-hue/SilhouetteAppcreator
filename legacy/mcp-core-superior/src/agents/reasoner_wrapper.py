"""
Wrapper MCP para ReasonerAgent
Analiza intención del usuario y define estrategia inicial
"""
from typing import Dict, Any, List, Optional
import asyncio
import logging
from datetime import datetime

from .base_agent_wrapper import BaseAgentWrapper, AgentCapability
from ..core.exceptions import AgentException, handle_exceptions
from ..core.config import settings


class ReasonerAgentWrapper(BaseAgentWrapper):
    """
    Wrapper para ReasonerAgent
    
    Capacidades:
    - Análisis de intención del usuario
    - Definición de estrategia inicial
    - Enriquecimiento de contexto
    - Extracción de restricciones
    """
    
    def __init__(self):
        capabilities = [
            AgentCapability.INTENT_ANALYSIS,
            AgentCapability.STRATEGY_DEFINITION,
            AgentCapability.CONTEXT_ENRICHMENT
        ]
        
        super().__init__(
            agent_name="reasoner",
            capabilities=capabilities,
            max_concurrent=settings.max_concurrent_tools,
            timeout_seconds=settings.agent_timeout_seconds,
            retry_attempts=settings.agent_retry_attempts,
            retry_delay=settings.agent_retry_delay
        )
        
        self.logger = logging.getLogger("mcp.agents.reasoner")
    
    async def _initialize(self) -> None:
        """Inicialización específica del ReasonerAgent"""
        self.logger.info("Inicializando ReasonerAgent...")
        
        # Aquí se conectaría con el ReasonerAgent real del backend
        # Por ahora simulamos la inicialización
        await asyncio.sleep(0.1)
        
        self.logger.info("ReasonerAgent inicializado correctamente")
    
    async def process_request(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesar request de análisis de intención
        
        Args:
            request: Request del cliente
                - objective: Objetivo o tarea a realizar
                - context: Contexto adicional
                - conversation_id: ID de conversación para memoria
                - user_id: ID del usuario
            context: Contexto adicional
            
        Returns:
            Análisis de intención y estrategia definida
        """
        return await self.execute_operation(
            operation_name="analyze_intent",
            capability=AgentCapability.INTENT_ANALYSIS,
            operation_func=self._analyze_intent,
            request=request,
            context=context
        )
    
    @handle_exceptions
    async def _analyze_intent(
        self,
        request: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Implementación del análisis de intención"""
        
        objective = request.get("objective", "")
        user_context = request.get("context", {})
        conversation_id = request.get("conversation_id")
        user_id = request.get("user_id")
        
        if not objective:
            raise AgentException(
                message="Objective es requerido para análisis de intención",
                agent_name=self.agent_name,
                operation="analyze_intent",
                error_code="INVALID_REQUEST",
                details={"missing_field": "objective"}
            )
        
        self.logger.info(f"Analizando intención para: {objective[:100]}...")
        
        # Aquí se conectaría con el ReasonerAgent real
        # Por ahora simulamos el análisis
        
        # Simular tiempo de procesamiento
        await asyncio.sleep(0.1)
        
        # Análisis simulado
        analysis_result = {
            "objective": objective,
            "analysis": {
                "intent_type": self._classify_intent(objective),
                "complexity_level": self._assess_complexity(objective),
                "domain": self._identify_domain(objective),
                "requirements": self._extract_requirements(objective),
                "constraints": self._extract_constraints(objective, user_context),
                "success_criteria": self._define_success_criteria(objective),
                "estimated_effort": self._estimate_effort(objective)
            },
            "strategy": {
                "approach": self._define_approach(objective),
                "phases": self._plan_phases(objective),
                "dependencies": self._identify_dependencies(objective),
                "parallelization_possible": self._assess_parallelization(objective),
                "resource_requirements": self._assess_resources(objective),
                "risk_factors": self._assess_risks(objective)
            },
            "context": {
                "user_context": user_context,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "analysis_metadata": {
                    "reasoner_version": "1.0.0",
                    "model": "reasoner_advanced",
                    "confidence_score": 0.85
                }
            }
        }
        
        self.logger.info(
            f"Análisis completado - Tipo: {analysis_result['analysis']['intent_type']}, "
            f"Complejidad: {analysis_result['analysis']['complexity_level']}"
        )
        
        return analysis_result
    
    def _classify_intent(self, objective: str) -> str:
        """Clasificar tipo de intención del objetivo"""
        objective_lower = objective.lower()
        
        if any(word in objective_lower for word in ["analizar", "análisis", "evaluar"]):
            return "analysis"
        elif any(word in objective_lower for word in ["crear", "desarrollar", "generar", "build"]):
            return "creation"
        elif any(word in objective_lower for word in ["investigar", "buscar", "explorar", "research"]):
            return "research"
        elif any(word in objective_lower for word in ["programar", "codificar", "desarrollar", "implementar"]):
            return "development"
        elif any(word in objective_lower for word in ["optimizar", "mejorar", "enhance"]):
            return "optimization"
        elif any(word in objective_lower for word in ["automatizar", "automatización"]):
            return "automation"
        else:
            return "general"
    
    def _assess_complexity(self, objective: str) -> str:
        """Evaluar nivel de complejidad del objetivo"""
        # Análisis básico basado en longitud y palabras clave
        complexity_indicators = [
            "múltiple", "varios", "complejo", "avanzado", "integración",
            "multiple", "several", "complex", "advanced", "integration"
        ]
        
        objective_lower = objective.lower()
        indicator_count = sum(1 for indicator in complexity_indicators if indicator in objective_lower)
        
        if len(objective) > 200 or indicator_count >= 3:
            return "high"
        elif len(objective) > 100 or indicator_count >= 1:
            return "medium"
        else:
            return "low"
    
    def _identify_domain(self, objective: str) -> str:
        """Identificar dominio del objetivo"""
        objective_lower = objective.lower()
        
        domains = {
            "technology": ["desarrollo", "programación", "software", "web", "api", "tech"],
            "business": ["negocio", "ventas", "marketing", "estrategia", "business"],
            "data": ["datos", "análisis", "estadísticas", "métricas", "analytics"],
            "content": ["contenido", "documento", "escritura", "redacción", "content"],
            "research": ["investigación", "estudio", "paper", "academic", "research"],
            "finance": ["financiero", "presupuesto", "inversión", "finance", "financial"],
            "design": ["diseño", "ui", "ux", "visual", "interface", "design"]
        }
        
        for domain, keywords in domains.items():
            if any(keyword in objective_lower for keyword in keywords):
                return domain
        
        return "general"
    
    def _extract_requirements(self, objective: str) -> List[str]:
        """Extraer requisitos del objetivo"""
        # Análisis básico de requisitos
        requirements = []
        
        # Buscar patrones de requisitos
        import re
        requirement_patterns = [
            r"necesito\s+([^.]+)",
            r"requiere\s+([^.]+)",
            r"debe\s+([^.]+)",
            r"con\s+([^.]+)"
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, objective, re.IGNORECASE)
            requirements.extend(matches)
        
        # Si no se encuentran requisitos específicos, inferir
        if not requirements:
            requirements.append("Completar el objetivo especificado")
        
        return requirements[:5]  # Limitar a 5 requisitos
    
    def _extract_constraints(self, objective: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer restricciones del objetivo"""
        constraints = {
            "time": "No especificado",
            "budget": "No especificado", 
            "technology": "No especificado",
            "quality": "Estándar"
        }
        
        # Analizar contexto del usuario
        if user_context:
            if "deadline" in user_context:
                constraints["time"] = user_context["deadline"]
            if "budget" in user_context:
                constraints["budget"] = user_context["budget"]
            if "tech_stack" in user_context:
                constraints["technology"] = str(user_context["tech_stack"])
        
        # Buscar restricciones en el objetivo
        objective_lower = objective.lower()
        if "urgente" in objective_lower or "rápido" in objective_lower:
            constraints["time"] = "Urgente"
        if "presupuesto" in objective_lower:
            constraints["budget"] = "Limitado"
        
        return constraints
    
    def _define_success_criteria(self, objective: str) -> List[str]:
        """Definir criterios de éxito"""
        criteria = [
            "Objetivo completado satisfactoriamente",
            "Entrega en tiempo especificado",
            "Calidad conforme a estándares"
        ]
        
        # Añadir criterios específicos según el dominio
        objective_lower = objective.lower()
        if "análisis" in objective_lower:
            criteria.append("Análisis completo con insights accionables")
        if "desarrollo" in objective_lower or "crear" in objective_lower:
            criteria.append("Código funcional y bien documentado")
        if "investigación" in objective_lower:
            criteria.append("Investigación exhaustiva con fuentes confiables")
        
        return criteria
    
    def _estimate_effort(self, objective: str) -> str:
        """Estimar esfuerzo requerido"""
        complexity = self._assess_complexity(objective)
        objective_length = len(objective)
        
        if complexity == "high" or objective_length > 300:
            return "high"
        elif complexity == "medium" or objective_length > 150:
            return "medium"
        else:
            return "low"
    
    def _define_approach(self, objective: str) -> str:
        """Definir enfoque de trabajo"""
        intent_type = self._classify_intent(objective)
        complexity = self._assess_complexity(objective)
        
        approaches = {
            ("analysis", "high"): "Análisis profundo iterativo",
            ("analysis", "medium"): "Análisis sistemático",
            ("creation", "high"): "Desarrollo iterativo con validaciones",
            ("creation", "medium"): "Desarrollo directo",
            ("research", "high"): "Investigación exhaustiva multi-fuente",
            ("research", "medium"): "Investigación dirigida",
            ("development", "high"): "Desarrollo ágil con sprints",
            ("development", "medium"): "Desarrollo estructurado"
        }
        
        return approaches.get((intent_type, complexity), "Enfoque sistemático adaptable")
    
    def _plan_phases(self, objective: str) -> List[str]:
        """Planificar fases de ejecución"""
        intent_type = self._classify_intent(objective)
        
        base_phases = [
            "Preparación y configuración",
            "Ejecución principal",
            "Validación y revisión",
            "Entrega y documentación"
        ]
        
        # Añadir fases específicas según el tipo
        if intent_type == "research":
            base_phases.insert(1, "Recopilación de información")
            base_phases.insert(2, "Análisis y síntesis")
        elif intent_type == "development":
            base_phases.insert(1, "Diseño y arquitectura")
            base_phases.insert(2, "Implementación")
            base_phases.insert(3, "Testing y QA")
        
        return base_phases
    
    def _identify_dependencies(self, objective: str) -> List[str]:
        """Identificar dependencias"""
        dependencies = []
        
        objective_lower = objective.lower()
        
        # Dependencias técnicas
        if "api" in objective_lower:
            dependencies.append("Acceso a APIs externas")
        if "base de datos" in objective_lower or "database" in objective_lower:
            dependencies.append("Configuración de base de datos")
        if "web" in objective_lower:
            dependencies.append("Servicios de hosting/despliegue")
        
        # Dependencias de datos
        if "datos" in objective_lower or "data" in objective_lower:
            dependencies.append("Acceso a fuentes de datos")
        
        # Si no hay dependencias específicas
        if not dependencies:
            dependencies.append("Ninguna dependencia crítica identificada")
        
        return dependencies
    
    def _assess_parallelization(self, objective: str) -> bool:
        """Evaluar si es posible paralelización"""
        objective_lower = objective.lower()
        
        # Palabras que indican tareas independientes
        parallel_indicators = [
            "múltiple", "varios", "separados", "independiente",
            "multiple", "various", "separate", "independent"
        ]
        
        # Palabras que indican secuencialidad
        sequential_indicators = [
            "secuencial", "sucesivo", "dependiente", "primero",
            "sequential", "consecutive", "dependent", "first"
        ]
        
        if any(indicator in objective_lower for indicator in sequential_indicators):
            return False
        
        return any(indicator in objective_lower for indicator in parallel_indicators)
    
    def _assess_resources(self, objective: str) -> Dict[str, Any]:
        """Evaluar recursos necesarios"""
        resources = {
            "computational": "Standard",
            "memory": "Standard",
            "storage": "Standard",
            "network": "Standard",
            "specialized": []
        }
        
        objective_lower = objective.lower()
        
        # Recursos computacionales
        if "ml" in objective_lower or "machine learning" in objective_lower:
            resources["computational"] = "High"
            resources["specialized"].append("GPU/TPU para ML")
        if "análisis grande" in objective_lower or "big data" in objective_lower:
            resources["memory"] = "High"
            resources["storage"] = "High"
        
        # Recursos especializados
        if "web scraping" in objective_lower:
            resources["specialized"].append("Web scraping tools")
        if "api" in objective_lower:
            resources["specialized"].append("API access")
        
        return resources
    
    def _assess_risks(self, objective: str) -> List[Dict[str, Any]]:
        """Evaluar factores de riesgo"""
        risks = []
        
        complexity = self._assess_complexity(objective)
        
        if complexity == "high":
            risks.append({
                "factor": "Complejidad técnica",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Descomposición en tareas más pequeñas"
            })
        
        # Riesgos específicos por dominio
        domain = self._identify_domain(objective)
        
        if domain == "technology":
            risks.append({
                "factor": "Dependencia de tecnologías",
                "probability": "low",
                "impact": "medium",
                "mitigation": "Validar compatibilidad técnica temprana"
            })
        elif domain == "data":
            risks.append({
                "factor": "Calidad de datos",
                "probability": "medium",
                "impact": "high",
                "mitigation": "Validar calidad de fuentes de datos"
            })
        
        # Riesgo general si no se identifican específicos
        if not risks:
            risks.append({
                "factor": "Requisitos cambiantes",
                "probability": "low",
                "impact": "medium",
                "mitigation": "Validación temprana con usuario"
            })
        
        return risks
    
    # Métodos específicos de la interfaz MCP
    
    async def analyze_intent(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analizar intención del usuario
        
        Args:
            objective: Objetivo o tarea a realizar
            context: Contexto adicional
            conversation_id: ID de conversación
            user_id: ID del usuario
            
        Returns:
            Análisis de intención y estrategia definida
        """
        request = {
            "objective": objective,
            "context": context or {},
            "conversation_id": conversation_id,
            "user_id": user_id
        }
        
        return await self.process_request(request)
    
    async def get_status(self) -> Dict[str, Any]:
        """Obtener estado del ReasonerAgent"""
        base_status = super().get_status()
        base_status.update({
            "agent_type": "reasoner",
            "specialization": "Análisis de intención y definición de estrategia",
            "input_format": {
                "required": ["objective"],
                "optional": ["context", "conversation_id", "user_id"]
            },
            "output_format": {
                "analysis": "Análisis detallado del objetivo",
                "strategy": "Estrategia y plan inicial",
                "context": "Contexto procesado"
            }
        })
        return base_status
