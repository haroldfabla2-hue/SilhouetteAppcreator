# SilhouetteMCP v4.0.0 - Package de Actualización Completa

## 📦 Contenido del Package

Este package contiene todo lo necesario para actualizar tu VPS SilhouetteMCP de 3 agentes a **51 herramientas** en **6 agentes especializados**.

### 📁 Estructura del Package

```
silhouettemcp_v4_unified/
├── server/                           # Archivos principales del servidor
│   ├── silhouettemcp_server_unified.py    # Servidor unificado (51 herramientas)
│   ├── silhouettemcp_dashboard_expanded.html  # Dashboard actualizado
│   └── requirements.txt                    # Dependencias Python
├── config/                           # Configuración del sistema
│   ├── nginx.conf                          # Configuración proxy nginx
│   ├── silhouettemcp.service               # Servicio systemd
│   └── docker-compose.yml                  # Configuración Docker opcional
├── scripts/                          # Scripts de automatización
│   ├── deploy.sh                             # Script de despliegue completo
│   ├── update.sh                             # Script de actualización
│   └── backup.sh                             # Script de backup automático
├── docs/                            # Documentación completa
│   ├── README_ACTUALIZACION.md               # Guía de actualización paso a paso
│   ├── API_ENDPOINTS.md                      # Documentación completa de API (51 herramientas)
│   ├── GUIA_USUARIO.md                       # Manual de usuario completo
│   └── CHANGELOG.md                          # Lista de cambios detallados
└── .env.example                    # Template de variables de entorno
```

## 🚀 Instalación Rápida

### Opción 1: Instalación Nueva (Recomendada)

```bash
# 1. Descargar y extraer
unzip silhouettemcp_v4_unified.zip
cd silhouettemcp_v4_unified

# 2. Hacer scripts ejecutables
chmod +x scripts/*.sh

# 3. Ejecutar instalación completa
sudo scripts/deploy.sh

# 4. Configurar variables de entorno
sudo nano /opt/silhouettemcp_v4_unified/.env

# 5. Reiniciar servicios
sudo systemctl restart silhouettemcp
sudo systemctl restart nginx
```

### Opción 2: Actualización desde Versión Anterior

```bash
# 1. Extraer package
unzip silhouettemcp_v4_unified.zip
cd silhouettemcp_v4_unified

# 2. Ejecutar actualización (incluye backup automático)
sudo scripts/update.sh
```

### Opción 3: Docker (Desarrollo/Testing)

```bash
# 1. Extraer y usar docker-compose
unzip silhouettemcp_v4_unified.zip
cd silhouettemcp_v4_unified

# 2. Iniciar con Docker
docker-compose --profile basic up -d
```

## ✅ Verificación Post-Instalación

```bash
# Verificar estado de servicios
systemctl status silhouettemcp
systemctl status nginx

# Test endpoints
curl http://localhost:8001/health
curl http://localhost:8001/agents
curl http://localhost:8001/tools

# Verificar dashboard
curl http://localhost:8001/files/dashboard
```

## 📊 Nuevas Características v4.0.0

### Agentes Disponibles (6 total, 51 herramientas)

1. **🗺️ Maps Intelligence** (6 herramientas)
   - Geocodificación, búsqueda de lugares, direcciones

2. **💰 Financial Intelligence** (9 herramientas)
   - Precios de acciones, criptomonedas, análisis de mercado

3. **✈️ Social Media + Travel** (13 herramientas)
   - Redes sociales, planificación de viajes, actividades

4. **📝 Content Creation** (8 herramientas)
   - Generación de contenido, SEO, análisis de tono

5. **🗄️ Database Operations** (13 herramientas - Supabase)
   - Operaciones completas de base de datos

6. **🔍 Research Intelligence** (2 herramientas)
   - Búsqueda web, investigación académica

### 🔧 Mejoras Técnicas

- **Servidor unificado**: Todos los agentes en un solo servidor
- **API consistente**: Endpoints estandarizados
- **Dashboard moderno**: Interfaz mejorada
- **Backup automático**: Protección de datos
- **Docker support**: Contenedorización opcional
- **SSL/HTTPS**: Configuración para producción
- **Monitoring**: Métricas con Prometheus/Grafana

## 🔐 Credenciales por Defecto

- **Dashboard**: http://tu-servidor:8001/files/dashboard
- **Usuario**: alberto.farahb@hotmail.com
- **Contraseña**: Fbalberto1910

⚠️ **IMPORTANTE**: Cambiar contraseña por defecto después de la instalación

## 📚 URLs Importantes

- **Dashboard**: http://tu-servidor:8001/files/dashboard
- **API Docs**: http://tu-servidor:8001/docs
- **Health Check**: http://tu-servidor:8001/health
- **Stats**: http://tu-servidor:8001/stats
- **Agents**: http://tu-servidor:8001/agents
- **Tools**: http://tu-servidor:8001/tools

## 🛠️ Configuración Requerida

Edita `/opt/silhouettemcp_v4_unified/.env`:

```bash
# SUPABASE (OBLIGATORIO)
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key
SUPABASE_ANON_KEY=tu_anon_key
SUPABASE_PROJECT_ID=tu_project_id

# SEGURIDAD (CAMBIAR)
ADMIN_EMAIL=tu-email@ejemplo.com
ADMIN_PASSWORD_HASH=sha256_hash_de_tu_contraseña
```

## 🔧 Comandos Útiles

```bash
# Ver estado
sudo systemctl status silhouettemcp

# Reiniciar
sudo systemctl restart silhouettemcp

# Ver logs
sudo journalctl -u silhouettemcp -f

# Backup manual
sudo scripts/backup.sh

# Ver estadísticas
curl http://localhost:8001/stats
```

## 📞 Soporte

- **Email**: alberto.farahb@hotmail.com
- **Documentación**: Ver carpeta `docs/`
- **Logs**: `/var/log/silhouettemcp/`

## ✅ Checklist Post-Instalación

- [ ] Servicio SilhouetteMCP funcionando
- [ ] Nginx configurado y funcionando
- [ ] Dashboard accesible
- [ ] Variables de entorno configuradas
- [ ] Contraseña cambiada por defecto
- [ ] Tests de API pasando
- [ ] Backup automático configurado

## 🎯 Próximos Pasos

1. **Configurar APIs externas** si necesitas funcionalidades específicas
2. **Configurar SSL** para producción
3. **Personalizar dashboard** según necesidades
4. **Configurar alertas** de monitoreo
5. **Revisar documentación** en `docs/`

---

**¡SilhouetteMCP v4.0.0 FINAL UNIFIED está listo para proporcionar 51 herramientas especializadas en un servidor unificado y optimizado!**

*Para instalación detallada, consulta `docs/README_ACTUALIZACION.md`*
