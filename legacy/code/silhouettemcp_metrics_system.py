#!/usr/bin/env python3
"""
SilhouetteMCP Metrics System - Sistema de Métricas
Puerto 8005: Proporciona métricas en tiempo real de todos los sistemas
"""

import psutil
import json
import time
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, List, Any
import uvicorn

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Crear aplicación FastAPI
app = FastAPI(
    title="SilhouetteMCP Metrics System",
    description="Sistema de métricas en tiempo real para SilhouetteMCP",
    version="1.0.0"
)

class MetricsCollector:
    """Recolector de métricas del sistema"""
    
    def __init__(self):
        self.start_time = time.time()
        self.system_metrics = {}
        self.performance_history = []
        
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Recolecta métricas del sistema"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "uptime": time.time() - self.start_time,
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count()
                },
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "used": memory.used,
                    "percent": memory.percent
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                },
                "processes": {
                    "count": len(psutil.pids()),
                    "running": len([p for p in psutil.process_iter(['status']) 
                                  if p.info['status'] == psutil.STATUS_RUNNING])
                }
            }
            
            self.system_metrics = metrics
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {}
    
    def collect_silhouettemcp_metrics(self) -> Dict[str, Any]:
        """Recolecta métricas específicas de SilhouetteMCP"""
        try:
            # Obtener métricas de procesos SilhouetteMCP
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                try:
                    if 'silhouettemcp' in ' '.join(proc.info['cmdline'] or []).lower():
                        processes.append({
                            "pid": proc.info['pid'],
                            "name": proc.info['name'],
                            "cpu_percent": proc.info['cpu_percent'],
                            "memory_percent": proc.info['memory_percent'],
                            "cmdline": ' '.join(proc.info['cmdline'] or [])
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            silhouettemcp_metrics = {
                "timestamp": datetime.now().isoformat(),
                "total_processes": len(processes),
                "processes": processes,
                "estimated_memory_usage": sum(p.get('memory_percent', 0) for p in processes),
                "estimated_cpu_usage": sum(p.get('cpu_percent', 0) for p in processes)
            }
            
            return silhouettemcp_metrics
            
        except Exception as e:
            logger.error(f"Error collecting SilhouetteMCP metrics: {e}")
            return {}

# Instancia del recolector
metrics_collector = MetricsCollector()

# Rutas de la API

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {
        "service": "SilhouetteMCP Metrics System",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    """Health check"""
    try:
        metrics = metrics_collector.collect_system_metrics()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "metrics_collected": len(metrics) > 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/metrics/system")
async def get_system_metrics():
    """Obtiene métricas del sistema"""
    try:
        metrics = metrics_collector.collect_system_metrics()
        return JSONResponse(content=metrics)
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/silhouettemcp")
async def get_silhouettemcp_metrics():
    """Obtiene métricas específicas de SilhouetteMCP"""
    try:
        metrics = metrics_collector.collect_silhouettemcp_metrics()
        return JSONResponse(content=metrics)
    except Exception as e:
        logger.error(f"Error getting SilhouetteMCP metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics/complete")
async def get_complete_metrics():
    """Obtiene métricas completas (sistema + SilhouetteMCP)"""
    try:
        system_metrics = metrics_collector.collect_system_metrics()
        silhouettemcp_metrics = metrics_collector.collect_silhouettemcp_metrics()
        
        complete_metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": system_metrics,
            "silhouettemcp": silhouettemcp_metrics,
            "summary": {
                "total_silhouettemcp_processes": silhouettemcp_metrics.get("total_processes", 0),
                "estimated_total_cpu": silhouettemcp_metrics.get("estimated_cpu_usage", 0),
                "estimated_total_memory": silhouettemcp_metrics.get("estimated_memory_usage", 0),
                "system_cpu_usage": system_metrics.get("cpu", {}).get("usage_percent", 0),
                "system_memory_usage": system_metrics.get("memory", {}).get("percent", 0)
            }
        }
        
        return JSONResponse(content=complete_metrics)
    except Exception as e:
        logger.error(f"Error getting complete metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """Obtiene estado general del sistema"""
    try:
        metrics = metrics_collector.collect_system_metrics()
        silhouettemcp_metrics = metrics_collector.collect_silhouettemcp_metrics()
        
        status = {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - metrics_collector.start_time,
            "system_health": {
                "cpu_usage": metrics.get("cpu", {}).get("usage_percent", 0),
                "memory_usage": metrics.get("memory", {}).get("percent", 0),
                "disk_usage": metrics.get("disk", {}).get("percent", 0)
            },
            "silhouettemcp_health": {
                "active_processes": silhouettemcp_metrics.get("total_processes", 0),
                "estimated_cpu": silhouettemcp_metrics.get("estimated_cpu_usage", 0),
                "estimated_memory": silhouettemcp_metrics.get("estimated_memory_usage", 0)
            },
            "overall_health": "healthy"
        }
        
        # Determinar salud general
        if (status["system_health"]["cpu_usage"] > 90 or 
            status["system_health"]["memory_usage"] > 90 or
            status["system_health"]["disk_usage"] > 90):
            status["overall_health"] = "warning"
        
        if (status["system_health"]["cpu_usage"] > 95 or 
            status["system_health"]["memory_usage"] > 95):
            status["overall_health"] = "critical"
            
        return JSONResponse(content=status)
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("🚀 Iniciando SilhouetteMCP Metrics System en puerto 8005")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8005,
        log_level="info",
        access_log=True
    )