// Cliente de API para MCP Server
export interface APIConfig {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
}

// Real API Config using our localhost MCP server
export const API_CONFIG: APIConfig = {
  baseUrl: 'http://localhost:8000',
  timeout: 30000,
  retryAttempts: 3
};

export interface HealthResponse {
  status: 'healthy' | 'unhealthy';
  uptime: number;
  version: string;
  timestamp: string;
}

export interface MetricsResponse {
  total_conversations: number;
  active_projects: number;
  tokens_used: number;
  system_load: number;
  memory_usage: number;
  last_updated: string;
  server_status: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  tokens?: number;
  project_id?: string;
}

export interface ChatResponse {
  id: string;
  message: ChatMessage;
  streaming: boolean;
}

export interface Project {
  id: string;
  name: string;
  description?: string;
  created_at: string;
  updated_at: string;
  files_count: number;
  conversations_count: number;
  last_activity: string;
}

export interface FileItem {
  id: string;
  name: string;
  path: string;
  size: number;
  type: string;
  created_at: string;
  updated_at: string;
  content?: string;
  project_id: string;
}

export interface Template {
  id: string;
  name: string;
  description: string;
  category: string;
  files: FileItem[];
  tags: string[];
  created_at: string;
  preview?: string;
}

class MCPClient {
  private config: APIConfig;
  private baseUrl: string;
  private isOnline: boolean = false;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;

  constructor() {
    this.config = {
      baseUrl: localStorage.getItem('mcp-server-url') || 'http://localhost:8000',
      timeout: 30000,
      retryAttempts: 3
    };
    this.baseUrl = this.config.baseUrl;
  }

  // Configuración
  setServerUrl(url: string) {
    this.baseUrl = url;
    localStorage.setItem('mcp-server-url', url);
    this.config.baseUrl = url;
  }

  getServerUrl(): string {
    return this.baseUrl;
  }

