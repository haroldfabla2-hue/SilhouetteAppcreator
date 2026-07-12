#!/bin/bash
# ===============================================================================
# COMANDOS RÁPIDOS PARA GEMINI CLI - SILHOUETTEMCP
# ===============================================================================
# EJECUTAR EN TU VPS DESPUÉS DE SUBIR LOS ARCHIVOS
# ===============================================================================

echo "🚀 COMANDOS PARA GEMINI CLI - SILHOUETTEMCP"
echo "============================================="

# Comandos paso a paso
echo ""
echo "📁 1. SUBIR ARCHIVOS (desde tu máquina local):"
echo "   scp -r . user@TU-VPS-IP:/tmp/silhouettemcp_deploy/"
echo ""
echo "🔑 2. CONECTAR A VPS:"
echo "   ssh user@TU-VPS-IP"
echo "   cd /tmp/silhouettemcp_deploy"
echo ""
echo "▶️  3. EJECUTAR CON GEMINI CLI:"
echo "   gemini run --file=deploy_with_gemini.sh"
echo ""
echo "⚡ O EJECUTAR DIRECTAMENTE:"
echo "   bash deploy_with_gemini.sh"
echo ""
echo "🎯 4. VERIFICAR DESPLIEGUE:"
echo "   curl https://silhouettemcp.albertofarah.com/health"
echo ""
echo "📊 5. ACCEDER AL DASHBOARD:"
echo "   https://silhouettemcp.albertofarah.com/admin/dashboard"
echo "   Email: alberto.farahb@hotmail.com"
echo "   Password: Fbalberto1910"
echo ""
echo "✅ ¡LISTO! El sistema se desplegará automáticamente"
echo ""
echo "🛠️ COMANDOS DE GESTIÓN (después del despliegue):"
echo "   cd /opt/silhouettemcp"
echo "   ./comandos_silhouettemcp.sh status"
echo "   ./comandos_silhouettemcp.sh restart"
echo "   ./comandos_silhouettemcp.sh logs"
echo ""
echo "🔧 Archivos creados:"
ls -la