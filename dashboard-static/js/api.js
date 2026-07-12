// API Client for SilhouetteMCP Dashboard
const API_BASE_URL = window.location.origin;

class SilhouetteMCPAPI {
    constructor() {
        this.token = this.getStoredToken();
        this.baseURL = API_BASE_URL;
    }

    // Authentication
    getStoredToken() {
        return localStorage.getItem('silhouettemcp_token');
    }

    storeToken(token) {
        localStorage.setItem('silhouettemcp_token', token);
        this.token = token;
    }

    getAuthHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    async login(email, password) {
        try {
            const response = await fetch(`${this.baseURL}/admin/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            if (!response.ok) {
                throw new Error('Login failed');
            }

            const data = await response.json();
            if (data.token) {
                this.storeToken(data.token);
            }
            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    // Dashboard Data
    async getDashboardData() {
        try {
            const response = await fetch(`${this.baseURL}/admin/dashboard`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                if (response.status === 401) {
                    // Auto-login with stored credentials
                    await this.login('alberto.farahb@hotmail.com', 'Fbalberto1910');
                    return this.getDashboardData();
                }
                throw new Error('Failed to fetch dashboard data');
            }

            return await response.json();
        } catch (error) {
            console.error('Dashboard data error:', error);
            throw error;
        }
    }

    // Applications
    async getApplications() {
        try {
            const response = await fetch(`${this.baseURL}/admin/applications`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to fetch applications');
            }

            return await response.json();
        } catch (error) {
            console.error('Applications error:', error);
            throw error;
        }
    }

    // Agents
    async getAgents() {
        try {
            const response = await fetch(`${this.baseURL}/admin/agents`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to fetch agents');
            }

            return await response.json();
        } catch (error) {
            console.error('Agents error:', error);
            throw error;
        }
    }

    async deployAgent(agentConfig) {
        try {
            const response = await fetch(`${this.baseURL}/api/agents/deploy`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify(agentConfig)
            });

            if (!response.ok) {
                throw new Error('Failed to deploy agent');
            }

            return await response.json();
        } catch (error) {
            console.error('Deploy agent error:', error);
            throw error;
        }
    }

    // Metrics Stream (SSE)
    connectMetricsStream(callback) {
        const eventSource = new EventSource(`${this.baseURL}/metrics/stream`);
        
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                callback(data);
            } catch (error) {
                console.error('Metrics stream parse error:', error);
            }
        };

        eventSource.onerror = (error) => {
            console.error('Metrics stream error:', error);
            eventSource.close();
            // Reconnect after 5 seconds
            setTimeout(() => {
                this.connectMetricsStream(callback);
            }, 5000);
        };

        return eventSource;
    }

    // Health Check
    async healthCheck() {
        try {
            const response = await fetch(`${this.baseURL}/health`);
            return await response.json();
        } catch (error) {
            console.error('Health check error:', error);
            throw error;
        }
    }

    // Public Metrics
    async getPublicMetrics() {
        try {
            const response = await fetch(`${this.baseURL}/metrics/public`);
            return await response.json();
        } catch (error) {
            console.error('Public metrics error:', error);
            throw error;
        }
    }

    // System Metrics (Real)
    async getSystemMetrics() {
        try {
            const response = await fetch(`${this.baseURL}/api/system/metrics`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to fetch system metrics');
            }

            return await response.json();
        } catch (error) {
            console.error('System metrics error:', error);
            throw error;
        }
    }

    // System Logs (Real)
    async getSystemLogs(lines = 50) {
        try {
            const response = await fetch(`${this.baseURL}/api/system/logs?lines=${lines}`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to fetch system logs');
            }

            return await response.json();
        } catch (error) {
            console.error('System logs error:', error);
            throw error;
        }
    }

    // Create Dynamic API
    async createDynamicAPI(name, description, agentType = 'custom') {
        try {
            const response = await fetch(`${this.baseURL}/api/dynamic/create`, {
                method: 'POST',
                headers: this.getAuthHeaders(),
                body: JSON.stringify({
                    name: name,
                    description: description,
                    agent_type: agentType
                })
            });

            if (!response.ok) {
                throw new Error('Failed to create API');
            }

            return await response.json();
        } catch (error) {
            console.error('Create API error:', error);
            throw error;
        }
    }

    // Delete Dynamic API
    async deleteDynamicAPI(appId) {
        try {
            const response = await fetch(`${this.baseURL}/api/dynamic/${appId}`, {
                method: 'DELETE',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to delete API');
            }

            return await response.json();
        } catch (error) {
            console.error('Delete API error:', error);
            throw error;
        }
    }

    // Create Backup
    async createBackup() {
        try {
            const response = await fetch(`${this.baseURL}/api/system/backup`, {
                method: 'POST',
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to create backup');
            }

            return await response.json();
        } catch (error) {
            console.error('Create backup error:', error);
            throw error;
        }
    }

    // List Backups
    async listBackups() {
        try {
            const response = await fetch(`${this.baseURL}/api/system/backups`, {
                headers: this.getAuthHeaders()
            });

            if (!response.ok) {
                throw new Error('Failed to list backups');
            }

            return await response.json();
        } catch (error) {
            console.error('List backups error:', error);
            throw error;
        }
    }
}

// Export for use in other modules
window.api = new SilhouetteMCPAPI();
