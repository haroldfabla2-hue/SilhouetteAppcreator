# SilhouetteMCP v4.0.0 - Guía de Actualización Completa

## 📋 Descripción General

Esta guía proporciona instrucciones detalladas para actualizar el sistema SilhouetteMCP de la versión anterior (3 agentes) a la nueva versión **FINAL UNIFIED v4.0.0** que incluye **51 herramientas** distribuidas en **6 agentes especializados**.

### 🎯 Objetivos de la Actualización

- **Escalar de 3 a 6 agentes especializados**
- **Agregar 51 herramientas total** (vs. herramientas anteriores)
- **Mantener compatibilidad** con datos y configuraciones existentes
- **Mejorar rendimiento** y arquitectura del sistema
- **Simplificar gestión** con dashboard unificado

## 🏗️ Arquitectura de la Nueva Versión

### Agentes Incluidos

| Agente | Herramientas | Descripción |
|--------|--------------|-------------|
| **Maps Intelligence** | 6 | Geolocalización, mapas, direcciones, distancias |
| **Financial Intelligence** | 9 | Mercados, precios, análisis financiero |
| **Social Media + Travel** | 13 | Redes sociales, planificación de viajes, actividades |
| **Content Creation** | 8 | Generación de contenido, SEO, análisis de tono |
| **Database Operations** | 13 | Operaciones completas de Supabase |
| **Research Intelligence** | 2 | Búsqueda web, investigación académica |
| **TOTAL** | **51** | **Servidor unificado** |

## 📦 Contenido del Package

```
silhouettemcp_v4_unified/
├── server/                          # Archivos principales
│   ├── silhouettemcp_server_unified.py
│   ├── silhouettemcp_dashboard_expanded.html
│   └── requirements.txt
├── config/                          # Configuración del sistema
│   ├── nginx.conf
│   ├── silhouettemcp.service
│   └── docker-compose.yml
├── scripts/                         # Scripts de automatización
│   ├── deploy.sh
│   ├── update.sh
│   └── backup.sh
└── docs/                           # Documentación completa
    ├── README_ACTUALIZACION.md
    ├── API_ENDPOINTS.md
    ├── GUIA_USUARIO.md
    └── CHANGELOG.md
```

## 🚀 Métodos de Instalación

### Opción 1: Instalación Completa (Recomendada)

```bash
# 1. Descargar y extraer el package
wget https://ejemplo.com/silhouettemcp_v4_unified.zip
unzip silhouettemcp_v4_unified.zip
cd silhouettemcp_v4_unified

# 2. Ejecutar script de despliegue completo
sudo scripts/deploy.sh

# 3. Configurar variables de entorno
sudo nano /opt/silhouettemcp_v4_unified/.env

# 4. Reiniciar servicios
sudo systemctl restart silhouettemcp
sudo systemctl restart nginx
```

### Opción 2: Actualización desde Versión Anterior

```bash
# 1. Crear backup de la versión actual
sudo scripts/backup.sh

# 2. Ejecutar script de actualización
sudo scripts/update.sh

# 3. Verificar funcionamiento
curl http://localhost:8001/health
```

### Opción 3: Instalación con Docker

```bash
# 1. Usar docker-compose con profile básico
cd silhouettemcp_v4_unified
docker-compose --profile basic up -d

# 2. Verificar contenedores
docker-compose ps
docker-compose logs -f
```

## ⚙️ Configuración Requerida

### Variables de Entorno Críticas

Edita el archivo `/opt/silhouettemcp_v4_unified/.env`:

```bash
# === CONFIGURACIÓN BÁSICA ===
PORT=8001
DEBUG=false

# === SUPABASE (OBLIGATORIO) ===
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=tu_service_role_key
SUPABASE_ANON_KEY=tu_anon_key
SUPABASE_PROJECT_ID=tu_project_id

# === AUTENTICACIÓN ===
ADMIN_EMAIL=alberto.farahb@hotmail.com
ADMIN_PASSWORD_HASH=sha256_hash_de_tu_contraseña
```

### Configuración de SSL (Producción)

```bash
# 1. Obtener certificados Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d tu-dominio.com

# 2. O configurar certificados manuales en nginx.conf
sudo nano /etc/nginx/sites-available/silhouettemcp
# Actualizar rutas SSL:
# ssl_certificate /ruta/a/certificado.crt
# ssl_certificate_key /ruta/a/private.key
```

