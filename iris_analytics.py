#!/usr/bin/env python3
"""
Sistema de backup y análisis de tendencias IRIS
Genera reportes automáticos y predice comportamientos futuros
"""
import json
import csv
import requests
from datetime import datetime, timedelta
import statistics
import matplotlib.pyplot as plt
from pathlib import Path

class IRISAnalytics:
    def __init__(self, api_base="http://localhost:8000"):
        self.api_base = api_base
        self.data_dir = Path("/workspace/iris_analytics")
        self.data_dir.mkdir(exist_ok=True)
        
    def collect_metrics_history(self, hours=24):
        """Recopilar historial de métricas"""
        print(f"📊 Recopilando historial de métricas (últimas {hours} horas)...")
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        history = []
        
        # Simular obtención de datos históricos
        # En un sistema real, esto vendría de una base de datos
        for hour_offset in range(hours):
            timestamp = end_time - timedelta(hours=hour_offset)
            
            try:
                response = requests.get(f"{self.api_base}/metrics/summary")
                data = response.json()
                
                record = {
                    'timestamp': timestamp.isoformat(),
                    'total_agents': data['summary']['total_agents'],
                    'active_agents': data['summary']['active_agents'],
                    'total_tasks': data['summary']['total_tasks'],
                    'total_tokens': data['summary']['total_tokens'],
                    'avg_response_time': data['summary']['avg_response_time'],
                    'system_health': data['summary']['system_health']
                }
                
                # Agregar métricas por agente
                for agent in data['agents']:
                    agent_key = f"{agent['id']}"
                    record[f"{agent_key}_status"] = agent['status']
                    record[f"{agent_key}_tasks"] = agent['tasksCompleted']
                    record[f"{agent_key}_tokens"] = agent['tokenUsage']
                    record[f"{agent_key}_success_rate"] = agent['successRate']
                
                history.append(record)
                
            except Exception as e:
                print(f"⚠️ Error obteniendo datos para {timestamp}: {e}")
        
        return history
    
    def save_to_csv(self, data, filename):
        """Guardar datos en CSV"""
        if not data:
            return
        
        filepath = self.data_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        print(f"💾 Datos guardados en {filepath}")
        return filepath
    
    def generate_analysis_report(self, data):
        """Generar reporte de análisis"""
        if len(data) < 2:
            return "Datos insuficientes para análisis"
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'period_hours': len(data),
            'insights': [],
            'recommendations': [],
            'predictions': {},
            'alerts': []
        }
        
        # Análisis de tendencias
        tasks_data = [record['total_tasks'] for record in data]
        tokens_data = [record['total_tokens'] for record in data]
        response_time_data = [record['avg_response_time'] for record in data]
        
        # Tendencias de tareas
        tasks_trend = self.calculate_trend(tasks_data)
        if tasks_trend > 0.1:
            report['insights'].append("📈 Incremento sostenido en tareas completadas")
        elif tasks_trend < -0.1:
            report['insights'].append("📉 Disminución en tareas completadas - revisar capacidad")
        
        # Análisis de tokens
        avg_tokens = statistics.mean(tokens_data)
        if avg_tokens > 100000:
            report['recommendations'].append("💡 Considerar optimizar uso de tokens")
        
        # Tiempo de respuesta
        avg_response = statistics.mean(response_time_data)
        if avg_response > 2.0:
            report['alerts'].append("⚠️ Tiempo de respuesta promedio alto (>2s)")
        
        # Predicciones
        if len(data) >= 10:
            next_hours_predictions = self.predict_next_values(tasks_data[-10:])
            report['predictions'] = {
                'next_6h_tasks': next_hours_predictions['tasks'],
                'confidence_level': next_hours_predictions['confidence']
            }
        
        return report
    
    def calculate_trend(self, data):
        """Calcular tendencia (pendiente)"""
        if len(data) < 2:
            return 0
        
        x = list(range(len(data)))
        n = len(data)
        
        # Cálculo de pendiente simple
        sum_x = sum(x)
        sum_y = sum(data)
        sum_xy = sum(x[i] * data[i] for i in range(n))
        sum_x2 = sum(xi * xi for xi in x)
        
        if n * sum_x2 - sum_x * sum_x == 0:
            return 0
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        # Normalizar por el promedio para obtener porcentaje
        avg_value = statistics.mean(data)
        return slope / avg_value if avg_value != 0 else 0
    
    def predict_next_values(self, recent_data):
        """Predicción simple basada en tendencia"""
        if len(recent_data) < 3:
            return {'tasks': 'Insuficientes datos', 'confidence': 'baja'}
        
        trend = self.calculate_trend(recent_data)
        last_value = recent_data[-1]
        
        # Predicción simple: tendencia lineal
        predicted_next = last_value + (trend * last_value * 6)  # Próximas 6 horas
        
        return {
            'tasks': round(predicted_next),
            'confidence': 'alta' if abs(trend) < 0.2 else 'media'
        }
    
    def create_dashboard_html(self, data, report):
        """Crear dashboard HTML con gráficos"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>IRIS Analytics Report</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; margin-bottom: 30px; }}
                .insights {{ background: #e8f4f8; padding: 15px; border-radius: 6px; margin: 10px 0; }}
                .recommendations {{ background: #f0f8e8; padding: 15px; border-radius: 6px; margin: 10px 0; }}
                .alerts {{ background: #ffe8e8; padding: 15px; border-radius: 6px; margin: 10px 0; }}
                .data-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .data-table th, .data-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .data-table th {{ background: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 IRIS Analytics Report</h1>
                    <p>Generado el: {report['generated_at']}</p>
                </div>
                
                <div class="insights">
                    <h3>🔍 Insights Principales</h3>
                    <ul>
                        {' '.join(f'<li>{insight}</li>' for insight in report['insights'])}
                    </ul>
                </div>
                
                <div class="recommendations">
                    <h3>💡 Recomendaciones</h3>
                    <ul>
                        {' '.join(f'<li>{rec}</li>' for rec in report['recommendations'])}
                    </ul>
                </div>
                
                {f'<div class="alerts"><h3>🚨 Alertas</h3><ul>{" ".join(f"<li>{alert}</li>" for alert in report['alerts'])}</ul></div>' if report['alerts'] else ''}
                
                <h3>📈 Predicciones</h3>
                <p><strong>Próximas 6 horas:</strong> ~{report['predictions'].get('next_6h_tasks', 'N/A')} tareas</p>
                <p><strong>Nivel de confianza:</strong> {report['predictions'].get('confidence_level', 'N/A')}</p>
                
                <h3>📊 Resumen de Datos</h3>
                <table class="data-table">
                    <tr><th>Métrica</th><th>Valor</th></tr>
                    <tr><td>Período de análisis</td><td>{report['period_hours']} horas</td></tr>
                    <tr><td>Registros procesados</td><td>{len(data)}</td></tr>
                    <tr><td>Generado</td><td>{report['generated_at']}</td></tr>
                </table>
            </div>
        </body>
        </html>
        """
        
        report_path = self.data_dir / f"iris_analytics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📋 Reporte generado: {report_path}")
        return report_path
    
    def run_full_analysis(self):
        """Ejecutar análisis completo"""
        print("🚀 Iniciando análisis completo de IRIS...")
        
        # Recopilar datos
        history = self.collect_metrics_history(hours=24)
        
        if not history:
            print("❌ No se pudieron obtener datos")
            return
        
        # Guardar datos
        csv_path = self.save_to_csv(history, f"iris_metrics_history_{datetime.now().strftime('%Y%m%d')}.csv")
        
        # Generar reporte
        report = self.generate_analysis_report(history)
        
        # Crear dashboard
        dashboard_path = self.create_dashboard_html(history, report)
        
        print("✅ Análisis completo finalizado")
        print(f"📁 Archivos generados:")
        print(f"   📊 CSV: {csv_path}")
        print(f"   📋 Dashboard: {dashboard_path}")
        
        return {
            'csv_file': str(csv_path),
            'dashboard_file': str(dashboard_path),
            'report': report
        }

if __name__ == "__main__":
    analytics = IRISAnalytics()
    result = analytics.run_full_analysis()
    
    if result:
        print(f"\n🎯 Resultados:")
        print(f"   • {len(result['report']['insights'])} insights identificados")
        print(f"   • {len(result['report']['recommendations'])} recomendaciones generadas")
        print(f"   • {len(result['report']['alerts'])} alertas detectadas")
        print(f"   • Predicción próxima 6h: {result['report']['predictions'].get('next_6h_tasks', 'N/A')} tareas")