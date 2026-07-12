#!/usr/bin/env python3
"""
Integración IRIS con sistemas externos
Monitorea métricas y envía notificaciones automáticas
"""
import requests
import json
import time
from datetime import datetime

class IRISMonitor:
    def __init__(self, stream_url="http://localhost:8000/metrics/stream"):
        self.stream_url = stream_url
        self.last_metrics = None
        
    def get_current_metrics(self):
        """Obtener métricas actuales"""
        response = requests.get("http://localhost:8000/metrics/summary")
        return response.json()
    
    def check_for_alerts(self, current_metrics):
        """Verificar condiciones de alerta"""
        alerts = []
        
        summary = current_metrics['summary']
        agents = current_metrics['agents']
        
        # Alertas de sistema
        if summary['system_health'] != 'healthy':
            alerts.append(f"🚨 Sistema no saludable: {summary['system_health']}")
        
        # Alertas de agentes
        for agent in agents:
            if agent['status'] == 'error':
                alerts.append(f"🔴 Agente en error: {agent['agent']}")
            
            if agent['successRate'] < 0.90:
                alerts.append(f"⚠️ Baja tasa de éxito en {agent['agent']}: {agent['successRate']:.1%}")
        
        # Alertas de performance
        if summary['avg_response_time'] > 3.0:
            alerts.append(f"🐌 Tiempo de respuesta alto: {summary['avg_response_time']:.2f}s")
        
        return alerts
    
    def send_notification(self, message, alert_type="info"):
        """Enviar notificación (personalizable)"""
        print(f"[{alert_type.upper()}] {message}")
        
        # Ejemplos de integración:
        # 1. Slack webhook
        # requests.post("SLACK_WEBHOOK_URL", json={"text": message})
        
        # 2. Discord webhook  
        # requests.post("DISCORD_WEBHOOK_URL", json={"content": message})
        
        # 3. Email (usando SMTP)
        # send_email(subject=f"IRIS Alert: {alert_type}", body=message)
    
    def monitor_continuous(self):
        """Monitoreo continuo"""
        print("🔍 Iniciando monitoreo continuo de IRIS...")
        
        while True:
            try:
                current_metrics = self.get_current_metrics()
                alerts = self.check_for_alerts(current_metrics)
                
                for alert in alerts:
                    self.send_notification(alert, "alert")
                
                # Estadísticas cada 5 minutos
                if int(time.time()) % 300 == 0:
                    stats = current_metrics['summary']
                    self.send_notification(
                        f"📊 Sistema: {stats['active_agents']} agentes activos, "
                        f"{stats['total_tokens']:,} tokens totales, "
                        f"{stats['total_tasks']} tareas completadas",
                        "stats"
                    )
                
                time.sleep(10)  # Verificar cada 10 segundos
                
            except Exception as e:
                print(f"❌ Error en monitoreo: {e}")
                time.sleep(30)

if __name__ == "__main__":
    monitor = IRISMonitor()
    monitor.monitor_continuous()