## 🔧 Configuración del Sistema

### Servicios Configurados

- **silhouettemcp.service**: Servicio principal del servidor
- **nginx**: Proxy reverso y servidor web
- **fail2ban**: Protección contra ataques
- **cron**: Tareas automatizadas (backup)

### Puertos Utilizados

- **8001**: Puerto principal del servidor
- **80**: HTTP (redirige a HTTPS)
- **443**: HTTPS (requiere configuración SSL)
- **6379**: Redis (opcional)
- **5432**: PostgreSQL (opcional)

### Archivos de Configuración

- **Servidor**: `/opt/silhouettemcp_v4_unified/.env`
- **Nginx**: `/etc/nginx/sites-available/silhouettemcp`
- **Servicio**: `/etc/systemd/system/silhouettemcp.service`
- **Logs**: `/var/log/silhouettemcp/`

## 📊 Verificación de la Instalación

### Tests Automáticos

```bash
# Verificar estado de servicios
systemctl status silhouettemcp
systemctl status nginx
systemctl status fail2ban

# Verificar puertos
netstat -tuln | grep 8001

# Test endpoint de salud
curl http://localhost:8001/health

# Verificar dashboard
curl http://localhost:8001/files/dashboard
```

### URLs de Verificación

- **Salud**: http://tu-servidor:8001/health
- **Estadísticas**: http://tu-servidor:8001/stats
- **Agentes**: http://tu-servidor:8001/agents
- **Herramientas**: http://tu-servidor:8001/tools
- **Dashboard**: http://tu-servidor:8001/files/dashboard
- **Documentación**: http://tu-servidor:8001/docs

## 🔄 Proceso de Migración de Datos

### Backup Automático

El script de actualización crea automáticamente un backup que incluye:

- ✅ Configuraciones existentes
- ✅ Datos de aplicaciones
- ✅ Variables de entorno
- ✅ Logs del sistema
- ✅ Configuraciones de servicios

```bash
# Los backups se guardan en:
/var/backups/silhouettemcp/silhouettemcp_backup_YYYYMMDD_HHMMSS.tar.gz
```

### Restauración en Caso de Error

```bash
# 1. Identificar el backup más reciente
ls -la /var/backups/silhouettemcp/

# 2. Restaurar backup
cd /var/backups/silhouettemcp/
tar -xzf silhouettemcp_backup_YYYYMMDD_HHMMSS.tar.gz

# 3. Restaurar archivos
cp -r backup_name/* /opt/silhouettemcp_v4_unified/

# 4. Reiniciar servicios
systemctl restart silhouettemcp
systemctl restart nginx
```

## 🛠️ Comandos de Gestión

### Gestión del Servicio

```bash
# Iniciar servicio
sudo systemctl start silhouettemcp

# Detener servicio
sudo systemctl stop silhouettemcp

# Reiniciar servicio
sudo systemctl restart silhouettemcp

# Ver estado
sudo systemctl status silhouettemcp

# Ver logs en tiempo real
sudo journalctl -u silhouettemcp -f

# Ver logs históricos
sudo journalctl -u silhouettemcp --since "1 hour ago"
```

### Backup Manual

```bash
# Crear backup completo
sudo scripts/backup.sh

# Ver backups disponibles
ls -la /var/backups/silhouettemcp/

# Limpiar backups antiguos (automático)
sudo find /var/backups/silhouettemcp/ -name "*.tar.gz" -mtime +30 -delete
```

### Actualización

```bash
# Actualizar a nueva versión
sudo scripts/update.sh

# Verificar integridad de la instalación
curl -s http://localhost:8001/health | jq '.'
```

## 🔍 Solución de Problemas

### Problemas Comunes

#### 1. Servicio no inicia

```bash
# Verificar logs
sudo journalctl -u silhouettemcp -n 50

# Verificar configuración
sudo systemctl status silhouettemcp

# Verificar permisos
ls -la /opt/silhouettemcp_v4_unified/

# Verificar entorno virtual
ls -la /opt/silhouettemcp_v4_unified/venv/bin/python
```

#### 2. Puerto 8001 no disponible

```bash
# Verificar procesos usando el puerto
sudo netstat -tulpn | grep 8001

# Terminar procesos conflictivos
sudo kill -9 PID

# Reiniciar servicio
sudo systemctl restart silhouettemcp
```

