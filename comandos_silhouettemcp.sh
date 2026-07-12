#!/bin/bash

# ============================================================================
# COMANDOS DIRECTOS - SilhouetteMCP Server
# Referencia rápida para gestión del servidor
# ============================================================================

# CONFIGURACIÓN
DOMAIN="silhouettemcp.albertofarah.com"
PROJECT_DIR="/opt/silhouettemcp"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              Comandos Directos - SilhouetteMCP               ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# FUNCIÓN PARA MOSTRAR COMANDOS
show_commands() {
    echo -e "${GREEN}🌐 URLS PRINCIPALES:${NC}"
    echo "  Dashboard:  https://$DOMAIN"
    echo "  API Health: https://$DOMAIN/health"
    echo "  API Docs:   https://$DOMAIN/docs"
    echo ""
    
    echo -e "${GREEN}🔑 CREDENCIALES:${NC}"
    echo "  Email:    alberto.farahb@hotmail.com"
    echo "  Password: Fbalberto1910"
    echo ""
    
    echo -e "${GREEN}📊 VER ESTADO:${NC}"
    echo "  docker-compose -f $PROJECT_DIR/docker-compose.yml ps"
    echo "  sudo systemctl status silhouettemcp"
    echo ""
    
    echo -e "${GREEN}📋 VER LOGS:${NC}"
    echo "  cd $PROJECT_DIR && docker-compose logs -f"
    echo "  docker-compose logs -f silhouettemcp-server"
    echo "  docker-compose logs -f nginx"
    echo ""
    
    echo -e "${GREEN}🔄 GESTIÓN DE SERVICIOS:${NC}"
    echo "  cd $PROJECT_DIR && docker-compose restart"
    echo "  sudo systemctl restart silhouettemcp"
    echo "  docker-compose down && docker-compose up -d"
    echo ""
    
    echo -e "${GREEN}💾 BACKUP:${NC}"
    echo "  /opt/silhouettemcp/backup.sh"
    echo "  ls -la /opt/silhouettemcp/backups/"
    echo ""
    
    echo -e "${GREEN}🔍 DIAGNÓSTICO:${NC}"
    echo "  curl -f https://$DOMAIN/health"
    echo "  openssl s_client -connect $DOMAIN:443"
    echo "  dig $DOMAIN"
    echo ""
    
    echo -e "${GREEN}🔒 SSL:${NC}"
    echo "  certbot renew"
    echo "  certbot certificates"
    echo ""
    
    echo -e "${GREEN}📁 ARCHIVOS IMPORTANTES:${NC}"
    echo "  Config: $PROJECT_DIR/"
    echo "  Logs:   /var/log/silhouettemcp/"
    echo "  Backup: /opt/silhouettemcp/backups/"
    echo ""
}

# EJECUTAR COMANDOS RÁPIDOS
case "${1:-}" in
    "status"|"ps")
        echo -e "${YELLOW}Estado de servicios:${NC}"
        cd "$PROJECT_DIR" 2>/dev/null && docker-compose ps || echo "Proyecto no encontrado en $PROJECT_DIR"
        ;;
    "logs")
        echo -e "${YELLOW}Logs del servidor (Ctrl+C para salir):${NC}"
        cd "$PROJECT_DIR" 2>/dev/null && docker-compose logs -f silhouettemcp-server || echo "Proyecto no encontrado en $PROJECT_DIR"
        ;;
    "restart")
        echo -e "${YELLOW}Reiniciando servicios:${NC}"
        cd "$PROJECT_DIR" 2>/dev/null && docker-compose restart || echo "Proyecto no encontrado en $PROJECT_DIR"
        ;;
    "backup")
        echo -e "${YELLOW}Creando backup:${NC}"
        /opt/silhouettemcp/backup.sh
        ;;
    "health")
        echo -e "${YELLOW}Verificando health:${NC}"
        curl -f "https://$DOMAIN/health" && echo -e "\n${GREEN}✅ Servidor saludable${NC}" || echo -e "\n${RED}❌ Servidor no responde${NC}"
        ;;
    "ssl")
        echo -e "${YELLOW}Estado de certificados:${NC}"
        certbot certificates
        ;;
    "info")
        show_commands
        ;;
    "update")
        echo -e "${YELLOW}Actualizando servicios:${NC}"
        cd "$PROJECT_DIR" 2>/dev/null && docker-compose pull && docker-compose up -d || echo "Proyecto no encontrado en $PROJECT_DIR"
        ;;
    "stop")
        echo -e "${YELLOW}Deteniendo servicios:${NC}"
        cd "$PROJECT_DIR" 2>/dev/null && docker-compose down || echo "Proyecto no encontrado en $PROJECT_DIR"
        ;;
    "start")
        echo -e "${YELLOW}Iniciando servicios:${NC}"
        cd "$PROJECT_DIR" 2>/dev/null && docker-compose up -d || echo "Proyecto no encontrado en $PROJECT_DIR"
        ;;
    *)
        echo -e "${BLUE}Uso: $0 {status|logs|restart|backup|health|ssl|info|update|stop|start}${NC}"
        echo ""
        show_commands
        ;;
esac