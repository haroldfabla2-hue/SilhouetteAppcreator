# GEMINI.md - MCP Server Superior

## Project Overview

This project, "MCP Server Superior," is a sophisticated, enterprise-grade, multi-agent system designed for a wide range of automation and data processing tasks. It leverages a hybrid architecture of multiple specialized AI agents orchestrated by a central controller. The system is built to integrate with over 50 real-world tools and services, including Google Workspace, Microsoft 365, Salesforce, and Stripe.

**Core Features:**

*   **Multi-Agent Architecture:** The system uses a Multi-Agent Orchestrator to manage specialized agents for tasks like reasoning, planning, and execution.
*   **Extensive Tooling:** It integrates with a vast array of tools for Git operations, web scraping (Playwright, BeautifulSoup), database management (PostgreSQL with pgvector for RAG), file processing (PDF, Excel, CSV, OCR), and secure code execution.
*   **Advanced Memory:** Utilizes a PostgreSQL database with the `pgvector` extension for advanced Retrieval-Augmented Generation (RAG) and context persistence.
*   **Observability:** The system is equipped with a full observability stack, including Prometheus for metrics and Grafana for real-time dashboards, to monitor performance, errors, and resource usage.
*   **Scalability and Resilience:** Designed for high performance, with features like auto-scaling, auto-healing for automatic failure recovery, and zero-downtime deployments.

**Technical Stack:**

*   **Backend:** FastAPI, LangGraph, and `asyncio` for high-performance, asynchronous services.
*   **Frontend:** React with TypeScript and TailwindCSS.
*   **Database:** PostgreSQL with `pgvector` for vector embeddings.
*   **Cache & Message Queues:** Redis.
*   **Deployment:** Docker Compose for container orchestration, with readiness for Kubernetes.
*   **Agents:** Implemented in Python using multiprocessing and asynchronous I/O.
*   **Security:** Implements JWT, OAuth, and RBAC for secure operations.

## Building and Running

The primary method for running the entire system is via Docker Compose, which orchestrates all the necessary services.

### **1. Running with Docker (Recommended)**

This method starts all services, including the backend, frontend, database, and monitoring tools.

**Prerequisites:**
*   Docker and Docker Compose

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd SilhouetteAppcreator
    ```

2.  **Configure Environment Variables:**
    *   Copy the template file:
        ```bash
        cp .env.template .env
        ```
    *   Edit the `.env` file to include the necessary API keys and configurations. An `OPENROUTER_API_KEY` is required for the free MiniMax M2 model.

3.  **Build and Start Services:**
    ```bash
    docker-compose up --build
    ```

4.  **Accessing Services:**
    *   **Backend API:** `http://localhost:8000`
    *   **API Docs (Swagger UI):** `http://localhost:8000/docs`
    *   **Frontend:** `http://localhost:3000`
    *   **Grafana Dashboards:** `http://localhost:3001` (login: admin/admin)
    *   **PostgreSQL:** `localhost:5432`
    *   **Redis:** `localhost:6379`

### **2. Running Locally (for Backend Development)**

This method is suitable for developing or testing the backend service independently.

**Prerequisites:**
*   Python 3.9+
*   A running PostgreSQL and Redis instance.

**Steps:**

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set Environment Variables:**
    *   Ensure that environment variables for connecting to PostgreSQL and Redis, as well as any required API keys, are set in your shell or a `.env` file.

3.  **Run the Application:**
    ```bash
    python main.py
    ```
    Alternatively, for development with auto-reload:
    ```bash
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ```

### **3. System Verification**

The project includes scripts to verify the setup and configuration.

*   **Full System Check:**
    ```bash
    python verificar_sistema.py
    ```
*   **Auto-configuration and Verification:**
    ```bash
    python main.py --verify
    ```

## Development Conventions

*   **Modular Architecture:** The project is divided into distinct services (`backend`, `frontend`) and infrastructure components, each with its own directory.
*   **Configuration:** All configuration is managed through environment variables, following the 12-factor app methodology. A `.env.template` file provides a schema for the required variables.
*   **Asynchronous Code:** The backend heavily utilizes `asyncio` and `FastAPI` to handle concurrent requests efficiently.
*   **Dependency Management:** Python dependencies are managed in `requirements.txt`.
*   **Testing:** The project includes a suite of tests (e.g., `test_*.py` files). Although the exact test command is not specified, it is likely that a standard Python test runner like `pytest` is used.
*   **Documentation:** The project is extensively documented in Markdown files, covering architecture, setup, usage guides, and API references.