#### 3. Nginx no funciona

```bash
# Probar configuración
sudo nginx -t

# Ver logs de nginx
sudo tail -f /var/log/nginx/error.log

# Reiniciar nginx
sudo systemctl restart nginx
```

#### 4. Problemas de permisos

```bash
# Reconfigurar permisos
sudo chown -R www-data:www-data /opt/silhouettemcp_v4_unified/
sudo chmod -R 755 /opt/silhouettemcp_v4_unified/

# Para logs
sudo chown -R syslog:adm /var/log/silhouettemcp/
```

### Logs Importantes

- **Aplicación**: `/var/log/silhouettemcp/app.log`
- **Sistema**: `journalctl -u silhouettemcp`
- **Nginx**: `/var/log/nginx/error.log`
- **Actualización**: `/var/log/silhouettemcp/update_*.log`
- **Backup**: `/var/log/silhouettemcp/backup_*.log`

## 🔒 Seguridad

### Configuraciones de Seguridad Incluidas

- ✅ **Firewall UFW** configurado
- ✅ **Fail2Ban** para protección contra ataques
- ✅ **Headers de seguridad** en nginx
- ✅ **Rate limiting** configurado
- ✅ **Logs de auditoría** habilitados

### Recomendaciones Adicionales

1. **Cambiar credenciales por defecto**
2. **Configurar SSL/TLS** para producción
3. **Configurar monitoreo** de seguridad
4. **Mantener sistema actualizado**
5. **Configurar alertas** de seguridad

## 📈 Monitoreo y Mantenimiento

### Métricas Disponibles

```bash
# Estadísticas del sistema
curl http://localhost:8001/stats

# Health check detallado
curl http://localhost:8001/health | jq

# Ver agentes disponibles
curl http://localhost:8001/agents | jq '.agents[]'
```

### Tareas de Mantenimiento

#### Diario (Automático)
- ✅ Backup de datos
- ✅ Limpieza de logs antiguos
- ✅ Verificación de salud del sistema

#### Semanal
- 🔄 Revisar logs de seguridad
- 🔄 Verificar espacio en disco
- 🔄 Actualizar dependencias de seguridad

#### Mensual
- 📊 Revisar métricas de uso
- 🔄 Actualizar sistema operativo
- 🔄 Probar procedimientos de backup/restore

## 🆘 Soporte

### Recursos de Ayuda

1. **Documentación completa**: `/opt/silhouettemcp_v4_unified/docs/`
2. **API Documentation**: http://tu-servidor:8001/docs
3. **Logs del sistema**: `/var/log/silhouettemcp/`
4. **Comandos de diagnóstico**: Ver sección de troubleshooting

### Contacto

- **Email**: alberto.farahb@hotmail.com
- **Dashboard**: http://tu-servidor:8001/files/dashboard
- **GitHub Issues**: (si aplica)

## ✅ Lista de Verificación Post-Instalación

- [ ] Servicio SilhouetteMCP funcionando
- [ ] Nginx configurado y funcionando
- [ ] Puerto 8001 accesible
- [ ] Dashboard accesible
- [ ] Documentación API disponible
- [ ] Variables de entorno configuradas
- [ ] SSL configurado (producción)
- [ ] Backup automático funcionando
- [ ] Logs configurados correctamente
- [ ] Firewall configurado
- [ ] Fail2Ban configurado
- [ ] Tests de verificación pasando

## 🎯 Próximos Pasos

1. **Configurar APIs externas** necesarias para las herramientas
2. **Personalizar dashboard** según necesidades
3. **Configurar alertas** de monitoreo
4. **Implementar CI/CD** para actualizaciones
5. **Configurar backup externo** para disaster recovery

---

## 📝 Notas Importantes

- **Compatibilidad**: La actualización mantiene compatibilidad con configuraciones existentes
- **Backup**: Siempre crear backup antes de actualizar
- **Downtime**: Esperar downtime de 5-15 minutos durante la actualización
- **Rollback**: Procedimientos de rollback disponibles en caso de problemas

**¡La nueva versión SilhouetteMCP v4.0.0 FINAL UNIFIED está lista para proporcionar 51 herramientas especializadas en un servidor unificado y optimizado!**
