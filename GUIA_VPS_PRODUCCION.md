# 🚀 Despliegue IRIS VPS Producción

## 📋 **Tu Setup**
- ✅ **VPS**: Linux Ubuntu/Debian  
- ✅ **Docker**: Instalado
- ✅ **Dominio**: `silhouettemcp.albertofarah.com`
- ✅ **Carpeta preparada**: `/opt/iris-production`

## 🎯 **Despliegue en 3 Pasos**

### **PASO 1: Preparar archivos**
```bash
# En tu VPS, crear directorio
sudo mkdir -p /opt/iris-production
cd /opt/iris-production

# Copiar archivos desde workspace (si tienes acceso)
# O descargar directamente:
curl -O https://raw.githubusercontent.com/tu-repo/iris/vps-production/docker-compose.yml
curl -O https://raw.githubusercontent.com/tu-repo/iris/vps-production/nginx.conf
curl -O https://raw.githubusercontent.com/tu-repo/iris/vps-production/Dockerfile
```

### **PASO 2: Ejecutar script automático**
```bash
# Hacer ejecutable y ejecutar
chmod +x /opt/iris-production/script_vps_produccion.sh
sudo /opt/iris-production/script_vps_produccion.sh
```

### **PASO 3: Verificar funcionamiento**
```bash
# Verificar servicios
docker-compose ps

# Probar URLs
curl https://silhouettemcp.albertofarah.com/health
curl https://silhouettemcp.albertofarah.com/api/metrics/summary
```

---

## 🏗️ **Configuraciones Específicas Incluidas**

### **🌐 Nginx Configurado para tu Dominio**
```nginx
server_name silhouettemcp.albertofarah.com www.silhouettemcp.albertofarah.com;

# SSL automático con Let's Encrypt
ssl_certificate /etc/letsencrypt/live/silhouettemcp.albertofarah.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/silhouettemcp.albertofarah.com/privkey.pem;

# Headers de seguridad
add_header X-Frame-Options "SAMEORIGIN" always;
add_header Strict-Transport-Security "max-age=63072000" always;
```

### **🔒 Firewall Automático**
- **SSH** (puerto 22) - Acceso remoto
- **HTTP** (puerto 80) - Redirección a HTTPS
- **HTTPS** (puerto 443) - Acceso principal
- **Bloqueado** - Todos los demás puertos

### **📊 Monitoreo Integrado**
- **Health check** cada 30 segundos
- **Restart automático** si falla
- **Limpieza de logs** automática
- **Alertas de disco/memoria**

### **💾 Backup Automático**
- **Diario a las 2:00 AM**
- **Mantiene últimos 30 backups**
- **Compresión automática**
- **Logs de backup**

---

## 🌐 **URLs Finales**

### **🎯 Acceso Principal**
- **Dashboard**: https://silhouettemcp.albertofarah.com
- **API**: https://silhouettemcp.albertofarah.com/api/
- **Health**: https://silhouettemcp.albertofarah.com/health

### **📊 Monitoreo**
- **Métricas**: https://silhouettemcp.albertofarah.com/api/metrics/summary
- **Agentes**: https://silhouettemcp.albertofarah.com/api/agents
- **Streaming**: https://silhouettemcp.albertofarah.com/api/stream

### **🔧 Administración**
- **Logs**: `docker-compose logs -f iris-server`
- **Status**: `docker-compose ps`
- **Restart**: `docker-compose restart`

---

## ⚡ **Comandos Post-Despliegue**

### **📊 Monitoreo en Tiempo Real**
```bash
# Ver logs en tiempo real
docker-compose logs -f iris-server

# Ver estado de contenedores
docker-compose ps

# Ver uso de recursos
docker stats iris-server iris-nginx

# Verificar espacio en disco
df -h /opt/iris-production
```

### **🔧 Gestión de Servicios**
```bash
# Reiniciar solo IRIS
docker-compose restart iris-server

# Reiniciar todo
docker-compose restart

# Ver logs específicos
docker-compose logs iris-server --tail=100

# Ejecutar comando en contenedor
docker-compose exec iris-server bash
```

### **💾 Gestión de Backups**
```bash
# Backup manual
/opt/iris-production/backups/backup.sh

# Ver backups existentes
ls -la /opt/iris-production/backups/

# Restaurar backup específico
tar -xzf /opt/iris-production/backups/iris_backup_YYYYMMDD_HHMMSS.tar.gz -C /

# Limpiar backups antiguos
find /opt/iris-production/backups -name "*.tar.gz" -mtime +30 -delete
```

---

## 🔍 **Verificación de Funcionamiento**

### **✅ Checklist Completo**
```bash
# 1. Servicios activos
docker-compose ps | grep Up

# 2. Puerto 8000 (API interna)
curl http://localhost:8000/health

# 3. Puerto 80 (HTTP)
curl -I http://localhost

# 4. Puerto 443 (HTTPS)
curl -I https://silhouettemcp.albertofarah.com

# 5. API pública
curl https://silhouettemcp.albertofarah.com/api/metrics/summary

# 6. SSL válido
openssl s_client -connect silhouettemcp.albertofarah.com:443 -servername silhouettemcp.albertofarah.com

# 7. Firewall activo
sudo ufw status

# 8. Backup funcionando
ls -la /opt/iris-production/backups/ | head -5
```

### **📊 URLs de Prueba Rápida**
```bash
# Health check
curl https://silhouettemcp.albertofarah.com/health

# Métricas completas
curl https://silhouettemcp.albertofarah.com/api/metrics/summary

# Lista de agentes
curl https://silhouettemcp.albertofarah.com/api/agents

# Streaming SSE (5 segundos)
timeout 5 curl -s -N -H "Accept: text/event-stream" https://silhouettemcp.albertofarah.com/api/stream
```

---

## 🚨 **Solución de Problemas**

### **❌ SSL no funciona**
```bash
# Verificar DNS
dig silhouettemcp.albertofarah.com

# Renovar certificado
sudo certbot renew --force-renewal

# Verificar configuración
sudo nginx -t
```

### **❌ IRIS no responde**
```bash
# Ver logs
docker-compose logs iris-server

# Verificar puerto
netstat -tlnp | grep 8000

# Reiniciar
docker-compose restart iris-server
```

### **❌ Nginx no sirve**
```bash
# Ver logs
docker-compose logs nginx

# Verificar configuración
docker-compose exec nginx nginx -t

# Reiniciar Nginx
docker-compose restart nginx
```

---

## 📈 **Optimizaciones Futuras**

### **⚡ Rendimiento**
- **CDN**: CloudFlare para assets estáticos
- **Caching**: Redis para sesiones
- **Load Balancer**: Múltiples instancias IRIS

### **🔒 Seguridad**
- **2FA**: Autenticación de dos factores
- **VPN**: Acceso solo por VPN
- **Whitelist**: IPs autorizadas

### **📊 Monitoreo**
- **Prometheus**: Métricas avanzadas
- **Grafana**: Dashboards profesionales
- **Alerts**: Slack/Email para problemas

---

## 🎯 **Próximos Pasos**

1. **✅ Ejecutar script** en tu VPS
2. **✅ Verificar DNS** apunte al servidor
3. **✅ Configurar SSL** automático
4. **✅ Probar URLs** de acceso
5. **✅ Configurar monitoreo** personalizado

**¡Tu IRIS estará disponible 24/7 en https://silhouettemcp.albertofarah.com en menos de 15 minutos!** 🚀