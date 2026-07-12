# 🚀 Guía Completa de Despliegue IRIS en Servidor Principal

## 📋 Resumen Ejecutivo

**¿Deberías migrar IRIS a tu servidor principal?** 
- ✅ **SÍ**, si necesitas **24/7 operativo** y **acceso desde internet**
- ✅ **SÍ**, si planeas **integraciones empresariales**
- ✅ **SÍ**, si quieres **backup automático** y **alta disponibilidad**

## 🎯 Opciones de Despliegue (de Menor a Mayor Complejidad)

### **OPCIÓN 1: Script Automatizado (RECOMENDADA para principiantes)**

```bash
# 1. Subir script a tu servidor
scp script_despliegue_iris.sh usuario@servidor:/tmp/

# 2. Ejecutar en tu servidor
ssh usuario@servidor
sudo bash /tmp/script_despliegue_iris.sh
```

**✅ Ventajas:**
- Automatización completa
- Firewall configurado
- Backup automático
- Servicio systemd
- Docker optimizado

**📊 Lo que hace:**
- Instala Docker y dependencias
- Configura firewall (puertos 80, 443, SSH)
- Crea servicio systemd para auto-inicio
- Configura backup diario a las 2:00 AM
- Verifica funcionamiento

---

### **OPCIÓN 2: Despliegue Manual Básico**

```bash
# 1. Subir archivos del workspace
scp -r /workspace/iris-mcp-integration/ usuario@servidor:/home/usuario/

# 2. Instalar dependencias en servidor
ssh usuario@servidor
sudo apt update && sudo apt install -y python3 python3-pip nodejs npm
cd /home/usuario/iris-mcp-integration

# 3. Instalar dependencias Python
pip3 install fastapi uvicorn requests

# 4. Ejecutar servidor
nohup python3 api/iris_metrics_server.py &

# 5. Configurar nginx (opcional)
sudo apt install -y nginx
# Configurar proxy a localhost:8000
```

---

### **OPCIÓN 3: Docker + Nginx (PROFESIONAL)**

```bash
# 1. Preparar archivos
cd /opt
sudo mkdir iris-server && cd iris-server

# 2. Crear archivos de configuración
# (usar los archivos Dockerfile, docker-compose.yml, nginx.conf que creé)

# 3. Construir y ejecutar
docker-compose build
docker-compose up -d

# 4. Configurar como servicio
sudo systemctl enable docker
sudo systemctl start docker
```

---

## 🏗️ Arquitectura Recomendada

```
Internet → Nginx (Puerto 80/443) → IRIS Server (Puerto 8000)
                    ↓
              Firewall Configurado
                    ↓
              Backup Automático (Diario)
```

### **Puertos a Configurar:**
- **80/443**: Acceso web (HTTP/HTTPS)
- **8000**: API interna (solo localhost o VPN)
- **22**: SSH (solo IP autorizada)

## 📂 Archivos Creados para Despliegue

| Archivo | Descripción | Uso |
|---------|-------------|-----|
| `script_despliegue_iris.sh` | **Script automatizado** | Opción recomendada |
| `docker-compose.iris.yml` | **Configuración Docker completa** | Para usuarios avanzados |
| `nginx.iris.conf` | **Proxy reverso configurado** | Producción con dominio |
| `Dockerfile.iris` | **Imagen Docker optimizada** | Construcción manual |
| `requirements.iris.txt` | **Dependencias Python** | Instalación manual |

## 🔧 Pasos Post-Despliegue

### **1. Verificar Funcionamiento**
```bash
# Verificar servicios
docker-compose ps
sudo systemctl status iris-server

# Probar API
curl http://localhost:8000/health
curl http://localhost:8000/api/metrics/summary

# Ver logs
docker-compose logs -f iris-server
```

### **2. Configurar Dominio (Opcional)**
```bash
# Editar nginx.conf
sudo nano /opt/iris-server/nginx.conf

# Cambiar:
server_name tu-dominio.com;  # Tu dominio real

# Reiniciar nginx
docker-compose restart nginx
```

### **3. Configurar SSL (Recomendado)**
```bash
# Usar Let's Encrypt
sudo apt install certbot
sudo certbot --nginx -d tu-dominio.com
```

### **4. Configurar Backup Remoto**
```bash
# Agregar a crontab para backup a servidor externo
0 3 * * * rsync -avz /opt/iris-server/backups/ usuario@servidor-backup:/backups/iris/
```

