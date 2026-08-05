import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import hashlib

class IRISTemplateManager:
    """Gestor de templates para automatización de agentes IRIS"""
    
    def __init__(self, templates_dir: str = "iris_templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
        self.templates_index = self._load_templates_index()
    
    def _load_templates_index(self) -> Dict[str, Any]:
        """Cargar índice de templates disponibles"""
        index_file = self.templates_dir / "templates_index.json"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"templates": []}
    
    def _save_templates_index(self):
        """Guardar índice de templates"""
        index_file = self.templates_dir / "templates_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(self.templates_index, f, indent=2, ensure_ascii=False)
    
    def create_sales_automation_template(self) -> Dict[str, Any]:
        """Crear template de automatización de ventas para IRIS"""
        return {
            "id": "iris_sales_automation",
            "name": "IRIS Sales Automation Template",
            "description": "Automatización completa de procesos de venta con agentes especializados",
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "author": "IRIS MCP Server",
            "category": "sales",
            "agents": {
                "lead_qualification_agent": {
                    "model": "minimax/m1",
                    "type": "sales",
                    "capabilities": [
                        "lead_scoring",
                        "demographic_analysis", 
                        "intent_detection",
                        "qualification_rules"
                    ],
                    "prompts": [
                        "Analyze lead data and determine qualification score",
                        "Identify pain points and business needs",
                        "Assess decision-maker presence and authority",
                        "Generate qualification summary with next actions"
                    ],
                    "actions": [
                        "score_lead",
                        "route_to_sales_rep",
                        "schedule_follow_up",
                        "update_crm_record"
                    ],
                    "config": {
                        "score_threshold": 70,
                        "response_time_target": "< 2 hours",
                        "escalation_rules": {
                            "hot_leads": "immediate_escalation",
                            "qualified_leads": "same_day_followup",
                            "unqualified_leads": "nurture_sequence"
                        }
                    }
                },
                "proposal_generator_agent": {
                    "model": "minimax/m2",
                    "type": "sales",
                    "capabilities": [
                        "proposal_creation",
                        "pricing_optimization",
                        "competitive_analysis",
                        "roi_calculation"
                    ],
                    "prompts": [
                        "Generate compelling sales proposals",
                        "Customize pricing based on customer profile",
                        "Include competitive advantages and value propositions",
                        "Create clear ROI calculations and timelines"
                    ],
                    "actions": [
                        "create_proposal_document",
                        "customize_pricing_tier",
                        "include_competitor_comparison",
                        "generate_timeline"
                    ],
                    "config": {
                        "default_validity_days": 30,
                        "include_terms": True,
                        "custom_branding": True,
                        "auto_follow_up": True
                    }
                },
                "follow_up_automation_agent": {
                    "model": "minimax/m1",
                    "type": "sales",
                    "capabilities": [
                        "communication_sequencing",
                        "crm_updates",
                        "meeting_scheduling",
                        "objection_handling"
                    ],
                    "prompts": [
                        "Generate personalized follow-up communications",
                        "Update CRM with interaction history",
                        "Schedule follow-up meetings and calls",
                        "Address common objections with solutions"
                    ],
                    "actions": [
                        "send_follow_up_email",
                        "update_crm_notes",
                        "schedule_meeting",
                        "log_interaction"
                    ],
                    "config": {
                        "sequence_templates": [
                            "post_demo_followup",
                            "proposal_followup", 
                            "closing_sequence",
                            "objection_handling"
                        ],
                        "timing_rules": {
                            "immediate": "within_2_hours",
                            "same_day": "before_5pm",
                            "next_day": "morning_followup"
                        }
                    }
                }
            },
            "workflow": {
                "stages": [
                    {
                        "name": "Lead Reception",
                        "agent": "lead_qualification_agent",
                        "description": "Incoming lead analysis and qualification"
                    },
                    {
                        "name": "Proposal Generation", 
                        "agent": "proposal_generator_agent",
                        "description": "Custom proposal creation"
                    },
                    {
                        "name": "Follow-up Management",
                        "agent": "follow_up_automation_agent", 
                        "description": "Ongoing communication and nurturing"
                    }
                ],
                "triggers": [
                    "new_lead_reception",
                    "proposal_request",
                    "demo_completion",
                    "negotiation_stage"
                ]
            },
            "integrations": {
                "crm_systems": ["salesforce", "hubspot", "pipedrive"],
                "email_platforms": ["outlook", "gmail", "mailchimp"],
                "calendar_systems": ["google_calendar", "outlook", "calendly"],
                "communication_tools": ["slack", "teams", "discord"]
            },
            "kpis": [
                "lead_conversion_rate",
                "avg_proposal_response_time",
                "sales_cycle_duration",
                "customer_acquisition_cost",
                "pipeline_velocity"
            ]
        }
    
    def create_support_template(self) -> Dict[str, Any]:
        """Crear template de automatización de soporte para IRIS"""
        return {
            "id": "iris_support_automation",
            "name": "IRIS Support Automation Template",
            "description": "Automatización de atención al cliente y gestión de tickets",
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "author": "IRIS MCP Server",
            "category": "support",
            "agents": {
                "ticket_classifier_agent": {
                    "model": "minimax/m1",
                    "type": "support",
                    "capabilities": [
                        "ticket_categorization",
                        "priority_assessment",
                        "sentiment_analysis",
                        "urgency_detection"
                    ],
                    "prompts": [
                        "Categorize support tickets by type and severity",
                        "Analyze customer sentiment and frustration level",
                        "Determine appropriate priority and escalation path",
                        "Assign to best-suited support agent or department"
                    ],
                    "actions": [
                        "categorize_ticket",
                        "set_priority_level",
                        "route_to_agent",
                        "update_ticket_status"
                    ],
                    "config": {
                        "priority_levels": ["critical", "high", "medium", "low"],
                        "response_time_sla": {
                            "critical": "< 1 hour",
                            "high": "< 4 hours", 
                            "medium": "< 24 hours",
                            "low": "< 72 hours"
                        },
                        "auto_escalation": True,
                        "sentiment_threshold": 0.8
                    }
                },
                "response_generator_agent": {
                    "model": "minimax/m2",
                    "type": "support",
                    "capabilities": [
                        "response_composition",
                        "knowledge_base_lookup",
                        "solution_recommendation",
                        "escalation_determination"
                    ],
                    "prompts": [
                        "Generate helpful and accurate customer responses",
                        "Reference relevant knowledge base articles",
                        "Provide step-by-step solutions when applicable",
                        "Determine if escalation to human agent is needed"
                    ],
                    "actions": [
                        "draft_response",
                        "lookup_knowledge_base",
                        "suggest_solutions",
                        "escalate_if_needed"
                    ],
                    "config": {
                        "auto_response_threshold": 0.9,
                        "include_knowledge_base_links": True,
                        "personalization_level": "high",
                        "escalation_triggers": [
                            "complex_technical_issue",
                            "angry_customer",
                            "billing_dispute",
                            "feature_request"
                        ]
                    }
                },
                "escalation_manager_agent": {
                    "model": "minimax/m1",
                    "type": "support",
                    "capabilities": [
                        "escalation_routing",
                        "handoff_management",
                        "priority_adjustment",
                        "sla_monitoring"
                    ],
                    "prompts": [
                        "Route escalated tickets to appropriate specialists",
                        "Ensure smooth handoff between support levels",
                        "Monitor SLA compliance and trigger alerts",
                        "Coordinate with other departments when needed"
                    ],
                    "actions": [
                        "route_to_specialist",
                        "notify_stakeholders",
                        "adjust_priority",
                        "create_sla_alert"
                    ],
                    "config": {
                        "escalation_levels": [
                            "tier_2_support",
                            "technical_specialist", 
                            "management_override",
                            "external_vendor"
                        ],
                        "auto_sla_alerts": True,
                        "handoff_timeout": 30, # minutes
                        "notification_channels": ["email", "slack", "teams"]
                    }
                }
            },
            "workflow": {
                "stages": [
                    {
                        "name": "Ticket Classification",
                        "agent": "ticket_classifier_agent",
                        "description": "Automatic ticket categorization and routing"
                    },
                    {
                        "name": "Initial Response",
                        "agent": "response_generator_agent", 
                        "description": "Generate helpful responses to common issues"
                    },
                    {
                        "name": "Escalation Management",
                        "agent": "escalation_manager_agent",
                        "description": "Handle complex cases and handoffs"
                    }
                ],
                "triggers": [
                    "new_ticket_creation",
                    "customer_response",
                    "sla_breach_warning",
                    "escalation_request"
                ]
            },
            "integrations": {
                "helpdesk_systems": ["zendesk", "freshdesk", "jira"],
                "knowledge_bases": ["confluence", "notion", "guru"],
                "communication_tools": ["slack", "teams", "email"],
                "monitoring_tools": ["newrelic", "datadog", "sentry"]
            },
            "kpis": [
                "first_response_time",
                "resolution_time",
                "customer_satisfaction_score",
                "escalation_rate",
                "knowledge_base_usage"
            ]
        }
    
    def create_consulting_template(self) -> Dict[str, Any]:
        """Crear template de análisis de consultoría para IRIS"""
        return {
            "id": "iris_consulting_analysis",
            "name": "IRIS Consulting Analysis Template",
            "description": "Análisis avanzado para consultoría y generación de insights",
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "author": "IRIS MCP Server",
            "category": "consulting",
            "agents": {
                "data_analyzer_agent": {
                    "model": "minimax/m2",
                    "type": "consulting",
                    "capabilities": [
                        "data_processing",
                        "statistical_analysis",
                        "pattern_recognition",
                        "trend_identification"
                    ],
                    "prompts": [
                        "Process and analyze provided business data",
                        "Identify key patterns and anomalies",
                        "Generate statistical summaries and correlations",
                        "Highlight significant trends and insights"
                    ],
                    "actions": [
                        "process_data_files",
                        "generate_statistics",
                        "identify_patterns",
                        "create_visualizations"
                    ],
                    "config": {
                        "supported_formats": ["csv", "json", "xlsx", "pdf"],
                        "statistical_tests": [
                            "correlation_analysis",
                            "regression_analysis", 
                            "cluster_analysis",
                            "time_series_analysis"
                        ],
                        "visualization_types": [
                            "line_charts",
                            "bar_charts",
                            "scatter_plots",
                            "heat_maps"
                        ]
                    }
                },
                "insight_generator_agent": {
                    "model": "minimax/m2",
                    "type": "consulting",
                    "capabilities": [
                        "insight_synthesis",
                        "recommendation_generation",
                        "risk_assessment",
                        "opportunity_identification"
                    ],
                    "prompts": [
                        "Synthesize findings into actionable insights",
                        "Generate specific recommendations based on data",
                        "Assess risks and mitigation strategies",
                        "Identify new opportunities and growth areas"
                    ],
                    "actions": [
                        "synthesize_insights",
                        "generate_recommendations",
                        "assess_risks",
                        "identify_opportunities"
                    ],
                    "config": {
                        "insight_categories": [
                            "operational_efficiency",
                            "revenue_optimization",
                            "cost_reduction",
                            "risk_mitigation",
                            "growth_opportunities"
                        ],
                        "confidence_threshold": 0.8,
                        "prioritization_method": "impact_effort_matrix"
                    }
                },
                "report_generator_agent": {
                    "model": "minimax/m2",
                    "type": "consulting",
                    "capabilities": [
                        "report_composition",
                        "executive_summary_creation",
                        "data_visualization",
                        "presentation_generation"
                    ],
                    "prompts": [
                        "Create comprehensive consulting reports",
                        "Generate executive summaries for leadership",
                        "Include compelling data visualizations",
                        "Format for different stakeholder audiences"
                    ],
                    "actions": [
                        "compile_findings",
                        "create_visualizations",
                        "generate_summary",
                        "format_report"
                    ],
                    "config": {
                        "report_templates": [
                            "executive_summary",
                            "detailed_analysis",
                            "technical_report",
                            "presentation_deck"
                        ],
                        "output_formats": [
                            "pdf",
                            "powerpoint",
                            "html",
                            "markdown"
                        ],
                        "branding_options": {
                            "company_logo": True,
                            "color_scheme": "professional",
                            "font_family": "corporate"
                        }
                    }
                }
            },
            "workflow": {
                "stages": [
                    {
                        "name": "Data Processing",
                        "agent": "data_analyzer_agent",
                        "description": "Process and analyze business data"
                    },
                    {
                        "name": "Insight Generation",
                        "agent": "insight_generator_agent",
                        "description": "Generate actionable insights and recommendations"
                    },
                    {
                        "name": "Report Creation",
                        "agent": "report_generator_agent",
                        "description": "Compile findings into professional reports"
                    }
                ],
                "triggers": [
                    "data_upload",
                    "analysis_request",
                    "periodic_review",
                    "custom_study"
                ]
            },
            "integrations": {
                "data_sources": ["salesforce", "google_analytics", "database_systems"],
                "analytics_tools": ["tableau", "powerbi", "looker"],
                "reporting_platforms": ["confluence", "sharepoint", "notion"],
                "collaboration_tools": ["slack", "teams", "zoom"]
            },
            "kpis": [
                "analysis_accuracy",
                "insight_relevance",
                "report_generation_time",
                "client_satisfaction",
                "implementation_success_rate"
            ]
        }
    
    def create_multiagent_template(self) -> Dict[str, Any]:
        """Crear template de configuración multiagente para IRIS"""
        return {
            "id": "iris_multiagent_config",
            "name": "IRIS Multi-Agent Configuration Template",
            "description": "Configuración coordinada de múltiples agentes IRIS especializados",
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "author": "IRIS MCP Server",
            "category": "configuration",
            "agents": {
                "orchestrator_agent": {
                    "model": "minimax/m2",
                    "type": "orchestrator",
                    "capabilities": [
                        "task_coordination",
                        "workflow_management",
                        "resource_allocation",
                        "performance_monitoring"
                    ],
                    "prompts": [
                        "Coordinate work between multiple specialized agents",
                        "Manage complex workflows and dependencies",
                        "Optimize resource allocation and task distribution",
                        "Monitor overall system performance and efficiency"
                    ],
                    "actions": [
                        "coordinate_agents",
                        "manage_workflows",
                        "allocate_resources",
                        "monitor_performance"
                    ],
                    "config": {
                        "max_concurrent_agents": 5,
                        "task_timeout": 300,  # seconds
                        "resource_limits": {
                            "cpu": "80%",
                            "memory": "2GB",
                            "concurrent_requests": 10
                        },
                        "scaling_policies": {
                            "auto_scale": True,
                            "scale_up_threshold": 0.8,
                            "scale_down_threshold": 0.3
                        }
                    }
                },
                "communication_agent": {
                    "model": "minimax/m1",
                    "type": "communication",
                    "capabilities": [
                        "inter_agent_communication",
                        "status_reporting",
                        "alert_management",
                        "notification_coordination"
                    ],
                    "prompts": [
                        "Facilitate communication between agents",
                        "Generate status reports and updates",
                        "Manage alerts and notifications",
                        "Coordinate agent handoffs and transitions"
                    ],
                    "actions": [
                        "relay_messages",
                        "generate_reports",
                        "send_alerts",
                        "coordinate_handoffs"
                    ],
                    "config": {
                        "communication_channels": [
                            "internal_messaging",
                            "status_updates",
                            "alert_system",
                            "log_aggregation"
                        ],
                        "notification_rules": {
                            "agent_startup": "status_channel",
                            "task_completion": "progress_channel",
                            "error_occurrence": "alerts_channel",
                            "workflow_completion": "summary_channel"
                        }
                    }
                }
            },
            "workflow": {
                "stages": [
                    {
                        "name": "Task Analysis",
                        "description": "Analyze incoming tasks and determine optimal agent assignment"
                    },
                    {
                        "name": "Agent Coordination", 
                        "description": "Coordinate multiple agents to work on complex tasks"
                    },
                    {
                        "name": "Progress Monitoring",
                        "description": "Monitor progress and adjust resource allocation"
                    },
                    {
                        "name": "Result Integration",
                        "description": "Integrate results from multiple agents"
                    }
                ],
                "coordination_patterns": [
                    "sequential_processing",
                    "parallel_execution", 
                    "pipeline_workflow",
                    "feedback_loop",
                    "hierarchical_cascade"
                ]
            },
            "monitoring": {
                "metrics": [
                    "agent_utilization",
                    "task_completion_rate",
                    "response_time",
                    "error_rate",
                    "resource_consumption"
                ],
                "alerts": [
                    "agent_failure",
                    "performance_degradation",
                    "resource_exhaustion",
                    "task_timeout"
                ],
                "dashboards": [
                    "agent_status",
                    "workflow_progress", 
                    "performance_metrics",
                    "resource_usage"
                ]
            },
            "integrations": {
                "monitoring_tools": ["prometheus", "grafana", "datadog"],
                "logging_systems": ["elasticsearch", "splunk", "cloudwatch"],
                "alerting_platforms": ["pagerduty", "opsgenie", "email"],
                "reporting_tools": ["powerbi", "tableau", "custom_dashboards"]
            },
            "kpis": [
                "overall_system_uptime",
                "average_task_completion_time",
                "agent_utilization_rate",
                "error_resolution_time",
                "system_throughput"
            ]
        }
    
    def create_optimization_template(self) -> Dict[str, Any]:
        """Crear template de optimización de flujos para IRIS"""
        return {
            "id": "iris_optimization_template",
            "name": "IRIS Workflow Optimization Template",
            "description": "Optimización automática de flujos de trabajo y procesos",
            "version": "1.0.0",
            "created": datetime.now().isoformat(),
            "author": "IRIS MCP Server",
            "category": "optimization",
            "agents": {
                "process_analyzer_agent": {
                    "model": "minimax/m2",
                    "type": "optimization",
                    "capabilities": [
                        "process_mapping",
                        "bottleneck_identification",
                        "efficiency_analysis",
                        "performance_measurement"
                    ],
                    "prompts": [
                        "Map current business processes and workflows",
                        "Identify bottlenecks and inefficiencies",
                        "Analyze process performance metrics",
                        "Recommend optimization strategies"
                    ],
                    "actions": [
                        "map_processes",
                        "identify_bottlenecks",
                        "measure_performance",
                        "recommend_optimizations"
                    ],
                    "config": {
                        "analysis_period": "30_days",
                        "bottleneck_threshold": 0.2,  # 20% above average
                        "metrics_tracked": [
                            "process_duration",
                            "resource_utilization",
                            "error_rate",
                            "customer_satisfaction"
                        ]
                    }
                },
                "optimization_agent": {
                    "model": "minimax/m2",
                    "type": "optimization",
                    "capabilities": [
                        "workflow_redesign",
                        "resource_optimization",
                        "automation_recommendation",
                        "efficiency_improvement"
                    ],
                    "prompts": [
                        "Redesign workflows for maximum efficiency",
                        "Optimize resource allocation and utilization",
                        "Recommend automation opportunities",
                        "Implement continuous improvement strategies"
                    ],
                    "actions": [
                        "redesign_workflows",
                        "optimize_resources",
                        "recommend_automation",
                        "implement_improvements"
                    ],
                    "config": {
                        "optimization_goals": [
                            "reduce_process_time",
                            "increase_accuracy",
                            "lower_costs",
                            "improve_customer_satisfaction"
                        ],
                        "automation_opportunities": {
                            "simple_repetitive_tasks": "high_priority",
                            "data_processing": "medium_priority",
                            "decision_making": "requires_human_oversight"
                        }
                    }
                }
            },
            "optimization_strategies": [
                "parallel_processing",
                "resource_pooling",
                "predictive_scaling",
                "load_balancing",
                "automation_layering"
            ],
            "monitoring_framework": {
                "kpis": [
                    "process_efficiency_ratio",
                    "automation_coverage",
                    "resource_utilization",
                    "error_reduction_rate",
                    "cost_savings_achieved"
                ],
                "alerts": [
                    "efficiency_drop",
                    "bottleneck_emergence",
                    "automation_failure",
                    "resource_overload"
                ]
            }
        }
    
    def save_template(self, template: Dict[str, Any]) -> str:
        """Guardar template en archivo"""
        template_id = template.get("id", template["name"].lower().replace(" ", "_"))
        file_path = self.templates_dir / f"{template_id}.json"
        
        # Agregar hash para verificación de integridad
        template_content = json.dumps(template, sort_keys=True)
        template["content_hash"] = hashlib.md5(template_content.encode()).hexdigest()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        # Actualizar índice
        template_summary = {
            "id": template["id"],
            "name": template["name"],
            "category": template["category"],
            "description": template["description"],
            "version": template["version"],
            "created": template["created"],
            "file_path": str(file_path)
        }
        
        self.templates_index["templates"].append(template_summary)
        self._save_templates_index()
        
        return str(file_path)
    
    def load_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Cargar template desde archivo"""
        file_path = self.templates_dir / f"{template_id}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            template = json.load(f)
        
        # Verificar integridad
        if "content_hash" in template:
            template_content = json.dumps(template, sort_keys=True)
            current_hash = hashlib.md5(template_content.encode()).hexdigest()
            if current_hash != template["content_hash"]:
                raise ValueError(f"Template integrity check failed for {template_id}")
            # Remove hash before returning
            del template["content_hash"]
        
        return template
    
    def list_templates(self) -> List[Dict[str, Any]]:
        """Listar todos los templates disponibles"""
        return self.templates_index.get("templates", [])
    
    def delete_template(self, template_id: str) -> bool:
        """Eliminar template"""
        file_path = self.templates_dir / f"{template_id}.json"
        
        if not file_path.exists():
            return False
        
        file_path.unlink()
        
        # Remover del índice
        self.templates_index["templates"] = [
            t for t in self.templates_index["templates"] if t["id"] != template_id
        ]
        self._save_templates_index()
        
        return True
    
    def generate_workflow_config(self, template_id: str, customizations: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generar configuración de workflow desde template"""
        template = self.load_template(template_id)
        
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Aplicar personalizaciones si se proporcionan
        if customizations:
            template = self._apply_customizations(template, customizations)
        
        # Generar configuración de runtime
        workflow_config = {
            "template_info": {
                "id": template["id"],
                "name": template["name"],
                "version": template["version"]
            },
            "agents": template["agents"],
            "workflow": template.get("workflow", {}),
            "runtime_config": {
                "deployment_mode": "production",
                "monitoring_enabled": True,
                "auto_scaling": True,
                "health_checks": True
            },
            "integrations": template.get("integrations", {}),
            "kpis": template.get("kpis", []),
            "generated_at": datetime.now().isoformat(),
            "generated_by": "IRIS MCP Template Manager"
        }
        
        return workflow_config
    
    def _apply_customizations(self, template: Dict[str, Any], customizations: Dict[str, Any]) -> Dict[str, Any]:
        """Aplicar personalizaciones al template"""
        customized = template.copy()
        
        # Aplicar personalizaciones de agentes
        if "agents" in customizations:
            for agent_name, agent_custom in customizations["agents"].items():
                if agent_name in customized["agents"]:
                    customized["agents"][agent_name].update(agent_custom)
        
        # Aplicar personalizaciones de workflow
        if "workflow" in customizations:
            customized["workflow"].update(customizations["workflow"])
        
        # Aplicar configuraciones de runtime
        if "runtime_config" in customizations:
            customized["runtime_config"] = customizations["runtime_config"]
        
        return customized
    
    def validate_template(self, template: Dict[str, Any]) -> Dict[str, Any]:
        """Validar template y retornar resultados de validación"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        # Verificar campos requeridos
        required_fields = ["id", "name", "description", "agents", "category"]
        for field in required_fields:
            if field not in template:
                validation_result["errors"].append(f"Missing required field: {field}")
                validation_result["valid"] = False
        
        # Verificar estructura de agentes
        if "agents" in template:
            for agent_name, agent_config in template["agents"].items():
                if not isinstance(agent_config, dict):
                    validation_result["errors"].append(f"Agent {agent_name} must be an object")
                    continue
                
                if "model" not in agent_config:
                    validation_result["errors"].append(f"Agent {agent_name} missing 'model' field")
                if "capabilities" not in agent_config:
                    validation_result["warnings"].append(f"Agent {agent_name} missing 'capabilities' field")
                if "prompts" not in agent_config:
                    validation_result["warnings"].append(f"Agent {agent_name} missing 'prompts' field")
                if "actions" not in agent_config:
                    validation_result["warnings"].append(f"Agent {agent_name} missing 'actions' field")
        
        # Verificar workflow si existe
        if "workflow" in template:
            if "stages" not in template["workflow"]:
                validation_result["warnings"].append("Workflow missing 'stages' definition")
            else:
                stages = template["workflow"]["stages"]
                if not isinstance(stages, list) or len(stages) == 0:
                    validation_result["errors"].append("Workflow stages must be a non-empty array")
        
        validation_result["info"].append(f"Template contains {len(template.get('agents', {}))} agents")
        validation_result["info"].append(f"Template category: {template.get('category', 'unspecified')}")
        
        return validation_result