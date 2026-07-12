/**
 * Servicio para comunicación con el backend
 */
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface TaskRequest {
  objetivo: string;
  contexto?: Record<string, any>;
  user_id?: string;
  stream?: boolean;
}

export interface TaskResponse {
  conversation_id: string;
  status: string;
  result?: any;
  error?: string;
  metadata?: any;
}

export interface SystemStats {
  system: {
    version: string;
    status: string;
  };
  llm?: {
    total_calls: number;
    by_provider: any;
    minimax_free_days_remaining: number;
  };
  orchestrator?: {
    active_sessions: number;
    agents: any;
  };
}

class ApiService {
  private client = axios.create({
    baseURL: API_BASE_URL,
    timeout: 120000, // 2 minutos
    headers: {
      'Content-Type': 'application/json',
    },
  });

  /**
   * Crea una nueva tarea
   */
  async createTask(request: TaskRequest): Promise<TaskResponse> {
    try {
      const response = await this.client.post<TaskResponse>(
        '/api/v1/tasks',
        request
      );
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail || 'Error creando tarea'
      );
    }
  }

  /**
   * Obtiene el estado de una tarea
   */
  async getTaskStatus(conversationId: string): Promise<any> {
    try {
      const response = await this.client.get(
        `/api/v1/tasks/${conversationId}`
      );
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail || 'Error obteniendo estado de tarea'
      );
    }
  }

  /**
   * Obtiene estadísticas del sistema
   */
  async getSystemStats(): Promise<SystemStats> {
    try {
      const response = await this.client.get<SystemStats>('/api/v1/stats');
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail || 'Error obteniendo estadísticas'
      );
    }
  }

  /**
   * Health check del sistema
   */
  async healthCheck(): Promise<any> {
    try {
      const response = await this.client.get('/health');
      return response.data;
    } catch (error: any) {
      throw new Error('Sistema no disponible');
    }
  }

  /**
   * Prueba el LLM Router
   */
  async testLLM(prompt: string = 'Hola'): Promise<any> {
    try {
      const response = await this.client.post('/api/v1/llm/test', null, {
        params: { prompt },
      });
      return response.data;
    } catch (error: any) {
      throw new Error(
        error.response?.data?.detail || 'Error probando LLM'
      );
    }
  }
}

export const apiService = new ApiService();
