"""
Script de prueba en vivo para SilhouetteMCP Server.
Envía una solicitud de creación de app al orquestador multi-agente.
"""
import requests
import json
import time

print("=" * 70)
print("  PROBANDO SILHOUETTE MCP SUPERIOR EN VIVO (LOCAL)")
print("=" * 70)

backend_url = "http://localhost:8001/api/agents/chat"

payload = {
    "prompt": "Crea una API en Python con FastAPI para gestionar una lista de tareas (To-Do List)",
    "model": "glm-5.2-max",
    "enable_verification": True
}

print(f"\n[1/3] Enviando prompt al Orquestador Multi-Agente...")
print(f"      Prompt: '{payload['prompt']}'")
print(f"      Endpoint: {backend_url}")

try:
    start_time = time.time()
    response = requests.post(backend_url, json=payload, timeout=60)
    elapsed = round(time.time() - start_time, 2)
    
    print(f"\n[2/3] Respuesta recibida en {elapsed} segundos (HTTP {response.status_code}):")
    
    if response.status_code == 200:
        data = response.json()
        print("\n" + "=" * 50)
        print("  RESULTADO DEL ORQUESTATOR MULTI-AGENTE:")
        print("=" * 50)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        print("\n[3/3] PRUEBA COMPLETADA EXITOSAMENTE!")
    else:
        print(f"Error HTTP {response.status_code}: {response.text}")
        
except Exception as e:
    print(f"\n[ERROR] No se pudo conectar al servidor backend local: {e}")
    print("Asegúrate de que 'python silhouettemcp_server.py' esté ejecutándose en http://localhost:8001")
