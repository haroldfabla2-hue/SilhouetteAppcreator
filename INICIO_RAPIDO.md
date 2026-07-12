# 🚀 INICIO RÁPIDO

## Comandos para Ejecutar Ahora

### Opción 1: Todo Automatizado (Recomendado)
```bash
cd /workspace
./quickstart.sh
```

### Opción 2: Validación Completa
```bash
cd /workspace
./validar_sistema.sh
```

### Opción 3: Manual
```bash
cd /workspace
docker compose up --build -d
sleep 30
python3 test_end_to_end.py
```

## URLs del Sistema

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Prometheus**: http://localhost:9090  
- **Grafana**: http://localhost:3001 (admin/admin)

## Prueba Manual en UI

1. Abre http://localhost:3000
2. Escribe: `Analiza las ventajas de usar sistemas multi-agente versus agentes individuales, incluyendo métricas de rendimiento`
3. Observa los 5 agentes ejecutándose en paralelo
4. Verifica streaming en tiempo real (<300ms)

## Verificar Paralelización

```bash
docker compose logs backend | grep "Agent.*started"
```

Debes ver ExecutorAgent, VerifierAgent y MemoryManagerAgent con timestamps idénticos o <100ms de diferencia.

## Detener Sistema

```bash
docker compose down
```

## Documentación Completa

- **Guía detallada**: `LISTO_PARA_PRUEBAS.md`
- **Instrucciones paso a paso**: `INSTRUCCIONES_PRUEBAS.md`
- **README general**: `README.md`

---

✅ **Sistema 100% listo** - Solo ejecuta `./quickstart.sh`
