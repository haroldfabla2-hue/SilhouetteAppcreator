# Patrones de Agentes SilhouetteMCP - Para agregar 15+ agentes

## 🚀 **Scripts para desplegar múltiples agentes**

### **E-commerce (5 agentes)**
```bash
# 1. Product Manager Agent
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"product_manager","config":{"name":"Product Manager","capabilities":["catalog","inventario","precios"],"database":"ecommerce_db"}}'

# 2. Order Processing Agent  
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"order_processor","config":{"name":"Order Processor","capabilities":["pedidos","envios","tracking"],"platform":"woocommerce"}}'

# 3. Customer Service Agent
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"customer_service","config":{"name":"Customer Service","capabilities":["chat","soporte","tickets"],"language":"es"}}'

# 4. Analytics Agent
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"analytics","config":{"name":"E-commerce Analytics","capabilities":["ventas","conversion","reportes"],"dashboard":"google_analytics"}}'

# 5. Marketing Agent
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"marketing","config":{"name":"Marketing Manager","capabilities":["campanas","seo","email_marketing"}}'
```

### **CRM/Cliente (4 agentes)**
```bash
# 6. Lead Generator Agent
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"lead_generator","config":{"name":"Lead Generator","capabilities":["prospectos","scoring","automatizacion"]}}'

# 7. Sales Agent
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"sales","config":{"name":"Sales Agent","capabilities":["cotizaciones","negociacion","cierre"]}}'

# 8. Customer Success Agent  
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"customer_success","config":{"name":"Customer Success","capabilities":["onboarding","retention","expansion"]}}'

# 9. Relationship Manager Agent
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"relationship_manager","config":{"name":"Relationship Manager","capabilities":["comunicacion","meetings","follow_up"]}}'
```

### **Contenido/Marketing (3 agentes)**
```bash
# 10. Content Creator Agent
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"content_creator","config":{"name":"Content Creator","capabilities":["articulos","social_media","seo_content"]}}'

# 11. Social Media Agent
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"social_media","config":{"name":"Social Media Manager","capabilities":["scheduling","engagement","analytics"]}}'

# 12. SEO Agent
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"seo","config":{"name":"SEO Specialist","capabilities":["keywords","backlinks","rankings"]}}'
```

### **Datos/Análisis (3 agentes)**
```bash
# 13. Data Analytics Agent
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"data_analytics","config":{"name":"Data Analytics","capabilities":["reportes","predicciones","dashboard"]}}'

# 14. Business Intelligence Agent  
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"business_intelligence","config":{"name":"BI Specialist","capabilities":["kpi","reports","forecasting"]}}'

# 15. Compliance Agent
curl -s "https://silhouettemcp.albertofarah.com/api/agents/deploy" \
  -X POST \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc" \
  -H "Content-Type: application/json" \
  -d '{"agent_type":"compliance","config":{"name":"Compliance Officer","capabilities":["auditoria","regulaciones","reportes"]}}'
```

## 🎯 **Resultado Esperado:**
- **Total Agentes**: 15+ (3 actuales + 12 nuevos)
- **Dashboard**: Métricas en tiempo real
- **Capacidades**: Multi-dominio especializado

## 📊 **Verificar después del despliegue:**
```bash
curl -s "https://silhouettemcp.albertofarah.com/api/agents" \
  -H "Authorization: Bearer sk-d8RahMZH5B8RIeSiLYx_ktBy5c9Ic8VkuTXo_2JkVzc"
```