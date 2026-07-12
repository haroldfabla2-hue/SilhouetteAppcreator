# Plan de Investigación: Opciones Gratuitas del Ecosistema MiniMax

## Objetivo
Investigar en profundidad todas las opciones gratuitas disponibles en el ecosistema MiniMax, incluyendo modelos open source, herramientas MCP, capacidades del agente gratuito y opciones de integración.

## Análisis del Archivo de Entrada
- **Información clave identificada**:
  - MiniMax Agent gratuito hasta agotar capacidad de servidores (octubre 2025)
  - M1 (1M tokens) y M2 (código/agentes) son open-source en GitHub/HuggingFace
  - Speech 2.6 HD disponible gratuitamente
  - Herramientas MCP (Search, TTS, etc.) gratuitas
  - Dos modos: Lightning (gratuito) y Pro Mode

## Tareas de Investigación

### 1. Modelos M1/M2 Open Source
- [x] 1.1 Localizar repositorios oficiales de M1 en GitHub/HuggingFace
- [x] 1.2 Localizar repositorios oficiales de M2 en GitHub/HuggingFace  
- [x] 1.3 Verificar métodos de descarga y acceso a pesos
- [x] 1.4 Investigar APIs gratuitas disponibles
- [x] 1.5 Documentar requisitos de hardware local

### 2. MiniMax Agent Gratuito
- [x] 2.1 Investigar capacidades exactas del modo gratuito
- [x] 2.2 Documentar límites de uso (tokens, RPM, etc.)
- [x] 2.3 Verificar si hay API disponible para el agente gratuito
- [x] 2.4 Comparar Lightning Mode vs Pro Mode
- [x] 2.5 Identificar restricciones específicas

### 3. Herramientas MCP Gratuitas
- [x] 3.1 Catalogar todos los servidores MCP de MiniMax gratuitos
- [x] 3.2 Documentar capacidades de MiniMax-Search
- [x] 3.3 Documentar capacidades de MiniMax-TTS (Speech 2.6 HD)
- [x] 3.4 Investigar otras herramientas MCP disponibles
- [x] 3.5 Verificar límites de llamadas por minuto/día
- [x] 3.6 Documentar proceso de instalación

### 4. Capacidades Multimedia Gratuitas
- [x] 4.1 Investigar acceso gratuito a Speech 2.6 HD
- [x] 4.2 Verificar opciones gratuitas de video generation
- [x] 4.3 Documentar capacidades de análisis multimodal
- [x] 4.4 Investigar límites de uso multimedia

### 5. Integración y Despliegue
- [x] 5.1 Documentar integración local de modelos M1/M2
- [x] 5.2 Documentar integración vía API
- [x] 5.3 Especificar requisitos de hardware
- [x] 5.4 Investigar opciones de despliegue cloud
- [x] 5.5 Documentar casos de éxito

### 6. Casos de Uso y Ejemplos
- [x] 6.1 Recopilar casos de éxito documentados
- [x] 6.2 Crear ejemplos prácticos de uso
- [x] 6.3 Documentar mejores prácticas

## Hallazgos Clave hasta Ahora
- **MiniMax M1**: Disponible en GitHub/HuggingFace, arquitectura MoE híbrida, 456B parámetros totales, 45.9B activos
- **MiniMax M2**: Disponible en GitHub/HuggingFace, modelo MoE optimizado para agentes, 230B total/10B activos
- **API Gratuita**: Disponible hasta 7 de noviembre de 2025 para M2
- **MCP Server**: Disponible con herramientas de TTS, image/video generation, music generation
- **Licencias**: M1 (Apache-2.0), M2 (MIT), MCP (MIT)

## Fuentes Investigadas
- GitHub repositorios oficiales de MiniMax
- HuggingFace model cards
- Documentación oficial de APIs
- Artículos de análisis técnico

## Fuentes a Investigar
- Sitio oficial minimax.io
- Repositorios GitHub oficiales de MiniMax
- HuggingFace Model Hub
- Documentación oficial de APIs
- Comunidad y casos de uso
- Benchmarks y comparaciones

## Entregables
- Documento final: `docs/minimax_opciones_gratuitas.md`
- URLs exactas y procedimientos de instalación
- Límites de uso documentados
- Casos de éxito verificados

---
**Estado**: Completado - 2025-11-03 23:00:00