## ⚡ Ventajas de Migrar a Servidor Principal

### **🚀 Disponibilidad 24/7**
- **No depende** del workspace local
- **Reinicio automático** con el servidor
- **Monitoreo continuo** sin interrupciones

### **🔒 Seguridad Empresarial**
- **Firewall configurado** automáticamente
- **Acceso controlado** por IP
- **HTTPS** con certificados SSL
- **Backup encriptado**

### **📊 Monitoreo Avanzado**
- **Logs centralizados** en el servidor
- **Métricas persistentes** entre reinicios
- **Alertas configurables** (email, Slack, etc.)
- **Dashboard compartido** con el equipo

### **🛠️ Mantenimiento Simplificado**
- **Un solo punto** de administración
- **Actualizaciones centralizadas**
- **Versionado** de configuraciones
- **Rollback fácil** con backups

## 💡 Casos de Uso Específicos

### **🏢 Para Empresa/Equipo**
```bash
# URL compartida: http://tu-dominio.com
# Acceso: Diferentes roles (admin, viewer, etc.)
# Notificaciones: Slack/Email para alertas
# Backup: Servidor de archivos dedicado
```

### **🔬 Para Desarrollo/Testing**
```bash
# URL local: http://IP-servidor
# Acceso: VPN o IP específica
# Logs: Centralizados para debugging
# Testing: Integración con CI/CD
```

### **🎯 Para Producción**
```bash
# URL pública: https://api.tu-empresa.com
# Seguridad: Certificados SSL, firewall, rate limiting
# Escalabilidad: Load balancer, múltiples instancias
# Compliance: Logs auditables, backups encriptados
```

## 📈 Costos y Recursos

### **💰 Costos Estimados (Mensuales)**
- **VPS Básico** (1 CPU, 1GB RAM): $5-10/mes
- **VPS Producción** (2 CPU, 4GB RAM): $15-25/mes
- **Cloud AWS/GCP**: $20-40/mes
- **Dominio**: $10-15/año
- **SSL Certificate**: Gratis (Let's Encrypt)

### **⚙️ Recursos del Sistema**
- **CPU**: 0.5-1 core (usado esporádicamente)
- **RAM**: 512MB - 1GB
- **Disco**: 5-10GB (incluyendo backups)
- **Red**: Mínimo 1Mbps

## 🔄 Migración Sin Downtime

```bash
# 1. Preparar nuevo servidor
./script_despliegue_iris.sh

# 2. Sincronizar datos (si hay persistencia)
rsync -avz /workspace/iris-mcp-integration/ usuario@nuevo-servidor:/opt/iris-server/

# 3. Configurar proxy temporal
# Nginx en servidor viejo → Redirigir a nuevo servidor

# 4. Cambiar DNS
# Apuntar tu-dominio.com al nuevo servidor

# 5. Verificar funcionamiento
# Apagar servidor viejo
```

## ❓ FAQ - Preguntas Frecuentes

**P: ¿Cuánto tiempo toma el despliegue?**
R: **5-15 minutos** con el script automatizado

**P: ¿Puedo tener múltiples instancias?**
R: **Sí**, con load balancer para alta disponibilidad

**P: ¿Qué pasa si el servidor se reinicia?**
R: **Auto-inicio** configurado, vuelve a funcionar automáticamente

**P: ¿Puedo acceder desde móvil?**
R: **Sí**, cualquier navegador web funciona

**P: ¿Hay límites de uso?**
R: **No**, ilimitado para uso normal

## 🎯 Recomendación Final

**Para la mayoría de usuarios: USAR OPCIÓN 1 (Script Automatizado)**

```bash
# Comando único para despliegue completo:
wget -O - https://raw.githubusercontent.com/tu-repo/iris-deploy.sh | sudo bash
```

**¡Tu servidor IRIS estará 100% operativo y accesible desde cualquier lugar en menos de 15 minutos!** 🚀

---

## 📞 Próximos Pasos

1. **Elige tu opción** de despliegue
2. **Ejecuta el script** o sigue la guía manual
3. **Configura tu dominio** (opcional)
4. **Habilita SSL** para seguridad
5. **Configura alertas** para monitoreo proactivo

**¿Necesitas ayuda con algún paso específico?**