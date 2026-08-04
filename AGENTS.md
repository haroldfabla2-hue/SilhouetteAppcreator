# AGENTS.md - Master Architecture & Agent Operational Guidelines

Welcome to **SilhouetteAppcreator (MCP Server Superior)** — *El Mejor Agente y Sistema Autónomo de Desarrollo de Software del Mercado*.

This file serves as the definitive reference guide, index of documentation, architectural handbook, and operational protocol for any AI Agent or developer working on this codebase.

---

## 🏛️ Project Overview & Technology Stack

**SilhouetteMCP / SilhouetteAppcreator** is an enterprise-grade, multi-agent AI orchestrator and cognitive development system engineered to surpass Claude Code, Devin, Cursor, and Codex:
- **Backend:** FastAPI, Python 3.12, Asyncio, LiteLLM, Redis Pub/Sub.
- **Cognitive Engines (`silhouette-brain` v3.0):** 4-Tier Memory System (Working Redis, Episodic SQLite, Semantic FastEmbed, Deep Graph Neo4j) + 4 Background Daemons (Curiosity, Janitor, Dreamer, Evolution).
- **Symbolic Logic & Reasoning:** Microsoft Z3 Solver (`z3-solver` OODA Loop), MCTS (Monte Carlo Tree Search Code Planner), Debate Swarm Matrix (Creator vs Critic + Judge).
- **OS & Capability Layer:** Playwright Chromium Web Control, `psutil` OS Process Control, FastMCP Dynamic Server Factory, Self-Healing Subprocess Sandbox.
- **Frontend Studio UI:** React 18, TypeScript, Vite, TailwindCSS, Alt+1..8 Keyboard Navigation, Omni-Search (Cmd+K), Real-time Recharts & AI Error Explainer.
- **Omnichannel Security:** Anti-Prompt Injection Threat Classifier (`SecurityGuard`) over Telegram, WhatsApp, and Discord.

---

## 📑 Index of Project Documentation & Memories

All documentation files in this repository are categorized below for instant context retrieval:

### Core Architecture & Operational Guides
- [`GEMINI.md`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/GEMINI.md): Main project specification, Docker deployment, and technical stack details.
- [`README.md`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/README.md): Primary repository entrypoint and quick-start instructions.
- [`CONFIGURACION_RAPIDA.md`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/CONFIGURACION_RAPIDA.md): Fast setup guide for environment variables and dependencies.
- [`reporte_final_100_puntos.md`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/reporte_final_100_puntos.md): Audit report detailing full system scoring and verification benchmarks.
- [`verificar_sistema.py`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/verificar_sistema.py): Automated system health and dependency diagnostic script.

### System Plans & Design Documents
- [`plan_maestro_dashboard_ultra_avanzado.md`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/plan_maestro_dashboard_ultra_avanzado.md): Master design specification for the React Dashboard UI.
- [`patrones_agentes_silhouettemcp.md`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/patrones_agentes_silhouettemcp.md): Design patterns for specialized multi-agent subroutines.
- [`plan_expansion_silhouettemcp.md`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/plan_expansion_silhouettemcp.md): Roadmap for feature expansions and integrations.

### Historical Memories & Context Specs
- [`memories/dashboard_silhouettemcp.md`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/memories/dashboard_silhouettemcp.md): Context memory for UI layout evolution.
- [`memories/proyecto_sistema_agente.md`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/memories/proyecto_sistema_agente.md): Core agent orchestrator memories.
- [`memories/expansion_silhouettemcp_iris.md`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/memories/expansion_silhouettemcp_iris.md): Integration specs for Iris AI module.
- [`memories/proyecto_iris_ui_design.md`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/memories/proyecto_iris_ui_design.md): UI styling tokens and design system specs.

### Subsystem Documentation
- [`microsoft365-integration/TESTS_SUMMARY.md`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/microsoft365-integration/TESTS_SUMMARY.md): Test suite results for Graph API & M365 tools.
- [`package/silhouettemcp_v4_unified/docs/API_ENDPOINTS.md`](file:///d:/Proyectos%20personales/SilhouetteAppcreator/package/silhouettemcp_v4_unified/docs/API_ENDPOINTS.md): Complete REST API reference.

---

## 🤖 Enterprise Multi-Agent Architecture

SilhouetteMCP uses specialized background workers and subagents for complex workflows:

1. **Hybrid Sandbox Manager (`backend/app/services/hybrid_sandbox_manager.py`)**
   - Creates isolated Git Worktrees paired with Docker containers (`python:3.10-slim`) with memory limits for safe code execution.
2. **Redis Orchestrator (`code/silhouettemcp_hierarchical_architecture.py`)**
   - Asynchronous heartbeat mechanisms and `SETNX` leader locks for distributed node synchronization.
3. **Semantic Merger (`backend/app/agents/semantic_merger.py`)**
   - AI-assisted merge conflict resolution for git operations using `LLMRouter`.
4. **Prometheus Telemetry (`silhouettemcp_server.py`)**
   - Production metrics exposed at `@app.get("/metrics")`.
5. **Local AI Autodiscovery Service (`backend/app/core/local_ai_service.py`)**
   - Background scanner for local AI instances on ports `11434` (Ollama) and `1234` (LM Studio), plus Ollama model pulling endpoint.

---

## ⚡ Universal LLM Router & Omni-Adapter V2

The router in `backend/app/core/llm_router.py` translates requests dynamically using **LiteLLM**:

```
[User Request] 
      │
      ▼
[React Dashboard / REST API]
      │
      ▼
[silhouettemcp_server.py]
      │
      ▼
[LLMRouter + DynamicModelRegistry] ◄── [custom_models.json / .env]
      │
      ├───────────────────────┼───────────────────────┐
      ▼                       ▼                       ▼
 [LiteLLM Cloud]       [OpenRouter API]      [Local AI Autodiscovery]
 (GLM-5.2, MiniMax M3, (Qwen 3.7 Max,        (Ollama :11434,
  Kimi K3, OpenAI)      Claude Fable 5)       LM Studio :1234)
```

### Adding New LLMs
You can add any new LLM without modifying code:
1. **Via UI:** Open the Dashboard > `Configuraciones` > `Añadir Nueva API / Modelo`.
2. **Via JSON:** Add an entry to `backend/app/config/custom_models.json`.
3. **Via .env:** Edit global secrets using the Dashboard `Gestor de Credenciales Globales (.env)` card.

---

## 💻 Developer & Agent Instructions

### Verification & Testing
Before declaring any task completed, run:
```bash
python verificar_sistema.py
```
*Expected Status:* `ESTADO GENERAL: EXCELENTE (95.2%+)`

### Running the Services Locally
- **Backend API Server:**
  ```bash
  python silhouettemcp_server.py
  ```
  *URL:* `http://localhost:8001` (Docs: `http://localhost:8001/docs`)
- **React Dashboard:**
  ```bash
  cd mcp-dashboard
  npm run dev
  ```
  *URL:* `http://localhost:5173`

### Git & Remote Repository
- **Remote Repository:** `https://github.com/haroldfabla2-hue/SilhouetteAppcreator.git`
- **Branch:** `main`
- **Rule:** Never push raw `.zip` files or `__pycache__` to Git. Keep `.gitignore` updated.