  // Health Check
  async checkHealth(): Promise<HealthResponse | null> {
    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(this.config.timeout)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      this.isOnline = true;
      this.reconnectAttempts = 0;
      return data;
    } catch (error) {
      console.error('Health check failed:', error);
      this.isOnline = false;
      this.handleReconnection();
      return null;
    }
  }

  // Metrics
  async getMetrics(): Promise<MetricsResponse | null> {
    try {
      const response = await fetch(`${this.baseUrl}/metrics`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(this.config.timeout)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to fetch metrics:', error);
      return this.getFallbackMetrics();
    }
  }

  // Chat
  async sendMessage(
    message: string, 
    projectId?: string, 
    conversationId?: string
  ): Promise<ChatResponse | null> {
    try {
      const response = await fetch(`${this.baseUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message,
          project_id: projectId,
          conversation_id: conversationId
        }),
        signal: AbortSignal.timeout(this.config.timeout)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to send message:', error);
      return null;
    }
  }

  // Streaming Chat
  async sendMessageStream(
    message: string,
    projectId?: string,
    conversationId?: string,
    onChunk?: (chunk: string) => void
  ): Promise<{ success: boolean; messageId?: string; error?: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
        },
        body: JSON.stringify({
          message,
          project_id: projectId,
          conversation_id: conversationId
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let messageId = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') {
                return { success: true, messageId };
              }
              
              try {
                const parsed = JSON.parse(data);
                if (parsed.id) messageId = parsed.id;
                if (parsed.content && onChunk) {
                  onChunk(parsed.content);
                }
              } catch (e) {
                // Ignore parsing errors for non-JSON chunks
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

      return { success: true, messageId };
    } catch (error) {
      console.error('Streaming failed:', error);
      return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
    }
  }

  // Projects
  async getProjects(): Promise<Project[]> {
    try {
      const response = await fetch(`${this.baseUrl}/projects`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(this.config.timeout)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return data.projects || [];
    } catch (error) {
      console.error('Failed to fetch projects:', error);
      return this.getFallbackProjects();
    }
  }

  async createProject(name: string, description?: string): Promise<Project | null> {
    try {
      const response = await fetch(`${this.baseUrl}/projects`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name,
          description: description || ''
        }),
        signal: AbortSignal.timeout(this.config.timeout)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return data.project;
    } catch (error) {
      console.error('Failed to create project:', error);
      return null;
    }
  }

  // Files
  async getProjectFiles(projectId: string): Promise<FileItem[]> {
    try {
      const response = await fetch(`${this.baseUrl}/projects/${projectId}/files`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(this.config.timeout)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return data.files || [];
    } catch (error) {
      console.error('Failed to fetch project files:', error);
      return [];
    }
  }

  async uploadFile(projectId: string, file: File): Promise<FileItem | null> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${this.baseUrl}/projects/${projectId}/files`, {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(this.config.timeout)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return data.file;
    } catch (error) {
      console.error('Failed to upload file:', error);
      return null;
    }
  }

  async saveFile(fileId: string, content: string): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/files/${fileId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content }),
        signal: AbortSignal.timeout(this.config.timeout)
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to save file:', error);
      return false;
    }
  }

  // Templates
  async getTemplates(): Promise<Template[]> {
    try {
      const response = await fetch(`${this.baseUrl}/templates`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(this.config.timeout)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return data.templates || [];
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      return this.getFallbackTemplates();
    }
  }

  async createFromTemplate(templateId: string, projectName: string): Promise<Project | null> {
    try {
      const response = await fetch(`${this.baseUrl}/templates/${templateId}/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ project_name: projectName }),
        signal: AbortSignal.timeout(this.config.timeout)
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return data.project;
    } catch (error) {
      console.error('Failed to create project from template:', error);
      return null;
    }
  }

  // Status
  isServerOnline(): boolean {
    return this.isOnline;
  }

  // Fallback data cuando el servidor no está disponible
  private getFallbackMetrics(): MetricsResponse {
    return {
      total_conversations: 42,
      active_projects: 8,
      tokens_used: 156789,
      system_load: 0.35,
      memory_usage: 0.68,
      last_updated: new Date().toISOString(),
      server_status: 'fallback'
    };
  }

  private getFallbackProjects(): Project[] {
    return [
      {
        id: '1',
        name: 'Proyecto React Dashboard',
        description: 'Dashboard interactivo con métricas en tiempo real',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-20T14:30:00Z',
        files_count: 24,
        conversations_count: 8,
        last_activity: '2024-01-20T14:30:00Z'
      },
      {
        id: '2',
        name: 'API REST Service',
        description: 'Microservicio con endpoints RESTful',
        created_at: '2024-01-10T09:15:00Z',
        updated_at: '2024-01-18T16:45:00Z',
        files_count: 18,
        conversations_count: 12,
        last_activity: '2024-01-18T16:45:00Z'
      }
    ];
  }

  private getFallbackTemplates(): Template[] {
    return [
      {
        id: '1',
        name: 'React Dashboard Template',
        description: 'Template completo para dashboards React',
        category: 'dashboard',
        files: [
          {
            id: '1',
            name: 'App.tsx',
            path: '/src/App.tsx',
            size: 2048,
            type: 'typescript',
            created_at: '2024-01-15T10:00:00Z',
            updated_at: '2024-01-15T10:00:00Z',
            content: 'import React from \'react\';\\nfunction App() { return <div>Dashboard</div>; }\\nexport default App;',
            project_id: 'template'
          }
        ],
        tags: ['react', 'dashboard', 'typescript'],
        created_at: '2024-01-15T10:00:00Z'
      }
    ];
  }

  private handleReconnection() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn('Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.pow(2, this.reconnectAttempts) * 1000; // Exponential backoff

    setTimeout(() => {
      console.log(`Attempting reconnection ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
      this.checkHealth();
    }, delay);
  }
}

// Singleton instance
export const mcpClient = new MCPClient();
export default mcpClient;