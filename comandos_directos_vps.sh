#!/bin/bash
# COMANDOS DIRECTOS PARA VPS - Copiar y pegar

# 1. CREAR ESTRUCTURA DE DIRECTORIOS
echo "🔧 Creando estructura..."
sudo mkdir -p /opt/iris-production/{data,logs,backups,ssl,frontends,monitoring}
cd /opt/iris-production
sudo chown $USER:$USER /opt/iris-production

# 2. CREAR DOCKER-COMPOSE.YML
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  iris-server:
    build: .
    container_name: iris-metrics-server
    ports:
      - "127.0.0.1:8000:8000"
    environment:
      - IRIS_ENV=production
      - IRIS_LOG_LEVEL=INFO
      - IRIS_DOMAIN=silhouettemcp.albertofarah.com
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  nginx:
    image: nginx:alpine
    container_name: iris-nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./frontends:/var/www/html:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - iris-server
    restart: unless-stopped

volumes:
  iris_data:
  iris_logs:
EOF

# 3. CREAR DOCKERFILE
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN pip install fastapi uvicorn requests

COPY iris-mcp-integration/ ./iris-mcp-integration/
RUN mkdir -p /app/data /app/logs

EXPOSE 8000
CMD ["python3", "iris-mcp-integration/api/iris_metrics_server.py"]
EOF

# 4. CREAR NGINX.CONF
cat > nginx.conf << 'EOF'
events { worker_connections 1024; }

http {
    upstream iris_backend { server iris-server:8000; }

    server {
        listen 80;
        server_name silhouettemcp.albertofarah.com www.silhouettemcp.albertofarah.com;

        location /api/ {
            proxy_pass http://iris_backend/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            root /var/www/html;
            try_files $uri $uri/ /index.html;
        }

        location /health {
            proxy_pass http://iris_backend/health;
            access_log off;
        }
    }
}
EOF

# 5. CONFIGURAR FIREWALL
echo "🔥 Configurando firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
echo "y" | sudo ufw enable

# 6. CONSTRUIR Y EJECUTAR
echo "🚀 Construyendo y ejecutando..."
docker-compose build --no-cache
docker-compose up -d

# 7. VERIFICAR
echo "✅ Verificando funcionamiento..."
sleep 10
docker-compose ps
curl -s http://localhost:8000/health && echo " - API OK"
curl -s http://localhost/health && echo " - Nginx OK"

echo ""
echo "🎉 ¡IRIS desplegado!"
echo "📍 URLs:"
echo "   • https://silhouettemcp.albertofarah.com"
echo "   • https://silhouettemcp.albertofarah.com/api/metrics/summary"
echo ""
echo "🔧 Comandos útiles:"
echo "   • Ver logs: docker-compose logs -f"
echo "   • Reiniciar: docker-compose restart"
echo "   • Status: docker-compose ps"